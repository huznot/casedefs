import pandas as pd
import pytest

from casedefs import ClaimsExclusion, apply, get_definition

from ..conftest import case_day, claims, day, hospital, ids, people

ADULT = people((1, "1960-01-01", "F"))


class TestOsteoporosis:
    ID = "ccdss.osteoporosis"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.verified and d.min_age == 40
        assert d.icd9 == ("733.0",) and d.claims_codes == (("733",), ("M80", "M81"))

    def test_one_claim(self):
        assert case_day(apply(self.ID, claims=claims((1, 3, "733")), people=ADULT), 1) == 3

    def test_hospital_733_1_is_not_osteoporosis(self):
        assert apply(self.ID, hospital=hospital((1, 0, "733.1")), people=ADULT, hospital_coding="icd9").empty
        assert ids(apply(self.ID, hospital=hospital((1, 0, "733.00")), people=ADULT, hospital_coding="icd9")) == {1}

    def test_icd10(self):
        df = hospital((1, 20, "M81.0"))
        df["admit_date"] = day(15)
        assert case_day(apply(self.ID, hospital=df, people=ADULT), 1) == 15

    def test_near_miss(self):
        assert apply(self.ID, hospital=hospital((1, 0, "M82")), people=ADULT).empty

    def test_age_39(self):
        assert apply(self.ID, claims=claims((1, 0, "733")), people=people((1, "1975-06-01", "F"))).empty


class TestOsteoarthritis:
    ID = "ccdss.osteoarthritis"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd10ca == ("M15", "M16", "M17", "M18", "M19")
        assert (d.rule.window_days, d.rule.min_days_between, d.min_age) == (1825, 1, 20)

    def test_two_claims_1825_days(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "715"), (1, 1825, "715")), people=ADULT), 1) == 1825

    def test_1826_days(self):
        assert apply(self.ID, claims=claims((1, 0, "715"), (1, 1826, "715")), people=ADULT).empty

    def test_same_day(self):
        assert apply(self.ID, claims=claims((1, 0, "715"), (1, 0, "715.9")), people=ADULT).empty

    @pytest.mark.parametrize("code, hit", [("M15", True), ("M17.1", True), ("M19.9", True), ("M14", False), ("M20", False)])
    def test_icd10_hospital(self, code, hit):
        assert (not apply(self.ID, hospital=hospital((1, 0, code)), people=ADULT).empty) == hit


class TestGout:
    ID = "ccdss.gout"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("274", "712") and d.icd10ca == ("M10", "M11") and d.min_age == 20

    @pytest.mark.parametrize("code", ["274", "274.9", "712"])
    def test_claims(self, code):
        assert ids(apply(self.ID, claims=claims((1, 0, code), (1, 1, code)), people=ADULT)) == {1}

    def test_same_day_miss(self):
        assert apply(self.ID, claims=claims((1, 0, "274"), (1, 0, "274.1")), people=ADULT).empty

    def test_near_miss(self):
        assert apply(self.ID, hospital=hospital((1, 0, "M12")), people=ADULT).empty


class TestJia:
    ID = "ccdss.juvenile_idiopathic_arthritis"
    kid = people((1, "2010-01-01", "M"))

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.max_age == 15 and d.min_age is None and d.rule.min_days_between == 57
        assert d.icd10ca == ("M05", "M06", "M07.0", "M07.1", "M07.2", "M07.3", "M08", "M45")

    def test_claims_57_days_apart(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "714"), (1, 57, "720")), people=self.kid), 1) == 57

    def test_claims_56_days_apart(self):
        assert apply(self.ID, claims=claims((1, 0, "714"), (1, 56, "714")), people=self.kid).empty

    def test_m07_4_not_listed(self):
        assert apply(self.ID, hospital=hospital((1, 0, "M07.4")), people=self.kid).empty
        assert ids(apply(self.ID, hospital=hospital((1, 0, "M07.3")), people=self.kid)) == {1}

    def test_age_16(self):
        assert apply(self.ID, hospital=hospital((1, 0, "M08")), people=people((1, "1998-01-01", "M"))).empty


class TestRheumatoidArthritis:
    ID = "ccdss.rheumatoid_arthritis"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("714",) and d.icd10ca == ("M05", "M06") and d.min_age == 16
        assert d.rule.min_days_between == 57
        excl = d.exclusions[0]
        assert isinstance(excl, ClaimsExclusion)
        assert set(excl.icd9) == {"710", "446", "725", "696", "720", "713"}
        assert "L40.5" in excl.icd10ca and "M35.3" in excl.icd10ca

    def test_two_claims_over_8_weeks(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "714"), (1, 57, "714")), people=ADULT), 1) == 57

    def test_two_claims_exactly_8_weeks(self):
        assert apply(self.ID, claims=claims((1, 0, "714"), (1, 56, "714")), people=ADULT).empty

    def test_later_lupus_claims_exclude(self):
        cl = claims((1, 0, "714"), (1, 60, "714"), (1, 100, "710"), (1, 200, "710"))
        assert apply(self.ID, claims=cl, people=ADULT).empty

    def test_later_psoriatic_arthritis_icd10(self):
        cl = pd.concat([claims((1, 100, "L40.5"), (1, 101, "L40.5"))])
        res = apply(self.ID, claims=cl, hospital=hospital((1, 0, "M05.9")), people=ADULT, claims_coding="icd10ca")
        assert res.empty

    def test_one_later_claim_does_not_exclude(self):
        cl = claims((1, 0, "714"), (1, 60, "714"), (1, 100, "710"))
        assert ids(apply(self.ID, claims=cl, people=ADULT)) == {1}

    def test_age_15(self):
        assert apply(self.ID, hospital=hospital((1, 0, "M05")), people=people((1, "2000-06-01", "F"))).empty
