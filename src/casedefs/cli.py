from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from . import __version__, _resolve, apply, comorbidity_score
from .codes import normalize_code
from .definition import Composite
from .inputs import CasedefsInputError
from .registry import all_definitions, get_definition

app = typer.Typer(
    help="Apply published health case definitions to administrative health data.",
    no_args_is_help=True,
    add_completion=False,
)


def _fail(message: str) -> None:
    typer.secho(f"error: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def _read_csv(path: Optional[Path], label: str) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    if not path.exists():
        _fail(f"{label} file not found: {path}")
    try:
        # read everything as text so codes like 042 and 250.00 keep their form
        return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    except Exception as exc:  # noqa: BLE001
        _fail(f"could not read {label} file {path}: {exc}")
    return None


def _parse_maps(pairs: list[str]) -> dict[str, object]:
    out: dict[str, object] = {}
    for pair in pairs:
        if "=" not in pair:
            _fail(f"--map expects standard=yours, got {pair!r}")
        standard, theirs = (s.strip() for s in pair.split("=", 1))
        out[standard] = theirs
    return out


def _dot(code: str) -> str:
    """put the dot back after the third character, whatever form the code was stored in."""
    code = normalize_code(code)
    return code if len(code) <= 3 else f"{code[:3]}.{code[3:]}"


def _compact(codes: tuple[str, ...]) -> str:
    """show runs like O21, O22, ... O95 as O21-O95, with dots."""
    out: list[str] = []
    run: list[str] = []

    def key(code: str) -> tuple[str, int, int] | None:
        letters = code.rstrip("0123456789")
        digits = code[len(letters):]
        if not digits:
            return None
        return (letters, int(digits), len(digits))

    def flush() -> None:
        if len(run) > 2:
            out.append(f"{_dot(run[0])}-{_dot(run[-1])}")
        else:
            out.extend(_dot(c) for c in run)
        run.clear()

    for code in (normalize_code(c) for c in codes):
        k, prev = key(code), key(run[-1]) if run else None
        if k and prev and k[0] == prev[0] and k[2] == prev[2] and k[1] == prev[1] + 1:
            run.append(code)
        else:
            flush()
            run.append(code)
    flush()
    return ", ".join(out) or "none"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="show version"),
) -> None:
    pass


@app.command("list")
def list_cmd(
    source: Optional[str] = typer.Option(None, "--source", help="only ids starting with this, e.g. tonelli"),
) -> None:
    """list definitions with source and verified status."""
    defs = [d for d in all_definitions().values() if not source or d.id.startswith(source)]
    if not defs:
        _fail(f"no definitions start with {source!r}")
    width = max(len(d.id) for d in defs)
    typer.echo(f"{'ID':<{width}}  {'VERSION':<16} {'VERIFIED':<9} {'AGES':<9} NAME")
    for d in defs:
        flag = "yes" if d.verified else "NO"
        if not isinstance(d, Composite) and not d.complete:
            flag += "*"
        typer.echo(f"{d.id:<{width}}  {d.version:<16} {flag:<9} {d.age_text():<9} {d.name}")
    counts: dict[str, int] = {}
    for d in defs:
        family = d.id.rsplit(".", 1)[0]
        counts[family] = counts.get(family, 0) + 1
    typer.echo("")
    typer.echo(f"{len(defs)} definitions: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    if any(not isinstance(d, Composite) and not d.complete for d in defs):
        typer.echo("* part of the published rule is not implemented; see 'casedefs show <id>'")
    typer.echo("run 'casedefs show <id>' for codes and citation")


def _show_lines(d) -> list[str]:
    lines = [
        f"{d.id}  ({d.version})",
        d.name,
        "",
        f"verified:   {'yes' if d.verified else 'NO, see notes'}",
    ]
    if isinstance(d, Composite):
        lines += [
            f"rule:       {d.describe()}",
            f"ages:       {d.age_text()}",
            "conditions: " + ", ".join(c if isinstance(c, str) else c.id for c in d.components),
        ]
        return lines

    icd9, icd10 = d.claims_codes
    lines += [
        f"rule:       {d.rule.describe()}",
        f"ages:       {d.age_text()}",
    ]
    if d.rule.min_hospital:
        lines += [f"hospital ICD-9:      {_compact(d.icd9)}", f"hospital ICD-10-CA:  {_compact(d.icd10ca)}"]
    if d.rule.min_claims:
        lines += [f"claims ICD-9:        {_compact(icd9)}", f"claims ICD-10-CA:    {_compact(icd10)}"]
        if d.claims_specialties:
            lines.append(f"claims specialties:  {', '.join(d.claims_specialties)} (specialty column)")
    if d.rule.min_ambulatory:
        lines += [f"ambulatory ICD-9:    {_compact(d.icd9)}", f"ambulatory ICD-10:   {_compact(d.icd10ca)}"]
        if d.ambulatory_dx_types:
            lines.append(f"ambulatory dx types: {', '.join(d.ambulatory_dx_types)}")
    if not d.complete:
        lines.append("complete:            NO, part of the rule is not implemented (see notes)")
    if d.excluded_codes:
        lines.append(f"never counts:        {', '.join(_dot(c) for c in d.excluded_codes)}")
    if d.hospital_dx_types:
        lines.append(f"hospital dx types:   {', '.join(d.hospital_dx_types)} (M is MRDx)")
    if d.hospital_date != "separation":
        lines.append(f"hospital date:       {d.hospital_date}")
    if d.rule.min_procedures:
        lines += [
            f"procedures CCI:      {', '.join(d.procedure_cci)}",
            f"procedures CCP:      {', '.join(d.procedure_ccp)}",
            f"procedures ICD-9-CM: {', '.join(d.procedure_icd9cm)}",
        ]
    if d.rule.min_drugs:
        lines.append(f"drugs:               {len(d.drug_dins)} DINs (see the definition file)")
    lines.append("codes match by prefix: a code also covers every longer code under it")
    for e in d.exclusions:
        lines += ["", f"exclusion:  {e.name}", f"  {e.description}"]
        lines += [f"  ICD-9:     {_compact(e.icd9)}", f"  ICD-10-CA: {_compact(e.icd10ca)}"]
    return lines


@app.command()
def show(definition_id: str = typer.Argument(..., help="e.g. ccdss.diabetes")) -> None:
    """show codes, rule and citation for one definition."""
    try:
        d = get_definition(definition_id)
    except KeyError as exc:
        _fail(str(exc.args[0]))
    lines = _show_lines(d)
    if d.notes:
        lines += ["", f"notes:      {d.notes}"]
    lines += ["", "source:", f"  {d.source_title}", f"  {d.source_location}", f"  {d.source_url}"]
    typer.echo("\n".join(lines))


@app.command()
def run(
    definition_ids: list[str] = typer.Argument(..., help="ids like ccdss.diabetes, a source like tonelli.*, or all"),
    claims: Optional[Path] = typer.Option(None, "--claims", help="physician claims csv"),
    hospital: Optional[Path] = typer.Option(None, "--hospital", help="hospital discharge csv"),
    people: Optional[Path] = typer.Option(None, "--people", help="people csv with person_id, birth_date, sex"),
    procedures: Optional[Path] = typer.Option(None, "--procedures", help="procedures csv (for ihd)"),
    drugs: Optional[Path] = typer.Option(None, "--drugs", help="drug dispensations csv (for dementia)"),
    ambulatory: Optional[Path] = typer.Option(None, "--ambulatory", help="ed and clinic visits csv (nacrs, accs)"),
    output: Path = typer.Option(..., "--output", "-o", help="where to write cases csv"),
    map_: list[str] = typer.Option([], "--map", help="column mapping standard=yours, repeatable"),
    hospital_dx: Optional[str] = typer.Option(None, "--hospital-dx", help="comma separated hospital dx columns"),
    claims_coding: str = typer.Option("icd9", help="icd9, icd10ca or both"),
    hospital_coding: str = typer.Option("icd10ca", help="icd9, icd10ca or both"),
    procedure_coding: str = typer.Option("cci", help="cci, ccp or icd9cm"),
    date_format: Optional[str] = typer.Option(None, help="e.g. %d/%m/%Y, default is automatic"),
) -> None:
    """find cases and write them to a csv."""
    try:
        ids = [d.id for d in _resolve(definition_ids)]
    except KeyError as exc:
        _fail(str(exc.args[0]))
    if all(t is None for t in (claims, hospital, procedures, drugs, ambulatory)):
        _fail("pass at least one of --claims, --hospital, --ambulatory, --procedures or --drugs")

    columns = _parse_maps(map_)
    if hospital_dx:
        columns["hospital_dx_columns"] = [c.strip() for c in hospital_dx.split(",") if c.strip()]

    tables = {
        "claims": _read_csv(claims, "claims"),
        "hospital": _read_csv(hospital, "hospital"),
        "people": _read_csv(people, "people"),
        "procedures": _read_csv(procedures, "procedures"),
        "drugs": _read_csv(drugs, "drugs"),
        "ambulatory": _read_csv(ambulatory, "ambulatory"),
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            cases = apply(
                ids,
                **tables,
                columns=columns or None,
                claims_coding=claims_coding,
                hospital_coding=hospital_coding,
                procedure_coding=procedure_coding,
                date_format=date_format,
            )
        except CasedefsInputError as exc:
            _fail(str(exc))
    seen = set()
    for w in caught:
        message = str(w.message)
        if message not in seen:
            seen.add(message)
            typer.secho(f"warning: {message}", fg=typer.colors.YELLOW, err=True)

    out = cases.copy()
    out["case_date"] = pd.to_datetime(out["case_date"]).dt.strftime("%Y-%m-%d")
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    label = ids[0] if len(ids) == 1 else f"{len(ids)} definitions"
    typer.echo(f"{len(out)} case(s) of {label} written to {output}")


@app.command()
def score(
    index: str = typer.Argument(..., help="charlson or elixhauser"),
    hospital: Optional[Path] = typer.Option(None, "--hospital", help="hospital discharge csv"),
    claims: Optional[Path] = typer.Option(None, "--claims", help="physician claims csv"),
    include_claims: bool = typer.Option(False, "--include-claims", help="also count physician claims"),
    index_dates: Optional[Path] = typer.Option(None, "--index-dates", help="csv of person_id, index_date"),
    lookback_days: Optional[int] = typer.Option(None, "--lookback-days", help="days before the index date"),
    output: Path = typer.Option(..., "--output", "-o", help="where to write scores csv"),
    map_: list[str] = typer.Option([], "--map", help="column mapping standard=yours, repeatable"),
    claims_coding: str = typer.Option("icd9", help="icd9, icd10ca or both"),
    hospital_coding: str = typer.Option("icd10ca", help="icd9, icd10ca or both"),
    date_format: Optional[str] = typer.Option(None, help="e.g. %d/%m/%Y, default is automatic"),
) -> None:
    """charlson or elixhauser comorbidity flags and score per person."""
    try:
        out = comorbidity_score(
            index,
            hospital=_read_csv(hospital, "hospital"),
            claims=_read_csv(claims, "claims"),
            index_dates=_read_csv(index_dates, "index dates"),
            lookback_days=lookback_days,
            include_claims=include_claims,
            columns=_parse_maps(map_) or None,
            claims_coding=claims_coding,
            hospital_coding=hospital_coding,
            date_format=date_format,
        )
    except CasedefsInputError as exc:
        _fail(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    typer.echo(f"{index} scores for {len(out)} person(s) written to {output}")


if __name__ == "__main__":  # pragma: no cover
    app()
