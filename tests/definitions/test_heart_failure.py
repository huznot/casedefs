import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people

ID = "ccdss.heart_failure"


def run(cl=None, hosp=None, pp=None, **kw):
    pp = pp if pp is not None else people((1, "1950-01-01", "F"))
    return apply(ID, claims=cl, hospital=hosp, people=pp, **kw)


def test_metadata_matches_source():
    d = get_definition(ID)
    assert d.verified
    assert d.icd9 == ("428",)
    assert d.icd10ca == ("I50",)
    assert (d.rule.min_hospital, d.rule.min_claims, d.rule.window_days) == (1, 2, 365)
    assert d.min_age == 40
    assert "row 18" in d.source_location


def test_two_claims_365_days_apart_qualify():
    assert case_day(run(claims((1, 0, "428"), (1, 365, "428.0"))), 1) == 365


def test_two_claims_366_days_apart_do_not():
    assert run(claims((1, 0, "428"), (1, 366, "428"))).empty


def test_one_hospital_record():
    assert ids(run(hosp=hospital((1, 0, "I50.0")))) == {1}


@pytest.mark.parametrize("code", ["I51", "I49", "I5"])
def test_near_miss_icd10(code):
    assert run(hosp=hospital((1, 0, code))).empty


@pytest.mark.parametrize("code", ["427", "429"])
def test_near_miss_icd9(code):
    assert run(claims((1, 0, code), (1, 1, code))).empty


def test_age_39_not_a_case():
    assert run(hosp=hospital((1, 0, "I50")), pp=people((1, "1975-06-01", "M"))).empty


def test_age_40_is_a_case():
    assert ids(run(hosp=hospital((1, 0, "I50")), pp=people((1, "1975-01-01", "M")))) == {1}
