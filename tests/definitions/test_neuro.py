import pandas as pd
import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, day, hospital, ids, people

OLD = people((1, "1940-01-01", "F"))


class TestDementia:
    ID = "ccdss.dementia"

    def run(self, pp=OLD, **kw):
        return apply(self.ID, people=pp, **kw)

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.verified and d.min_age == 65
        assert d.claims_codes == (("290", "331"), ("G30", "F00", "F01", "F02", "F03"))
        assert len(d.drug_dins) == 223 and d.drug_dins[0] == "02232043"
        assert (d.rule.min_claims, d.rule.window_days, d.rule.min_days_between, d.rule.min_drugs) == (3, 730, 30, 1)

    @pytest.mark.parametrize("code", ["046.1", "290.0", "290.4", "294.1", "294.2", "331.0", "331.1", "331.5", "331.82"])
    def test_hospital_icd9(self, code):
        assert ids(self.run(hospital=hospital((1, 0, code)), hospital_coding="icd9")) == {1}

    @pytest.mark.parametrize("code", ["290.5", "294.8", "331.2", "046.0"])
    def test_hospital_icd9_near_miss(self, code):
        assert self.run(hospital=hospital((1, 0, code)), hospital_coding="icd9").empty

    @pytest.mark.parametrize("code", ["G30.1", "F00", "F01.9", "F02", "F03"])
    def test_hospital_icd10(self, code):
        assert ids(self.run(hospital=hospital((1, 0, code)))) == {1}

    def test_three_claims_30_days_apart(self):
        res = self.run(claims=claims((1, 0, "290"), (1, 30, "331"), (1, 60, "290")))
        assert case_day(res, 1) == 60

    def test_three_claims_29_days_apart_miss(self):
        assert self.run(claims=claims((1, 0, "290"), (1, 29, "290"), (1, 58, "290"))).empty

    def test_two_claims_not_enough(self):
        assert self.run(claims=claims((1, 0, "290"), (1, 100, "290"))).empty

    def test_drug_path(self):
        drugs = pd.DataFrame({"person_id": [1], "dispense_date": [day(12)], "din": ["02232043"]})
        assert case_day(self.run(drugs=drugs), 1) == 12

    def test_other_drug_does_not_count(self):
        drugs = pd.DataFrame({"person_id": [1], "dispense_date": [day(12)], "din": ["00000001"]})
        assert self.run(drugs=drugs).empty

    def test_age_64(self):
        assert self.run(hospital=hospital((1, 0, "F03")), pp=people((1, "1950-06-01", "M"))).empty


class TestEpilepsy:
    ID = "ccdss.epilepsy"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.verified and d.min_age == 1 and d.rule.hospital_min_age == 20
        assert d.icd9 == ("345.0", "345.1", "345.4", "345.5", "345.6", "345.7", "345.8", "345.9")
        assert d.claims_codes == (("345",), ("G40",))

    def test_adult_hospital(self):
        res = apply(self.ID, hospital=hospital((1, 0, "G40.9")), people=people((1, "1980-01-01", "M")))
        assert ids(res) == {1}

    def test_child_hospital_does_not_count(self):
        assert apply(self.ID, hospital=hospital((1, 0, "G40")), people=people((1, "2005-01-01", "M"))).empty

    def test_child_three_claims(self):
        cl = claims((1, 0, "345"), (1, 30, "345"), (1, 60, "345"))
        assert case_day(apply(self.ID, claims=cl, people=people((1, "2005-01-01", "M"))), 1) == 60

    @pytest.mark.parametrize("code", ["345.2", "345.3"])
    def test_hospital_icd9_status_codes_not_listed(self, code):
        pp = people((1, "1980-01-01", "M"))
        assert apply(self.ID, hospital=hospital((1, 0, code)), people=pp, hospital_coding="icd9").empty

    def test_claims_gap_miss(self):
        cl = claims((1, 0, "345"), (1, 30, "345"), (1, 50, "345"))
        assert apply(self.ID, claims=cl, people=people((1, "1980-01-01", "M"))).empty


class TestMultipleSclerosis:
    ID = "ccdss.multiple_sclerosis"
    pp = people((1, "1970-01-01", "F"))

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.verified and d.icd9 == ("340",) and d.icd10ca == ("G35",) and d.min_age == 20
        assert (d.rule.min_claims, d.rule.window_days) == (5, 730)

    def test_five_claims_within_730(self):
        cl = claims(*[(1, d, "340") for d in (0, 100, 200, 300, 730)])
        assert case_day(apply(self.ID, claims=cl, people=self.pp), 1) == 730

    def test_five_claims_over_730(self):
        cl = claims(*[(1, d, "340") for d in (0, 100, 200, 300, 731)])
        assert apply(self.ID, claims=cl, people=self.pp).empty

    def test_four_claims(self):
        cl = claims(*[(1, d, "340") for d in (0, 10, 20, 30)])
        assert apply(self.ID, claims=cl, people=self.pp).empty

    def test_hospital(self):
        assert ids(apply(self.ID, hospital=hospital((1, 0, "G35")), people=self.pp)) == {1}

    def test_near_miss_code(self):
        assert apply(self.ID, hospital=hospital((1, 0, "G36")), people=self.pp).empty


class TestParkinsonism:
    ID = "ccdss.parkinsonism"
    pp = people((1, "1950-01-01", "M"))

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.verified and d.rule.min_hospital is None and d.min_age == 40
        assert d.claims_codes == (("332",), ("F02.3", "G20", "G21", "G22"))

    def test_two_claims_30_days_apart(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "332"), (1, 30, "332")), people=self.pp), 1) == 30

    def test_29_days_apart(self):
        assert apply(self.ID, claims=claims((1, 0, "332"), (1, 29, "332")), people=self.pp).empty

    def test_366_days_apart(self):
        assert apply(self.ID, claims=claims((1, 0, "332"), (1, 366, "332")), people=self.pp).empty

    def test_hospital_does_not_count(self):
        assert apply(self.ID, hospital=hospital((1, 0, "G20")), people=self.pp).empty

    @pytest.mark.parametrize("code", ["F02.3", "G20", "G21.1", "G22"])
    def test_icd10_claims(self, code):
        cl = claims((1, 0, code), (1, 40, code))
        assert ids(apply(self.ID, claims=cl, people=self.pp, claims_coding="icd10ca")) == {1}

    def test_f02_other_is_not_parkinsonism(self):
        cl = claims((1, 0, "F02.0"), (1, 40, "F02.0"))
        assert apply(self.ID, claims=cl, people=self.pp, claims_coding="icd10ca").empty
