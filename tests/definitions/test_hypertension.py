import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people

ID = "ccdss.hypertension"


def run(cl=None, hosp=None, pp=None, **kw):
    pp = pp if pp is not None else people((1, "1960-01-01", "M"))
    return apply(ID, claims=cl, hospital=hosp, people=pp, **kw)


def test_metadata_matches_source():
    d = get_definition(ID)
    assert d.verified
    assert d.icd9 == ("401", "402", "403", "404", "405")
    assert d.icd10ca == ("I10", "I11", "I12", "I13", "I15")
    assert (d.rule.min_hospital, d.rule.min_claims, d.rule.window_days) == (1, 2, 730)
    assert d.min_age == 20
    assert d.exclusions[0].min_age == 20 and d.exclusions[0].max_age == 54
    assert "row 14" in d.source_location


@pytest.mark.parametrize("code", ["401", "401.9", "402", "403.0", "404", "405.1"])
def test_icd9_codes(code):
    assert ids(run(claims((1, 0, code), (1, 100, code)))) == {1}


@pytest.mark.parametrize("code", ["I10", "I11.0", "I12", "I13.9", "I15.0"])
def test_icd10ca_codes(code):
    assert ids(run(hosp=hospital((1, 0, code)))) == {1}


@pytest.mark.parametrize("code", ["I14", "I16", "406", "400"])
def test_near_miss_codes(code):
    coding = "icd9" if code[0].isdigit() else "icd10ca"
    assert run(hosp=hospital((1, 0, code)), hospital_coding=coding).empty


def test_window_730_vs_731():
    assert case_day(run(claims((1, 0, "401"), (1, 730, "401"))), 1) == 730
    assert run(claims((1, 0, "401"), (1, 731, "401"))).empty


def test_single_claim_not_enough():
    assert run(claims((1, 0, "401"))).empty


def test_age_19_not_a_case():
    assert run(hosp=hospital((1, 0, "I10")), pp=people((1, "1996-01-01", "M"))).empty


def test_age_20_is_a_case():
    assert ids(run(hosp=hospital((1, 0, "I10")), pp=people((1, "1995-01-01", "M")))) == {1}


def test_gestational_hypertension_excluded():
    pp = people((1, "1990-01-01", "F"))
    assert run(claims((1, 0, "401"), (1, 30, "401")), hospital((1, 60, "O13")), pp).empty


def test_woman_over_54_not_excluded():
    pp = people((1, "1955-01-01", "F"))
    assert ids(run(claims((1, 0, "401"), (1, 30, "401")), hospital((1, 60, "O13")), pp)) == {1}
