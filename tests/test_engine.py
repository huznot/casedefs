"""rule engine tests using a made-up definition, so they do not depend on ccdss."""

import warnings

import pandas as pd
import pytest

from casedefs import Definition, Exclusion, MissingPeopleWarning, Rule, UnverifiedDefinitionWarning, apply
from casedefs.engine import age_on

from .conftest import case_day, claims, hospital, ids, people


def make(rule=Rule(1, 2, 730), min_age=None, max_age=None, exclusions=(), verified=True):
    return Definition(
        id="test.fake",
        name="fake condition",
        version="t1",
        source_title="test",
        source_url="https://example.org",
        source_location="n/a",
        verified=verified,
        icd9=("999",),
        icd10ca=("X99",),
        rule=rule,
        min_age=min_age,
        max_age=max_age,
        exclusions=exclusions,
    )


FAKE = make()


class TestClaimsWindow:
    def test_two_claims_exactly_at_window(self):
        res = apply(FAKE, claims=claims((1, 0, "999"), (1, 730, "999")))
        assert ids(res) == {1}
        assert case_day(res, 1) == 730

    def test_two_claims_one_day_past_window(self):
        res = apply(FAKE, claims=claims((1, 0, "999"), (1, 731, "999")))
        assert res.empty

    def test_single_claim_is_not_enough(self):
        assert apply(FAKE, claims=claims((1, 0, "999"))).empty

    def test_later_pair_qualifies_after_early_miss(self):
        res = apply(FAKE, claims=claims((1, 0, "999"), (1, 800, "999"), (1, 900, "999")))
        assert case_day(res, 1) == 900

    def test_same_day_duplicate_rows_count_once(self):
        assert apply(FAKE, claims=claims((1, 0, "999"), (1, 0, "999"))).empty

    def test_same_day_different_codes_count_as_two_claims(self):
        res = apply(FAKE, claims=claims((1, 0, "999"), (1, 0, "999.1")))
        assert case_day(res, 1) == 0

    def test_claims_of_other_people_do_not_combine(self):
        assert apply(FAKE, claims=claims((1, 0, "999"), (2, 10, "999"))).empty

    def test_non_matching_codes_ignored(self):
        assert apply(FAKE, claims=claims((1, 0, "998"), (1, 10, "998"))).empty

    def test_three_claims_rule(self):
        rule3 = make(Rule(None, 3, 30))
        yes = claims((1, 0, "999"), (1, 15, "999"), (1, 30, "999"))
        no = claims((2, 0, "999"), (2, 15, "999"), (2, 31, "999"))
        res = apply(rule3, claims=pd.concat([yes, no]))
        assert ids(res) == {1}
        assert case_day(res, 1) == 30

    def test_no_window_means_any_time(self):
        res = apply(make(Rule(None, 2, None)), claims=claims((1, 0, "999"), (1, 5000, "999")))
        assert case_day(res, 1) == 5000

    def test_single_claim_rule(self):
        res = apply(make(Rule(1, 1, None)), claims=claims((1, 20, "999"), (1, 40, "999")))
        assert case_day(res, 1) == 20


class TestHospital:
    def test_one_hospital_record_is_enough(self):
        res = apply(FAKE, hospital=hospital((1, 5, "A00", "X99.1")))
        assert case_day(res, 1) == 5

    def test_hospital_path_can_be_switched_off(self):
        assert apply(make(Rule(None, 2, 730)), hospital=hospital((1, 5, "X99"))).empty

    def test_two_codes_on_one_stay_are_one_record(self):
        res = apply(make(Rule(2, None, None)), hospital=hospital((1, 5, "X99", "X991")))
        assert res.empty

    def test_two_stays_needed(self):
        res = apply(make(Rule(2, None, None)), hospital=hospital((1, 5, "X99"), (1, 50, "X99")))
        assert case_day(res, 1) == 50

    def test_earliest_path_wins(self):
        res = apply(
            FAKE,
            claims=claims((1, 0, "999"), (1, 100, "999")),
            hospital=hospital((1, 60, "X99")),
        )
        assert case_day(res, 1) == 60

    def test_icd9_in_hospital_needs_coding_flag(self):
        hosp = hospital((1, 5, "999"))
        assert apply(FAKE, hospital=hosp).empty
        assert case_day(apply(FAKE, hospital=hosp, hospital_coding="icd9"), 1) == 5
        assert case_day(apply(FAKE, hospital=hosp, hospital_coding="both"), 1) == 5

    def test_per_row_icd_version_column(self):
        hosp = hospital((1, 5, "999"), (2, 5, "999"))
        hosp["icd_version"] = [9, 10]
        assert ids(apply(FAKE, hospital=hosp)) == {1}

    def test_icd10_codes_in_claims(self):
        cl = claims((1, 0, "X99"), (1, 10, "X99"))
        assert apply(FAKE, claims=cl).empty
        assert ids(apply(FAKE, claims=cl, claims_coding="icd10ca")) == {1}


class TestAge:
    def test_age_boundary(self):
        adult = make(min_age=20)
        pp = people((1, "1995-01-01", "F"), (2, "1995-01-02", "F"))
        # base date 2015-01-01: person 1 turns 20 that day, person 2 is still 19
        res = apply(adult, hospital=hospital((1, 0, "X99"), (2, 0, "X99")), people=pp)
        assert ids(res) == {1}

    def test_under_age_record_skipped_later_one_counts(self):
        adult = make(min_age=20)
        pp = people((1, "1995-06-01", "M"))
        res = apply(adult, hospital=hospital((1, 0, "X99"), (1, 200, "X99")), people=pp)
        assert case_day(res, 1) == 200

    def test_max_age(self):
        young = make(min_age=None, max_age=18)
        pp = people((1, "1990-01-01", "M"), (2, "2005-01-01", "M"))
        assert ids(apply(young, hospital=hospital((1, 0, "X99"), (2, 0, "X99")), people=pp)) == {2}

    def test_missing_people_table_warns_and_skips_age(self):
        with pytest.warns(MissingPeopleWarning):
            res = apply(make(min_age=20), hospital=hospital((1, 0, "X99")))
        assert ids(res) == {1}

    def test_unknown_birth_date_is_left_out_with_warning(self):
        pp = people((1, None, "M"), (2, "1970-01-01", "M"))
        with pytest.warns(MissingPeopleWarning, match="1 person"):
            res = apply(make(min_age=20), hospital=hospital((1, 0, "X99"), (2, 0, "X99")), people=pp)
        assert ids(res) == {2}

    def test_no_age_limit_needs_no_people(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            apply(FAKE, hospital=hospital((1, 0, "X99")))

    def test_age_on(self):
        birth = pd.to_datetime(pd.Series(["2000-02-29", "2000-06-15", None]))
        when = pd.to_datetime(pd.Series(["2001-02-28", "2010-06-15", "2010-01-01"]))
        out = age_on(birth, when)
        assert out.iloc[0] == 0
        assert out.iloc[1] == 10
        assert pd.isna(out.iloc[2])


PREG = Exclusion(
    name="pregnancy", icd9=("V27",), icd10ca=("O24",), days_before=120, days_after=180,
    sex="F", min_age=10, max_age=54,
)


class TestExclusion:
    def setup_method(self):
        self.defn = make(exclusions=(PREG,))

    def run(self, cl, hosp, sex="F", birth="1985-01-01"):
        return apply(self.defn, claims=cl, hospital=hosp, people=people((1, birth, sex)))

    @pytest.mark.parametrize("offset, excluded", [(-121, False), (-120, True), (0, True), (180, True), (181, False)])
    def test_window_edges(self, offset, excluded):
        # case date is day 500 from the second claim; the pregnancy stay moves around it
        cl = claims((1, 400, "999"), (1, 500, "999"))
        hosp = hospital((1, 500 - offset, "O24.4"))
        res = self.run(cl, hosp)
        assert res.empty == excluded

    def test_later_qualifying_date_outside_window_counts(self):
        cl = claims((1, 400, "999"), (1, 500, "999"), (1, 700, "999"))
        res = self.run(cl, hospital((1, 450, "O244")))
        assert case_day(res, 1) == 700

    def test_male_not_excluded(self):
        res = self.run(claims((1, 0, "999"), (1, 10, "999")), hospital((1, 10, "O24")), sex="M")
        assert ids(res) == {1}

    def test_unknown_sex_is_excluded(self):
        res = self.run(claims((1, 0, "999"), (1, 10, "999")), hospital((1, 10, "O24")), sex=None)
        assert res.empty

    def test_outside_age_band_not_excluded(self):
        res = self.run(claims((1, 0, "999"), (1, 10, "999")), hospital((1, 10, "O24")), birth="1950-01-01")
        assert ids(res) == {1}

    def test_exclusion_applies_without_people_table(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = apply(self.defn, claims=claims((1, 0, "999"), (1, 10, "999")), hospital=hospital((1, 10, "O24")))
        assert res.empty

    def test_icd9_exclusion_code_in_hospital(self):
        res = apply(
            self.defn,
            claims=claims((1, 0, "999"), (1, 10, "999")),
            hospital=hospital((1, 10, "V27.0")),
            hospital_coding="icd9",
            people=people((1, "1985-01-01", "F")),
        )
        assert res.empty

    def test_exclusion_on_the_same_stay_as_the_diagnosis(self):
        res = self.run(None, hospital((1, 10, "X99", "O24")))
        assert res.empty


def test_unverified_definition_warns():
    with pytest.warns(UnverifiedDefinitionWarning):
        apply(make(verified=False), hospital=hospital((1, 0, "X99")))


def test_output_shape_and_order():
    res = apply(FAKE, hospital=hospital((2, 5, "X99"), (1, 9, "X99"), (3, 5, "X99")))
    assert list(res.columns) == ["person_id", "case_date", "definition_id", "definition_version"]
    assert list(res["person_id"]) == [2, 3, 1]
    assert set(res["definition_id"]) == {"test.fake"}
    assert set(res["definition_version"]) == {"t1"}
    assert pd.api.types.is_datetime64_any_dtype(res["case_date"])


def test_no_cases_returns_empty_frame_with_columns():
    res = apply(FAKE, claims=claims((1, 0, "123")))
    assert res.empty
    assert list(res.columns) == ["person_id", "case_date", "definition_id", "definition_version"]
