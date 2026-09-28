import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people

ID = "ccdss.asthma"


def run(cl=None, hosp=None, pp=None, **kw):
    pp = pp if pp is not None else people((1, "2000-01-01", "F"))
    return apply(ID, claims=cl, hospital=hosp, people=pp, **kw)


def test_metadata_matches_source():
    d = get_definition(ID)
    assert d.verified
    assert d.icd9 == ("493",)
    assert d.icd10ca == ("J45", "J46")
    assert (d.rule.min_hospital, d.rule.min_claims, d.rule.window_days) == (1, 2, 730)
    assert d.min_age == 1
    assert d.exclusions == ()
    assert "row 11" in d.source_location


@pytest.mark.parametrize("code", ["J45", "J45.9", "J46"])
def test_icd10ca_hospital(code):
    assert ids(run(hosp=hospital((1, 0, "A00", code)))) == {1}


@pytest.mark.parametrize("code", ["493", "493.9"])
def test_icd9_claims(code):
    assert case_day(run(claims((1, 0, code), (1, 730, code))), 1) == 730


def test_731_days_is_a_miss():
    assert run(claims((1, 0, "493"), (1, 731, "493"))).empty


@pytest.mark.parametrize("code", ["J44", "J47", "492", "494"])
def test_near_miss_codes(code):
    coding = "icd9" if code[0].isdigit() else "icd10ca"
    assert run(claims((1, 0, code), (1, 10, code)), claims_coding=coding).empty


def test_under_one_year_old():
    pp = people((1, "2014-06-01", "M"))
    assert run(hosp=hospital((1, 0, "J45")), pp=pp).empty


def test_no_pregnancy_exclusion():
    pp = people((1, "1990-01-01", "F"))
    assert ids(run(hosp=hospital((1, 0, "J45"), (1, 10, "O80")), pp=pp)) == {1}
