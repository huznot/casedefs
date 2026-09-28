"""turn user tables into tidy tables of dated records."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

import pandas as pd

from .codes import normalize_series

HOSPITAL_DATE_COLUMNS = ("separation_date", "admit_date", "date")
PROCEDURE_DATE_COLUMNS = ("procedure_date", "date")
AMBULATORY_DATE_COLUMNS = ("visit_date", "date")
DRUG_DATE_COLUMNS = ("dispense_date", "date")
ICD_VERSION_COLUMN = "icd_version"
PROC_SYSTEM_COLUMN = "proc_system"
CODINGS = ("icd9", "icd10ca", "both")
PROCEDURE_CODINGS = ("cci", "ccp", "icd9cm")

EVENT_COLUMNS = ["person_id", "date", "code", "coding", "source", "record_id"]
CLAIMS_COLUMNS = EVENT_COLUMNS + ["specialty"]
HOSPITAL_COLUMNS = EVENT_COLUMNS + ["dx_type", "admit_date"]


class CasedefsInputError(ValueError):
    """raised when an input table is missing columns or has bad values."""


def _rename(df: pd.DataFrame, columns: Mapping[str, object] | None) -> pd.DataFrame:
    # the mapping goes standard name -> user column name
    if not columns:
        return df
    reverse = {}
    for standard, theirs in columns.items():
        if isinstance(theirs, str) and theirs in df.columns and theirs != standard:
            reverse[theirs] = standard
    return df.rename(columns=reverse)


def _found(df: pd.DataFrame) -> str:
    return ", ".join(map(str, df.columns)) or "(none)"


def _require(df: pd.DataFrame, needed: Sequence[str], table: str) -> None:
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise CasedefsInputError(
            f"{table} table is missing column(s): {', '.join(missing)}. "
            f"columns found: {_found(df)}. "
            f"if your data uses other names, pass a mapping such as "
            f"columns={{'{missing[0]}': 'your_column_name'}}"
        )


def _pick(df: pd.DataFrame, names: Sequence[str], table: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    raise CasedefsInputError(
        f"{table} table needs a date column named one of: {', '.join(names)}. "
        f"columns found: {_found(df)}. map yours with columns={{'{names[0]}': 'your_column'}}"
    )


def parse_dates(values: pd.Series, table: str, column: str, date_format: str | None = None) -> pd.Series:
    """parse a date column, raising a readable error on blanks or bad values."""
    if pd.api.types.is_datetime64_any_dtype(values):
        parsed = values
    else:
        parsed = pd.to_datetime(values, errors="coerce", format=date_format)
    bad = parsed.isna()
    if bad.any():
        rows = list(values.index[bad][:5])
        shown = ", ".join(f"row {r}: {values.loc[r]!r}" for r in rows)
        more = f" (and {int(bad.sum()) - len(rows)} more)" if bad.sum() > len(rows) else ""
        raise CasedefsInputError(
            f"could not read {int(bad.sum())} date(s) in {table}.{column}: {shown}{more}. "
            f"use ISO dates like 2021-03-31, or pass date_format (e.g. '%d/%m/%Y')"
        )
    return parsed.dt.normalize()


def _optional_dates(values: pd.Series, table: str, column: str, date_format: str | None) -> pd.Series:
    """like parse_dates but blanks are allowed and become NaT."""
    known = values.notna() & (values.astype("string").str.strip() != "")
    out = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    if known.any():
        out.loc[known] = parse_dates(values[known], table, column, date_format).astype("datetime64[ns]")
    return out


def _coding_column(df: pd.DataFrame, default: str, table: str) -> pd.Series:
    if default not in CODINGS:
        raise CasedefsInputError(f"{table}: coding must be one of {', '.join(CODINGS)}, got {default!r}")
    if ICD_VERSION_COLUMN not in df.columns:
        return pd.Series(default, index=df.index)
    raw = df[ICD_VERSION_COLUMN].astype("string").str.strip().str.lower()
    mapped = raw.map(
        {"9": "icd9", "icd9": "icd9", "icd-9": "icd9", "10": "icd10ca", "icd10": "icd10ca",
         "icd10ca": "icd10ca", "icd-10": "icd10ca", "icd-10-ca": "icd10ca"}
    )
    bad = mapped.isna() & raw.notna()
    if bad.any():
        examples = ", ".join(sorted(set(raw[bad].astype(str)))[:5])
        raise CasedefsInputError(f"{table}.{ICD_VERSION_COLUMN} has values that are not 9 or 10: {examples}")
    return mapped.fillna(default)


def _proc_system_column(df: pd.DataFrame, default: str) -> pd.Series:
    if default not in PROCEDURE_CODINGS:
        raise CasedefsInputError(
            f"procedures: coding must be one of {', '.join(PROCEDURE_CODINGS)}, got {default!r}"
        )
    if PROC_SYSTEM_COLUMN not in df.columns:
        return pd.Series(default, index=df.index)
    raw = df[PROC_SYSTEM_COLUMN].astype("string").str.strip().str.lower().str.replace("-", "", regex=False)
    bad = ~raw.isin(PROCEDURE_CODINGS) & raw.notna()
    if bad.any():
        examples = ", ".join(sorted(set(raw[bad].astype(str)))[:5])
        raise CasedefsInputError(
            f"procedures.{PROC_SYSTEM_COLUMN} must be one of {', '.join(PROCEDURE_CODINGS)}, got: {examples}"
        )
    return raw.fillna(default)


def _numbered(df: pd.DataFrame, stem: str) -> list[str]:
    pattern = re.compile(rf"^{re.escape(stem)}_(\d+)$")
    cols = [c for c in df.columns if pattern.match(str(c))]
    return sorted(cols, key=lambda c: int(pattern.match(str(c)).group(1)))


def claims_events(
    claims: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    coding: str = "icd9",
    date_format: str | None = None,
) -> pd.DataFrame:
    df = _rename(claims, columns)
    _require(df, ["person_id", "service_date", "dx_code"], "claims")
    out = pd.DataFrame(
        {
            "person_id": df["person_id"],
            "date": parse_dates(df["service_date"], "claims", "service_date", date_format),
            "code": normalize_series(df["dx_code"]),
            "coding": _coding_column(df, coding, "claims"),
        }
    )
    if "specialty" in df.columns:
        out["specialty"] = df["specialty"].astype("string").str.strip().str.upper()
    else:
        out["specialty"] = pd.Series(pd.NA, index=df.index, dtype="string")
    out = out[out["code"] != ""]
    # identical rows are almost always the same claim loaded twice
    out = out.drop_duplicates(["person_id", "date", "code"]).reset_index(drop=True)
    out["source"] = "claims"
    out["record_id"] = range(len(out))
    out["code"] = out["code"].astype("category")
    return out[CLAIMS_COLUMNS]


def ambulatory_events(
    ambulatory: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    coding: str = "icd10ca",
    date_format: str | None = None,
) -> pd.DataFrame:
    """ed and clinic visits (nacrs, accs). same layout as hospital data, dated by visit_date."""
    return hospital_events(ambulatory, columns, coding, date_format, table="ambulatory")


def hospital_events(
    hospital: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    coding: str = "icd10ca",
    date_format: str | None = None,
    table: str = "hospital",
) -> pd.DataFrame:
    """one row per diagnosis code on a hospital record.

    `date` is the separation date when there is one, otherwise the admission
    date or `date`. `admit_date` is kept too when given, for definitions that
    count from admission.
    """
    df = _rename(hospital, columns).reset_index(drop=True)
    _require(df, ["person_id"], table)
    date_col = _pick(df, HOSPITAL_DATE_COLUMNS if table == "hospital" else AMBULATORY_DATE_COLUMNS, table)

    wide_cols = list(columns.get("hospital_dx_columns", [])) if columns else []
    type_cols = list(columns.get("hospital_dx_type_columns", [])) if columns else []
    if wide_cols:
        _require(df, wide_cols, table)
    else:
        wide_cols = _numbered(df, "dx_code")
    if not wide_cols and "dx_code" not in df.columns:
        raise CasedefsInputError(
            f"{table} table needs diagnosis columns: either dx_code (long format, one row per code) "
            "or dx_code_1, dx_code_2, ... (wide format, one row per stay). "
            f"columns found: {_found(df)}. for other names pass columns={{'hospital_dx_columns': [...]}}"
        )

    base = pd.DataFrame(
        {
            "person_id": df["person_id"],
            "date": parse_dates(df[date_col], table, date_col, date_format),
            "coding": _coding_column(df, coding, table),
        }
    )
    if "admit_date" in df.columns and date_col != "admit_date":
        base["admit_date"] = _optional_dates(df["admit_date"], table, "admit_date", date_format)
    elif date_col == "admit_date":
        base["admit_date"] = base["date"]
    else:
        base["admit_date"] = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

    if wide_cols:
        # one input row is one hospital stay
        base["record_id"] = range(len(base))
        if type_cols:
            _require(df, type_cols, table)
            if len(type_cols) != len(wide_cols):
                raise CasedefsInputError("hospital_dx_type_columns must line up one to one with hospital_dx_columns")
        else:
            by_number = {str(c).rsplit("_", 1)[-1]: c for c in _numbered(df, "dx_type")}
            type_cols = [by_number.get(str(c).rsplit("_", 1)[-1]) for c in wide_cols]
        pieces = []
        for dx_col, type_col in zip(wide_cols, type_cols):
            piece = base.copy()
            piece["code"] = df[dx_col]
            piece["dx_type"] = df[type_col] if type_col is not None else pd.NA
            pieces.append(piece)
        long = pd.concat(pieces, ignore_index=True)
    else:
        long = base.assign(code=df["dx_code"], dx_type=df["dx_type"] if "dx_type" in df.columns else pd.NA)
        # in long format a stay is every row sharing person and date
        long["record_id"] = long.groupby(["person_id", "date"], sort=False).ngroup()

    long["code"] = normalize_series(long["code"])
    long["dx_type"] = normalize_dx_type(long["dx_type"])
    long = long[long["code"] != ""].copy()
    long["source"] = table
    long["code"] = long["code"].astype("category")
    return long[HOSPITAL_COLUMNS].sort_values(["record_id"], kind="stable").reset_index(drop=True)


def normalize_dx_type(values: pd.Series) -> pd.Series:
    """'MRDx', 'm' -> 'M'; '1' -> '1'; blanks -> NA."""
    out = values.astype("string").str.strip().str.upper()
    out = out.where(out != "", pd.NA)
    return out.replace({"MRDX": "M", "MRD": "M"})


def procedure_events(
    procedures: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    coding: str = "cci",
    date_format: str | None = None,
) -> pd.DataFrame:
    """procedures in long (proc_code) or wide (proc_code_1, ...) format."""
    df = _rename(procedures, columns).reset_index(drop=True)
    _require(df, ["person_id"], "procedures")
    date_col = _pick(df, PROCEDURE_DATE_COLUMNS, "procedures")
    wide_cols = _numbered(df, "proc_code")
    if not wide_cols and "proc_code" not in df.columns:
        raise CasedefsInputError(
            "procedures table needs proc_code (one row per procedure) or proc_code_1, proc_code_2, ... "
            f"columns found: {_found(df)}"
        )
    base = pd.DataFrame(
        {
            "person_id": df["person_id"],
            "date": parse_dates(df[date_col], "procedures", date_col, date_format),
            "coding": _proc_system_column(df, coding),
        }
    )
    base["record_id"] = range(len(base))
    code_cols = wide_cols or ["proc_code"]
    long = pd.concat([base.assign(code=df[c]) for c in code_cols], ignore_index=True)
    long["code"] = normalize_series(long["code"])
    long = long[long["code"] != ""].copy()
    long["source"] = "procedures"
    return long[EVENT_COLUMNS].reset_index(drop=True)


def drug_events(
    drugs: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    date_format: str | None = None,
) -> pd.DataFrame:
    df = _rename(drugs, columns).reset_index(drop=True)
    _require(df, ["person_id", "din"], "drugs")
    date_col = _pick(df, DRUG_DATE_COLUMNS, "drugs")
    code = normalize_series(df["din"])
    # dins are 8 digits; numeric reads drop the leading zeros
    digits = code.str.fullmatch(r"\d{1,8}").fillna(False)
    code = code.where(~digits, code.str.zfill(8))
    out = pd.DataFrame(
        {
            "person_id": df["person_id"],
            "date": parse_dates(df[date_col], "drugs", date_col, date_format),
            "code": code,
            "coding": "din",
        }
    )
    out = out[out["code"] != ""].reset_index(drop=True)
    out["source"] = "drugs"
    out["record_id"] = range(len(out))
    return out[EVENT_COLUMNS]


def people_table(
    people: pd.DataFrame,
    columns: Mapping[str, object] | None = None,
    date_format: str | None = None,
) -> pd.DataFrame:
    df = _rename(people, columns).reset_index(drop=True)
    _require(df, ["person_id", "birth_date"], "people")
    out = pd.DataFrame({"person_id": df["person_id"]})
    out["birth_date"] = _optional_dates(df["birth_date"], "people", "birth_date", date_format)
    if "sex" in df.columns:
        out["sex"] = df["sex"].astype("string").str.strip().str.upper().str[:1]
    else:
        out["sex"] = pd.Series(pd.NA, index=df.index, dtype="string")
    dupes = out["person_id"].duplicated()
    if dupes.any():
        example = out.loc[dupes, "person_id"].iloc[0]
        raise CasedefsInputError(f"people table has more than one row for person_id {example!r}")
    return out


def align_person_ids(*tables: pd.DataFrame | None) -> list[pd.DataFrame | None]:
    """make person_id comparable across tables. if dtypes differ, use strings."""
    present = [t for t in tables if t is not None]
    kinds = {str(t["person_id"].dtype) for t in present}
    if len(kinds) <= 1:
        return list(tables)
    return [None if t is None else t.assign(person_id=t["person_id"].astype(str)) for t in tables]
