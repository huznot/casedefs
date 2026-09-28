from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from . import __version__, apply
from .definition import ClaimsExclusion, Composite, Exclusion
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


def _compact(codes: tuple[str, ...]) -> str:
    """show runs like O21, O22, ... O95 as O21-O95."""
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
            out.append(f"{run[0]}-{run[-1]}")
        else:
            out.extend(run)
        run.clear()

    for code in codes:
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
def list_cmd() -> None:
    """list all definitions with source and verified status."""
    defs = list(all_definitions().values())
    width = max(len(d.id) for d in defs)
    typer.echo(f"{'ID':<{width}}  {'VERSION':<8} {'VERIFIED':<9} {'AGES':<9} NAME")
    for d in defs:
        flag = "yes" if d.verified else "NO"
        typer.echo(f"{d.id:<{width}}  {d.version:<8} {flag:<9} {d.age_text():<9} {d.name}")
    sources = sorted({d.source_url for d in defs})
    typer.echo("")
    typer.echo("source" + ("s" if len(sources) > 1 else "") + ":")
    for s in sources:
        typer.echo(f"  {s}")
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
            "conditions: " + ", ".join(d.components),
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
    if d.excluded_codes:
        lines.append(f"never counts:        {', '.join(d.excluded_codes)}")
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
    first = next(iter(d.icd10ca or d.icd9 or icd10 or icd9), None)
    if first:
        lines.append(f"codes match by prefix, so {first} also covers {first}.x")
    for e in d.exclusions:
        lines += ["", f"exclusion:  {e.name}", f"  {e.description}"]
        if isinstance(e, (Exclusion, ClaimsExclusion)):
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
    definition_ids: list[str] = typer.Argument(..., help="one or more ids, e.g. ccdss.diabetes, or 'all'"),
    claims: Optional[Path] = typer.Option(None, "--claims", help="physician claims csv"),
    hospital: Optional[Path] = typer.Option(None, "--hospital", help="hospital discharge csv"),
    people: Optional[Path] = typer.Option(None, "--people", help="people csv with person_id, birth_date, sex"),
    procedures: Optional[Path] = typer.Option(None, "--procedures", help="procedures csv (for ihd)"),
    drugs: Optional[Path] = typer.Option(None, "--drugs", help="drug dispensations csv (for dementia)"),
    output: Path = typer.Option(..., "--output", "-o", help="where to write cases csv"),
    map_: list[str] = typer.Option([], "--map", help="column mapping standard=yours, repeatable"),
    hospital_dx: Optional[str] = typer.Option(None, "--hospital-dx", help="comma separated hospital dx columns"),
    claims_coding: str = typer.Option("icd9", help="icd9, icd10ca or both"),
    hospital_coding: str = typer.Option("icd10ca", help="icd9, icd10ca or both"),
    procedure_coding: str = typer.Option("cci", help="cci, ccp or icd9cm"),
    date_format: Optional[str] = typer.Option(None, help="e.g. %d/%m/%Y, default is automatic"),
) -> None:
    """find cases and write them to a csv."""
    ids = list(all_definitions()) if definition_ids == ["all"] else definition_ids
    for def_id in ids:
        try:
            get_definition(def_id)
        except KeyError as exc:
            _fail(str(exc.args[0]))
    if claims is None and hospital is None and procedures is None and drugs is None:
        _fail("pass at least one of --claims, --hospital, --procedures or --drugs")

    columns = _parse_maps(map_)
    if hospital_dx:
        columns["hospital_dx_columns"] = [c.strip() for c in hospital_dx.split(",") if c.strip()]

    tables = {
        "claims": _read_csv(claims, "claims"),
        "hospital": _read_csv(hospital, "hospital"),
        "people": _read_csv(people, "people"),
        "procedures": _read_csv(procedures, "procedures"),
        "drugs": _read_csv(drugs, "drugs"),
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


if __name__ == "__main__":  # pragma: no cover
    app()
