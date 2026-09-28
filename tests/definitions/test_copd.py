import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people

ID = "ccdss.copd"


def run(cl=None, hosp=None, pp=None, **kw):
    pp = pp if pp is not None else people((1, "1950-01-01", "M"))
    return apply(ID, claims=cl, hospital=hosp, people=pp, **kw)


def test_metadata_matches_source():
    d = get_definition(ID)
    assert d.verified
    assert d.icd9 == ("491", "492", "496")
    assert d.icd10ca == ("J41", "J42", "J43", "J44")
    assert (d.rule.min_hospital, d.rule.min_claims) == (1, 1)
    assert d.min_age == 35
    assert "row 13" in d.source_location


@pytest.mark.parametrize("code", ["491", "491.2", "492", "496"])
def test_single_icd9_claim_is_enough(code):
    assert case_day(run(claims((1, 7, code))), 1) == 7


@pytest.mark.parametrize("code", ["J41", "J42", "J43.9", "J44.1"])
def test_single_hospital_record_is_enough(code):
    assert ids(run(hosp=hospital((1, 0, code)))) == {1}


@pytest.mark.parametrize("code", ["490", "493", "495"])
def test_near_miss_icd9(code):
    assert run(claims((1, 0, code))).empty


@pytest.mark.parametrize("code", ["J40", "J45", "J47"])
def test_near_miss_icd10(code):
    assert run(hosp=hospital((1, 0, code))).empty


def test_first_record_is_case_date():
    res = run(claims((1, 50, "496")), hospital((1, 20, "J44")))
    assert case_day(res, 1) == 20


def test_age_34_not_a_case():
    assert run(claims((1, 0, "496")), pp=people((1, "1980-06-01", "M"))).empty


def test_age_35_is_a_case():
    assert ids(run(claims((1, 0, "496")), pp=people((1, "1980-01-01", "M")))) == {1}
