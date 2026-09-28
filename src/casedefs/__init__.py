"""apply published health case definitions to administrative health data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from . import engine, inputs
from .definition import ClaimsExclusion, Composite, Definition, Exclusion, PersonExclusion, Rule
from .engine import (
    IncompleteDefinitionWarning,
    MissingFieldWarning,
    MissingPeopleWarning,
    UnverifiedDefinitionWarning,
)
from .inputs import CasedefsInputError
from .registry import all_definitions, get_definition

__version__ = "0.3.0"

from .scores import comorbidity_score  # noqa: E402


def list_definitions() -> pd.DataFrame:
    """one row per available definition."""
    rows = []
    for d in all_definitions().values():
        rule = d.describe() if isinstance(d, Composite) else d.rule.describe()
        rows.append(
            {
                "id": d.id,
                "name": d.name,
                "version": d.version,
                "verified": d.verified,
                "ages": d.age_text(),
                "rule": rule,
                "source": d.source_url,
            }
        )
    return pd.DataFrame(rows, columns=["id", "name", "version", "verified", "ages", "rule", "source"])


def _resolve(definition) -> list[Definition | Composite]:
    if isinstance(definition, (Definition, Composite)):
        return [definition]
    if isinstance(definition, str):
        definition = [definition]
    out: list[Definition | Composite] = []
    for d in definition:
        if isinstance(d, (Definition, Composite)):
            out.append(d)
        elif d == "all":
            out += list(all_definitions().values())
        elif d.endswith(".*"):
            # a whole source, e.g. "tonelli.*" or "quan.charlson.*"
            prefix = d[:-1]
            found = [x for i, x in all_definitions().items() if i.startswith(prefix)]
            if not found:
                raise KeyError(f"no definitions start with {prefix!r}")
            out += found
        else:
            out.append(get_definition(d))
    return list({d.id: d for d in out}.values())


def apply(
    definition: str | Definition | Composite | Sequence[str],
    claims: pd.DataFrame | None = None,
    hospital: pd.DataFrame | None = None,
    people: pd.DataFrame | None = None,
    procedures: pd.DataFrame | None = None,
    drugs: pd.DataFrame | None = None,
    ambulatory: pd.DataFrame | None = None,
    columns: Mapping[str, object] | None = None,
    claims_coding: str = "icd9",
    hospital_coding: str = "icd10ca",
    procedure_coding: str = "cci",
    date_format: str | None = None,
) -> pd.DataFrame:
    """find cases.

    definition is one id ("ccdss.diabetes"), a whole source ("tonelli.*"), a
    list of those, or "all".
    returns one row per person and definition: person_id, case_date,
    definition_id, definition_version.

    columns maps standard names to yours, e.g. {"person_id": "PHN"}.
    claims_coding and hospital_coding say which ICD version the codes are in
    ("icd9", "icd10ca" or "both"). a per-row icd_version column (9 or 10)
    overrides them.
    """
    defs = _resolve(definition)
    if all(t is None for t in (claims, hospital, procedures, drugs, ambulatory)):
        raise CasedefsInputError("pass at least one of claims, hospital, ambulatory, procedures or drugs")

    tables = engine.Tables(
        claims=None if claims is None else inputs.claims_events(claims, columns, claims_coding, date_format),
        hospital=None if hospital is None else inputs.hospital_events(hospital, columns, hospital_coding, date_format),
        procedures=None if procedures is None
        else inputs.procedure_events(procedures, columns, procedure_coding, date_format),
        drugs=None if drugs is None else inputs.drug_events(drugs, columns, date_format),
        people=None if people is None else inputs.people_table(people, columns, date_format),
        ambulatory=None if ambulatory is None
        else inputs.ambulatory_events(ambulatory, columns, hospital_coding, date_format),
    )
    tables = engine.Tables(*inputs.align_person_ids(
        tables.claims, tables.hospital, tables.procedures, tables.drugs, tables.people, tables.ambulatory
    ))

    # plain definitions first, so composites can reuse their results
    cache: dict[str, pd.DataFrame] = {}
    for d in defs:
        if not isinstance(d, Composite):
            cache[d.id] = engine.run(d, tables)
    results = [
        engine.run_composite(d, tables, get_definition, cache) if isinstance(d, Composite) else cache[d.id]
        for d in defs
    ]
    results = [r for r in results if not r.empty]
    if not results:
        return pd.DataFrame(columns=engine.OUTPUT_COLUMNS)
    return pd.concat(results, ignore_index=True)


__all__ = [
    "apply",
    "comorbidity_score",
    "list_definitions",
    "get_definition",
    "Definition",
    "Composite",
    "Rule",
    "Exclusion",
    "ClaimsExclusion",
    "PersonExclusion",
    "IncompleteDefinitionWarning",
    "CasedefsInputError",
    "UnverifiedDefinitionWarning",
    "MissingPeopleWarning",
    "MissingFieldWarning",
    "__version__",
]
