"""small builders for synthetic test data. no real data is used anywhere."""

from __future__ import annotations

import pandas as pd
import pytest

BASE = pd.Timestamp("2015-01-01")


def day(n: int) -> str:
    return (BASE + pd.Timedelta(days=n)).strftime("%Y-%m-%d")


def claims(*rows: tuple) -> pd.DataFrame:
    """rows of (person_id, day_offset, dx_code)."""
    return pd.DataFrame(
        [{"person_id": p, "service_date": day(d), "dx_code": c} for p, d, c in rows],
        columns=["person_id", "service_date", "dx_code"],
    )


def hospital(*rows: tuple) -> pd.DataFrame:
    """rows of (person_id, day_offset, code, code, ...) in wide format."""
    width = max((len(r) - 2 for r in rows), default=1)
    records = []
    for p, d, *codes in rows:
        rec = {"person_id": p, "separation_date": day(d)}
        for i in range(width):
            rec[f"dx_code_{i + 1}"] = codes[i] if i < len(codes) else None
        records.append(rec)
    cols = ["person_id", "separation_date"] + [f"dx_code_{i + 1}" for i in range(width)]
    return pd.DataFrame(records, columns=cols)


def people(*rows: tuple) -> pd.DataFrame:
    """rows of (person_id, birth_date, sex)."""
    return pd.DataFrame(rows, columns=["person_id", "birth_date", "sex"])


def ids(result: pd.DataFrame) -> set:
    return set(result["person_id"])


def case_day(result: pd.DataFrame, person) -> int:
    row = result[result["person_id"] == person]
    assert len(row) == 1, f"expected one case for {person}"
    return (row["case_date"].iloc[0] - BASE).days


@pytest.fixture
def adult_people():
    # everyone 40 on the base date, sex unknown unless a test says otherwise
    return lambda *pids, sex="M": people(*[(p, "1975-01-01", sex) for p in pids])
