"""charlson and elixhauser comorbidity scores."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

import pandas as pd

from . import engine, inputs
from .definition import Rule
from .definitions.quan import charlson, elixhauser
from .inputs import CasedefsInputError

INDEXES = {
    "charlson": (charlson.DEFINITIONS, charlson.WEIGHTS),
    # the MCHP concept dictionary scores elixhauser as a plain count
    "elixhauser": (elixhauser.DEFINITIONS, None),
}


def _window(events: pd.DataFrame | None, index_dates: pd.DataFrame | None, lookback_days: int | None):
    """keep records on or before each person's index date, back to the lookback."""
    if events is None or index_dates is None:
        return events
    merged = events.merge(index_dates, on="person_id", how="inner")
    keep = merged["date"] <= merged["index_date"]
    if lookback_days is not None:
        keep &= merged["date"] >= merged["index_date"] - pd.Timedelta(days=lookback_days)
    return merged.loc[keep, events.columns].reset_index(drop=True)


def comorbidity_score(
    index: str = "charlson",
    hospital: pd.DataFrame | None = None,
    claims: pd.DataFrame | None = None,
    index_dates: pd.DataFrame | None = None,
    lookback_days: int | None = None,
    include_claims: bool = False,
    columns: Mapping[str, object] | None = None,
    claims_coding: str = "icd9",
    hospital_coding: str = "icd10ca",
    date_format: str | None = None,
) -> pd.DataFrame:
    """one row per person: a 0/1 column per comorbidity and a score.

    index is "charlson" (weighted sum) or "elixhauser" (count of conditions).

    index_dates, if given, is a table of person_id and index_date (one row
    per person). only records on or before the index date count, going back
    lookback_days if set, and every person in index_dates gets a row. without
    it, all records count and the output has everyone with any record.

    the quan algorithms are for hospital abstracts. include_claims=True also
    counts physician claims with the same codes, as the MCHP concept
    dictionary does.
    """
    if index not in INDEXES:
        raise CasedefsInputError(f"index must be one of {', '.join(INDEXES)}, got {index!r}")
    defs, weights = INDEXES[index]
    if hospital is None and claims is None:
        raise CasedefsInputError("pass hospital, claims, or both")
    if claims is not None and not include_claims and hospital is None:
        raise CasedefsInputError("these algorithms use hospital records; pass include_claims=True to use claims")

    hosp = None if hospital is None else inputs.hospital_events(hospital, columns, hospital_coding, date_format)
    cl = None
    if claims is not None and include_claims:
        cl = inputs.claims_events(claims, columns, claims_coding, date_format)

    idx = None
    if index_dates is not None:
        frame = inputs._rename(index_dates, columns)
        inputs._require(frame, ["person_id", "index_date"], "index_dates")
        if frame["person_id"].duplicated().any():
            raise CasedefsInputError("index_dates must have one row per person_id")
        idx = pd.DataFrame({
            "person_id": frame["person_id"],
            "index_date": inputs.parse_dates(frame["index_date"], "index_dates", "index_date", date_format),
        })
    hosp, cl, idx = inputs.align_person_ids(hosp, cl, idx)
    tables = engine.Tables(hospital=_window(hosp, idx, lookback_days), claims=_window(cl, idx, lookback_days))

    if idx is not None:
        people = idx[["person_id"]]
    else:
        ids = [t["person_id"] for t in (hosp, cl) if t is not None]
        people = pd.DataFrame({"person_id": pd.unique(pd.concat(ids))}) if ids else pd.DataFrame({"person_id": []})
    out = people.reset_index(drop=True).copy()

    rule = Rule(min_hospital=1, min_claims=1 if include_claims else None)
    names = []
    for d in defs:
        key = d.id.rsplit(".", 1)[1]
        names.append(key)
        found = engine.run(dataclasses.replace(d, rule=rule), tables)
        out[key] = out["person_id"].isin(set(found["person_id"])).astype(int)

    if weights is None:
        out["score"] = out[names].sum(axis=1)
    else:
        out["score"] = sum(out[k] * weights[k] for k in names)
    return out
