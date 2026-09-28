from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def normalize_code(code: object) -> str:
    """uppercase a diagnosis code and drop dots and spaces. '250.1 ' -> '2501'."""
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return ""
    return str(code).strip().upper().replace(".", "").replace(" ", "")


def normalize_series(codes: pd.Series) -> pd.Series:
    out = codes.astype("string").str.strip().str.upper()
    out = out.str.replace(".", "", regex=False).str.replace(" ", "", regex=False)
    return out.fillna("")


def matches_any(codes: pd.Series, prefixes: Iterable[str]) -> pd.Series:
    """true where a (normalized) code starts with any of the prefixes.

    'E11' matches 'E119' and 'E11.9'. '250' matches '2501' and '250'.
    """
    clean = tuple(p for p in (normalize_code(p) for p in prefixes) if p)
    if not clean or codes.empty:
        return pd.Series(False, index=codes.index)
    # real data has far fewer distinct codes than rows, so match those once
    distinct = pd.unique(codes.to_numpy())
    hits = {c for c in distinct if normalize_code(c).startswith(clean)}
    return codes.isin(hits)
