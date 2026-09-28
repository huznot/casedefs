import pytest

from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people


class TestSchizophrenia:
    ID = "ccdss.schizophrenia"
    pp = people((1, "1990-01-01", "M"))

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("295",) and d.icd10ca == ("F20", "F21", "F23", "F25")
        assert (d.rule.window_days, d.rule.min_days_between, d.min_age) == (730, 30, 10)
        assert "misclassify" in d.notes

    def test_claims_30_days(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "295"), (1, 30, "295")), people=self.pp), 1) == 30

    def test_claims_29_days(self):
        assert apply(self.ID, claims=claims((1, 0, "295"), (1, 29, "295")), people=self.pp).empty

    @pytest.mark.parametrize("code, hit", [("F20.0", True), ("F25", True), ("F22", False), ("F24", False)])
    def test_hospital_codes(self, code, hit):
        assert (not apply(self.ID, hospital=hospital((1, 0, code)), people=self.pp).empty) == hit

    def test_age_9(self):
        assert apply(self.ID, hospital=hospital((1, 0, "F20")), people=people((1, "2006-01-02", "M"))).empty


class TestAutism:
    ID = "ccdss.autism"
    kid = people((1, "2010-01-01", "F"))

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("299",) and d.icd10ca == ("F84",)
        assert (d.min_age, d.max_age, d.rule.window_days) == (1, 19, None)

    def test_two_claims_far_apart(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "299"), (1, 2000, "299")), people=self.kid), 1) == 2000

    def test_one_claim(self):
        assert apply(self.ID, claims=claims((1, 0, "299")), people=self.kid).empty

    def test_hospital(self):
        assert ids(apply(self.ID, hospital=hospital((1, 0, "F84.0")), people=self.kid)) == {1}

    def test_adult_is_not_a_case(self):
        assert apply(self.ID, hospital=hospital((1, 0, "F84")), people=people((1, "1990-01-01", "F"))).empty

    def test_near_miss(self):
        assert apply(self.ID, hospital=hospital((1, 0, "F83")), people=self.kid).empty
