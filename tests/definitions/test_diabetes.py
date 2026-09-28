import pandas as pd
import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people

ID = "ccdss.diabetes"


def run(cl=None, hosp=None, pp=None, **kw):
    if pp is None:
        pids = set()
        for df in (cl, hosp):
            if df is not None:
                pids |= set(df["person_id"])
        pp = people(*[(p, "1970-01-01", "M") for p in sorted(pids)])
    return apply(ID, claims=cl, hospital=hosp, people=pp, **kw)


def test_metadata_matches_source():
    d = get_definition(ID)
    assert d.verified
    assert d.icd9 == ("250",)
    assert d.icd10ca == ("E10", "E11", "E13", "E14")
    assert (d.rule.min_hospital, d.rule.min_claims, d.rule.window_days) == (1, 2, 730)
    assert d.min_age == 1
    assert "row 6" in d.source_location


@pytest.mark.parametrize("code", ["250", "250.00", "2509", "250.4"])
def test_icd9_claims_variants(code):
    assert ids(run(claims((1, 0, code), (1, 30, code)))) == {1}


@pytest.mark.parametrize("code", ["E10", "E11.9", "E119", "e13.1", "E14"])
def test_icd10ca_hospital_variants(code):
    assert ids(run(hosp=hospital((1, 0, "I10", code)))) == {1}


def test_e12_is_not_in_the_definition():
    # E12 (malnutrition-related diabetes) is not listed by the ccdss
    assert run(hosp=hospital((1, 0, "E12"))).empty


def test_two_claims_730_days_apart_qualify():
    res = run(claims((1, 0, "250"), (1, 730, "250")))
    assert case_day(res, 1) == 730


def test_two_claims_731_days_apart_do_not():
    assert run(claims((1, 0, "250"), (1, 731, "250"))).empty


def test_one_claim_does_not_qualify():
    assert run(claims((1, 0, "250"))).empty


def test_one_hospital_record_qualifies():
    assert case_day(run(hosp=hospital((1, 42, "E11"))), 1) == 42


def test_infant_under_one_is_not_a_case():
    pp = people((1, "2014-06-01", "F"))
    assert run(hosp=hospital((1, 0, "E10")), pp=pp).empty


def test_turns_one_then_qualifies():
    pp = people((1, "2014-06-01", "F"))
    res = run(claims((1, 0, "250"), (1, 100, "250"), (1, 160, "250")), pp=pp)
    # day 151 is 2015-06-01; the claim on day 160 is the first after the first birthday
    assert case_day(res, 1) == 160


class TestGestational:
    def pp(self, sex="F", birth="1985-01-01"):
        return people((1, birth, sex))

    def test_claims_during_pregnancy_excluded(self):
        cl = claims((1, 100, "250"), (1, 150, "250"))
        hosp = hospital((1, 200, "Z37.0"))
        assert run(cl, hosp, self.pp()).empty

    def test_hospital_diabetes_code_with_pregnancy_code_excluded(self):
        assert run(hosp=hospital((1, 10, "O24.4", "E11.9", "O80")), pp=self.pp()).empty

    @pytest.mark.parametrize("code", ["O10", "O16.9", "O21", "O95", "O98.1", "O99.8", "Z37"])
    def test_each_pregnancy_block(self, code):
        assert run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, code)), self.pp()).empty

    @pytest.mark.parametrize("code", ["O17", "O20", "O96", "O97", "Z36"])
    def test_codes_outside_pregnancy_blocks_do_not_exclude(self, code):
        res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, code)), self.pp())
        assert ids(res) == {1}

    def test_icd9_pregnancy_codes(self):
        for code in ["641", "650", "679.1", "V27.0"]:
            res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, code)), self.pp(), hospital_coding="icd9")
            assert res.empty, code

    def test_121_days_before_pregnancy_record_is_fine(self):
        res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 131, "O80")), self.pp())
        assert case_day(res, 1) == 10

    def test_181_days_after_pregnancy_record_is_fine(self):
        res = run(claims((1, 150, "250"), (1, 191, "250")), hospital((1, 10, "O80")), self.pp())
        assert case_day(res, 1) == 191

    def test_woman_aged_55_not_excluded(self):
        res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, "O80")), self.pp(birth="1959-01-01"))
        assert ids(res) == {1}

    def test_girl_aged_9_not_excluded(self):
        res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, "O80")), self.pp(birth="2005-06-01"))
        assert ids(res) == {1}

    def test_man_with_odd_code_not_excluded(self):
        res = run(claims((1, 0, "250"), (1, 10, "250")), hospital((1, 20, "O80")), self.pp(sex="M"))
        assert ids(res) == {1}

    def test_persistent_diabetes_after_pregnancy_counts(self):
        cl = claims((1, 100, "250"), (1, 150, "250"), (1, 500, "250"))
        res = run(cl, hospital((1, 200, "O80")), self.pp())
        assert case_day(res, 1) == 500


def test_mixed_population():
    cl = pd.concat(
        [
            claims((1, 0, "250"), (1, 730, "250.0")),  # case at 730
            claims((2, 0, "250"), (2, 731, "250")),  # near miss
            claims((3, 0, "401"), (3, 10, "401")),  # hypertension only
        ]
    )
    hosp = hospital((4, 55, "E11.65"), (5, 20, "E11"), (5, 25, "O24.4"))
    pp = people((1, "1960-01-01", "M"), (2, "1960-01-01", "F"), (3, "1960-01-01", "F"),
                (4, "1950-01-01", "M"), (5, "1990-01-01", "F"))
    res = run(cl, hosp, pp)
    assert ids(res) == {1, 4}
    assert set(res["definition_version"]) == {"v2024"}
