"""a true case and a near miss for every registered definition.

each definition gets synthetic records built from its own rule and its first
listed code, so a new definition is covered as soon as it is added.
"""

import warnings

import pandas as pd
import pytest

from casedefs import Composite, apply
from casedefs.registry import all_definitions

from ..conftest import BASE

NOT_A_CODE = "ZZZ999"


def _age_for(defn) -> int:
    lo = defn.min_age if defn.min_age is not None else 0
    hi = defn.max_age if defn.max_age is not None else 120
    age = max(lo, min(50, hi))
    if defn.rule.hospital_min_age is not None:
        age = max(age, defn.rule.hospital_min_age)
    return min(age, hi)


def _records(defn, code, n):
    """n records on the first path this definition has, spaced to satisfy gaps."""
    rule = defn.rule
    gap = max(rule.min_days_between, 1)
    days = [i * gap for i in range(n)]
    dates = [(BASE + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in days]
    if rule.min_hospital:
        df = pd.DataFrame({"person_id": 1, "separation_date": dates, "dx_code_1": code})
        df["dx_type_1"] = "M"
        df["admit_date"] = dates
        return {"hospital": df}
    if rule.min_claims:
        df = pd.DataFrame({"person_id": 1, "service_date": dates, "dx_code": code})
        if defn.claims_specialties:
            df["specialty"] = defn.claims_specialties[0]
        return {"claims": df}
    raise AssertionError(f"no hospital or claims path: {defn.id}")


def _path_size(defn):
    rule = defn.rule
    return rule.min_hospital or rule.min_claims


def _first_code(defn):
    if defn.rule.min_hospital:
        codes, coding = (defn.icd10ca, "icd10ca") if defn.icd10ca else (defn.icd9, "icd9")
    else:
        icd9, icd10 = defn.claims_codes
        codes, coding = (icd10, "icd10ca") if icd10 else (icd9, "icd9")
    return codes[0], coding


PLAIN = [d for d in all_definitions().values() if not isinstance(d, Composite)]


def _run(defn, code, coding, n):
    tables = _records(defn, code, n)
    birth = (BASE - pd.DateOffset(years=_age_for(defn), days=1)).strftime("%Y-%m-%d")
    people = pd.DataFrame({"person_id": [1], "birth_date": [birth], "sex": ["M"]})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return apply(defn, people=people, hospital_coding=coding, claims_coding=coding, **tables)


@pytest.mark.parametrize("defn", PLAIN, ids=lambda d: d.id)
def test_true_case(defn):
    code, coding = _first_code(defn)
    assert list(_run(defn, code, coding, _path_size(defn))["person_id"]) == [1]


@pytest.mark.parametrize("defn", PLAIN, ids=lambda d: d.id)
def test_unrelated_code_is_not_a_case(defn):
    _, coding = _first_code(defn)
    assert _run(defn, NOT_A_CODE, coding, _path_size(defn)).empty


@pytest.mark.parametrize("defn", [d for d in PLAIN if _path_size(d) > 1], ids=lambda d: d.id)
def test_one_record_short_is_not_a_case(defn):
    code, coding = _first_code(defn)
    assert _run(defn, code, coding, _path_size(defn) - 1).empty
