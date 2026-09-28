"""apply one definition to tidy records from casedefs.inputs."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .codes import matches_any
from .definition import ClaimsExclusion, Composite, Definition, Exclusion, PersonExclusion

OUTPUT_COLUMNS = ["person_id", "case_date", "definition_id", "definition_version"]
CANDIDATE_COLUMNS = ["person_id", "date", "path"]


class UnverifiedDefinitionWarning(UserWarning):
    """the definition's codes were not confirmed against a primary source."""


class MissingPeopleWarning(UserWarning):
    """an age or sex rule could not be checked because people data was missing."""


class MissingFieldWarning(UserWarning):
    """the definition wants a field (like diagnosis type) that the data does not have."""


class IncompleteDefinitionWarning(UserWarning):
    """part of the published rule is not implemented, so some cases will be missed."""


@dataclass
class Tables:
    """tidy inputs, any of which may be None."""

    claims: pd.DataFrame | None = None
    hospital: pd.DataFrame | None = None
    procedures: pd.DataFrame | None = None
    drugs: pd.DataFrame | None = None
    people: pd.DataFrame | None = None
    ambulatory: pd.DataFrame | None = None


def _warn(message: str, category: type[Warning]) -> None:
    warnings.warn(message, category, stacklevel=4)


def _empty(columns=CANDIDATE_COLUMNS) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def match_codes(
    events: pd.DataFrame,
    icd9: tuple[str, ...],
    icd10ca: tuple[str, ...],
    excluded: tuple[str, ...] = (),
) -> pd.Series:
    is9 = events["coding"].isin(["icd9", "both"])
    is10 = events["coding"].isin(["icd10ca", "both"])
    hit = (is9 & matches_any(events["code"], icd9)) | (is10 & matches_any(events["code"], icd10ca))
    if excluded:
        hit &= ~matches_any(events["code"], excluded)
    return hit


def age_on(birth: pd.Series, when: pd.Series) -> pd.Series:
    """completed years of age on a date. nan where birth date is unknown."""
    years = when.dt.year - birth.dt.year
    before_birthday = (when.dt.month < birth.dt.month) | (
        (when.dt.month == birth.dt.month) & (when.dt.day < birth.dt.day)
    )
    return (years - before_birthday.astype(int)).where(birth.notna())


def nth_record(events: pd.DataFrame, n: int | None, path: str) -> pd.DataFrame:
    """date each person reaches n distinct records."""
    if not n or events.empty:
        return _empty()
    records = events.drop_duplicates(["person_id", "record_id"]).sort_values(["person_id", "date"])
    rank = records.groupby("person_id").cumcount() + 1
    return records.loc[rank >= n, ["person_id", "date"]].assign(path=path)


def record_path(events: pd.DataFrame, n: int | None, rule, path: str) -> pd.DataFrame:
    """dates a person meets n records of one kind, honouring the rule window and gap."""
    if not n or events.empty:
        return _empty()
    if n == 1:
        return nth_record(events, 1, path)
    records = events.drop_duplicates(["person_id", "record_id"])
    return chain_ends(records, "person_id", n, rule.window_days, rule.min_days_between).assign(path=path)


def chain_ends(
    events: pd.DataFrame,
    key: str,
    n: int,
    window_days: int | None,
    min_days_between: int = 0,
) -> pd.DataFrame:
    """rows where a chain of n claims for the same key ends.

    a chain is n claims, each at least min_days_between days after the one
    before, with the first and last no more than window_days apart. returns
    the key and the date of the last claim in each chain that fits.
    """
    if events.empty:
        return pd.DataFrame(columns=[key, "date"])
    rows = events.sort_values([key, "date"], kind="stable")[[key, "date"]].reset_index(drop=True)
    if n == 1:
        return rows
    if min_days_between <= 0:
        # any n records count, so the latest possible start is n-1 rows back
        start = rows.groupby(key, sort=False)["date"].shift(n - 1)
        ok = start.notna()
        if window_days is not None:
            ok &= (rows["date"] - start).dt.days <= window_days
        return rows.loc[ok.to_numpy()]

    # with a gap, walk up the chain length. best holds the latest start date
    # of a valid chain of the current length ending at each row.
    rows = rows.drop_duplicates()
    group = pd.factorize(rows[key])[0].astype(np.int64)
    days = (rows["date"] - pd.Timestamp("1900-01-01")).dt.days.to_numpy(dtype=np.int64)
    span = int(days.max() - days.min()) + min_days_between + 2
    sort_key = group * span + (days - days.min())
    best = days.astype(float)
    for _ in range(n - 1):
        running = pd.Series(best).groupby(group).cummax().to_numpy()
        idx = np.searchsorted(sort_key, sort_key - min_days_between, side="right") - 1
        valid = (idx >= 0) & (group[np.clip(idx, 0, None)] == group)
        best = np.where(valid, running[np.clip(idx, 0, None)], -np.inf)
    ok = np.isfinite(best)
    if window_days is not None:
        ok &= (days - best) <= window_days
    return rows.loc[ok, [key, "date"]]


def _ages(frame: pd.DataFrame, people: pd.DataFrame) -> pd.Series:
    merged = frame[["person_id", "date"]].merge(people[["person_id", "birth_date"]], on="person_id", how="left")
    return pd.Series(age_on(merged["birth_date"], merged["date"]).to_numpy(), index=frame.index)


def _age_filter(cands: pd.DataFrame, people: pd.DataFrame | None, min_age, max_age, label: str, text: str):
    if min_age is None and max_age is None:
        return cands
    if people is None:
        _warn(f"{label} has an age limit ({text}) but no people table was given, so age was not checked",
              MissingPeopleWarning)
        return cands
    age = _ages(cands, people)
    unknown = cands.loc[age.isna(), "person_id"].nunique()
    if unknown:
        _warn(
            f"{unknown} person(s) with qualifying records have no birth date in the people table "
            f"and were left out of {label}, since the {text} age limit could not be checked",
            MissingPeopleWarning,
        )
    keep = age.notna()
    if min_age is not None:
        keep &= age >= min_age
    if max_age is not None:
        keep &= age <= max_age
    return cands[keep]


def _blocked(cands: pd.DataFrame, hits: pd.DataFrame, excl: Exclusion, people: pd.DataFrame | None) -> pd.Series:
    """true for candidate rows that fall inside an exclusion window."""
    if hits.empty or cands.empty:
        return pd.Series(False, index=cands.index)
    pairs = cands.reset_index().merge(hits.rename(columns={"date": "hit_date"}), on="person_id")
    gap = (pairs["date"] - pairs["hit_date"]).dt.days
    inside = (gap >= -excl.days_before) & (gap <= excl.days_after)

    if people is not None and (excl.sex or excl.min_age is not None or excl.max_age is not None):
        pairs = pairs.merge(people, on="person_id", how="left")
        if excl.sex:
            # unknown sex counts as a match; the pregnancy codes already imply it
            sex = pairs["sex"]
            inside &= (sex.isna() | (sex == excl.sex[:1].upper())).to_numpy()
        age = age_on(pairs["birth_date"], pairs["date"])
        if excl.min_age is not None:
            inside &= (age.isna() | (age >= excl.min_age)).to_numpy()
        if excl.max_age is not None:
            inside &= (age.isna() | (age <= excl.max_age)).to_numpy()

    blocked_idx = pairs.loc[inside.to_numpy(), "index"].unique()
    return pd.Series(cands.index.isin(blocked_idx), index=cands.index)


def _claims_excluded(first: pd.DataFrame, claims: pd.DataFrame, excl: ClaimsExclusion) -> set:
    """people with repeat claims for an excluding code on or after qualifying."""
    hits = claims[match_codes(claims, excl.icd9, excl.icd10ca)]
    hits = hits.merge(first.rename(columns={"date": "qualified"}), on="person_id")
    hits = hits[hits["date"] >= hits["qualified"]]
    if hits.empty:
        return set()
    digits = np.where(hits["coding"] == "icd10ca", excl.icd10ca_digits, excl.icd9_digits)
    stem = [code[:d] for code, d in zip(hits["code"], digits)]
    hits = hits.assign(key=list(zip(hits["person_id"], stem)))
    ends = chain_ends(hits, "key", excl.min_claims, excl.window_days, excl.min_days_between)
    return {k[0] for k in ends["key"]}


def _record_rows(defn: Definition, table: pd.DataFrame, dx_types, label: str) -> pd.DataFrame:
    """rows of a hospital or ambulatory table that count for this definition."""
    rows = table[match_codes(table, defn.icd9, defn.icd10ca, defn.excluded_codes)]
    if dx_types:
        if table["dx_type"].notna().any():
            rows = rows[rows["dx_type"].isin(dx_types)]
        else:
            _warn(
                f"{defn.id} only counts {label} diagnosis types {', '.join(dx_types)} "
                f"but the {label} data has no dx_type columns, so every diagnosis field was used "
                f"(this can overcount)",
                MissingFieldWarning,
            )
    if label == "hospital" and defn.hospital_date == "admission":
        if table["admit_date"].notna().any():
            rows = rows.assign(date=rows["admit_date"].fillna(rows["date"]))
        else:
            _warn(
                f"{defn.id} dates hospital records by admission but the hospital data has no "
                f"admit_date column, so the separation date was used",
                MissingFieldWarning,
            )
    return rows


def _claims_rows(defn: Definition, claims: pd.DataFrame) -> pd.DataFrame:
    icd9, icd10 = defn.claims_codes
    rows = claims[match_codes(claims, icd9, icd10, defn.excluded_codes)]
    if defn.claims_specialties:
        if claims["specialty"].notna().any():
            rows = rows[rows["specialty"].isin([s.upper() for s in defn.claims_specialties])]
        else:
            _warn(
                f"{defn.id} only counts claims from {', '.join(defn.claims_specialties)} physicians "
                f"but the claims data has no specialty column, so all claims were used (this can overcount)",
                MissingFieldWarning,
            )
    return rows


def _present(table: pd.DataFrame | None) -> bool:
    return table is not None and not table.empty


def run(defn: Definition, tables: Tables) -> pd.DataFrame:
    if not defn.verified:
        _warn(
            f"{defn.id} is marked verified=False: see its notes and {defn.source_url} before using results",
            UnverifiedDefinitionWarning,
        )
    if not defn.complete:
        _warn(f"{defn.id} is not fully implemented and will miss some cases; run 'casedefs show {defn.id}' "
              f"for what is missing", IncompleteDefinitionWarning)
    rule = defn.rule
    parts = []
    if _present(tables.hospital) and rule.min_hospital:
        rows = _record_rows(defn, tables.hospital, defn.hospital_dx_types, "hospital")
        parts.append(record_path(rows, rule.min_hospital, rule, "hospital"))
    if _present(tables.claims) and rule.min_claims:
        claims = _claims_rows(defn, tables.claims)
        parts.append(
            chain_ends(claims, "person_id", rule.min_claims, rule.window_days, rule.min_days_between).assign(
                path="claims"
            )
        )
    if _present(tables.ambulatory) and rule.min_ambulatory:
        rows = _record_rows(defn, tables.ambulatory, defn.ambulatory_dx_types, "ambulatory")
        parts.append(record_path(rows, rule.min_ambulatory, rule, "ambulatory"))
    if tables.procedures is not None and not tables.procedures.empty and rule.min_procedures:
        procs = tables.procedures
        hit = (
            (procs["coding"].eq("cci") & matches_any(procs["code"], defn.procedure_cci))
            | (procs["coding"].eq("ccp") & matches_any(procs["code"], defn.procedure_ccp))
            | (procs["coding"].eq("icd9cm") & matches_any(procs["code"], defn.procedure_icd9cm))
        )
        parts.append(nth_record(procs[hit], rule.min_procedures, "procedures"))
    if tables.drugs is not None and not tables.drugs.empty and rule.min_drugs:
        drugs = tables.drugs
        parts.append(nth_record(drugs[drugs["code"].isin(defn.drug_dins)], rule.min_drugs, "drugs"))

    parts = [p for p in parts if not p.empty]
    if not parts:
        return _empty(OUTPUT_COLUMNS)
    cands = pd.concat(parts, ignore_index=True).drop_duplicates()
    cands["date"] = pd.to_datetime(cands["date"])

    cands = _age_filter(cands, tables.people, defn.min_age, defn.max_age, defn.id, defn.age_text())
    if rule.hospital_min_age is not None:
        hosp = cands[cands["path"] == "hospital"]
        kept = _age_filter(hosp, tables.people, rule.hospital_min_age, None,
                           f"{defn.id} (hospital path)", f"{rule.hospital_min_age}+")
        cands = pd.concat([cands[cands["path"] != "hospital"], kept])

    hospital = tables.hospital
    for excl in defn.exclusions:
        if isinstance(excl, Exclusion) and hospital is not None and not hospital.empty:
            hits = hospital.loc[match_codes(hospital, excl.icd9, excl.icd10ca), ["person_id", "date"]]
            cands = cands[~_blocked(cands, hits.drop_duplicates(), excl, tables.people).to_numpy()]

    if cands.empty:
        return _empty(OUTPUT_COLUMNS)
    first = cands.groupby("person_id", as_index=False)["date"].min()

    for excl in defn.exclusions:
        if isinstance(excl, ClaimsExclusion) and _present(tables.claims):
            first = first[~first["person_id"].isin(_claims_excluded(first, tables.claims, excl))]
        if isinstance(excl, PersonExclusion):
            excluded = set()
            for table in (tables.hospital, tables.claims, tables.ambulatory):
                if _present(table):
                    excluded |= set(table.loc[match_codes(table, excl.icd9, excl.icd10ca), "person_id"])
            first = first[~first["person_id"].isin(excluded)]

    return _output(first, defn.id, defn.version)


def run_composite(comp: Composite, tables: Tables, get, cache: dict | None = None) -> pd.DataFrame:
    """get(id) returns a component definition. cache maps ids to results already found."""
    if not comp.verified:
        _warn(f"{comp.id} is marked verified=False: see its notes", UnverifiedDefinitionWarning)
    cache = {} if cache is None else cache
    parts = [get(c) if isinstance(c, str) else c for c in comp.components]
    with warnings.catch_warnings():
        # the components warn on their own; the composite sums them up below
        warnings.simplefilter("ignore")
        for d in parts:
            if d.id not in cache:
                cache[d.id] = run(d, tables)
    found = [cache[d.id] for d in parts]
    found = [f for f in found if not f.empty]
    if not found:
        return _empty(OUTPUT_COLUMNS)
    all_cases = pd.concat(found, ignore_index=True).sort_values(["person_id", "case_date"])
    rank = all_cases.groupby("person_id").cumcount() + 1
    reached = all_cases.loc[rank == comp.min_conditions, ["person_id", "case_date"]]
    reached = reached.rename(columns={"case_date": "date"})
    has_ages = any(d.min_age is not None or d.max_age is not None for d in parts)
    if tables.people is None and has_ages:
        _warn(f"{comp.id}: no people table was given, so component age limits were not checked",
              MissingPeopleWarning)
    reached = _age_filter(reached, tables.people, comp.min_age, comp.max_age, comp.id, comp.age_text())
    return _output(reached, comp.id, comp.version)


def _output(first: pd.DataFrame, def_id: str, version: str) -> pd.DataFrame:
    if first.empty:
        return _empty(OUTPUT_COLUMNS)
    out = pd.DataFrame(
        {
            "person_id": first["person_id"].to_numpy(),
            "case_date": pd.to_datetime(first["date"]).to_numpy(),
            "definition_id": def_id,
            "definition_version": version,
        }
    )
    return out.sort_values(["case_date", "person_id"], kind="stable").reset_index(drop=True)
