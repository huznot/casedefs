import warnings

import pandas as pd
import pytest

from casedefs import IncompleteDefinitionWarning, MissingFieldWarning, apply, get_definition

from ..conftest import case_day, claims, day, hospital, ids


def amb(*rows, dx_type=None):
    df = pd.DataFrame([{"person_id": p, "visit_date": day(d), "dx_code_1": c} for p, d, c in rows])
    if dx_type is not None:
        df["dx_type_1"] = dx_type
    return df


def quiet(**kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return apply(**kw)


def test_sample_codes_match_the_table():
    assert get_definition("tonelli.hypertension").icd10ca == ("I10", "I11", "I12", "I13", "I15")
    assert get_definition("tonelli.dementia").icd9 == ("290", "2941", "3312")
    assert get_definition("tonelli.chronic_pulmonary_disease").icd9[:5] == ("4168", "4169", "490", "491", "492")
    assert "J45" not in get_definition("tonelli.chronic_pulmonary_disease").icd10ca
    assert get_definition("tonelli.hepatitis_b").icd9 == ("0702", "0703")
    assert get_definition("tonelli.stroke_tia").icd10ca == ("G450", "G451", "G452", "G453", "G458", "G459",
                                                             "H341", "I60", "I61", "I63", "I64")
    assert {"G890", "G892", "G894"} <= set(get_definition("tonelli.chronic_pain").icd10ca)


class TestAsthma:
    def test_three_ambulatory_within_two_years(self):
        res = apply("tonelli.asthma", ambulatory=amb((1, 0, "J45"), (1, 300, "J45.9"), (1, 730, "J45")))
        assert case_day(res, 1) == 730

    def test_two_ambulatory_not_enough(self):
        assert apply("tonelli.asthma", ambulatory=amb((1, 0, "J45"), (1, 30, "J45"))).empty

    def test_claims_not_used(self):
        assert apply("tonelli.asthma", claims=claims((1, 0, "493"), (1, 5, "493"), (1, 9, "493"))).empty


class TestInflammatoryBowelDisease:
    def cl(self, specialty):
        df = claims((1, 0, "555"), (1, 400, "555"))
        df["specialty"] = specialty
        return df

    def test_gastro_claims(self):
        assert case_day(apply("tonelli.inflammatory_bowel_disease", claims=self.cl("GAST")), 1) == 400

    def test_other_specialty_does_not_count(self):
        assert apply("tonelli.inflammatory_bowel_disease", claims=self.cl("DERM")).empty

    def test_no_specialty_warns(self):
        with pytest.warns(MissingFieldWarning, match="specialty"):
            res = apply("tonelli.inflammatory_bowel_disease", claims=claims((1, 0, "555"), (1, 400, "555")))
        assert ids(res) == {1}

    def test_two_hospitalizations_within_three_years(self):
        assert ids(apply("tonelli.inflammatory_bowel_disease", hospital=hospital((1, 0, "K50"), (1, 1095, "K51")))) == {1}
        assert apply("tonelli.inflammatory_bowel_disease", hospital=hospital((1, 0, "K50"), (1, 1096, "K51"))).empty


class TestCirrhosis:
    def test_needs_both_parts(self):
        assert apply("tonelli.cirrhosis", hospital=hospital((1, 0, "K74.6"))).empty
        res = apply("tonelli.cirrhosis", hospital=hospital((1, 0, "K74.6")), claims=claims((1, 90, "789.5")))
        assert case_day(res, 1) == 90

    def test_excluded_decompensation_codes(self):
        cl = claims((1, 90, "789.51"), (1, 91, "567.22"))
        assert apply("tonelli.cirrhosis", hospital=hospital((1, 0, "K74.6")), claims=cl).empty

    def test_ambulatory_counts(self):
        res = apply("tonelli.cirrhosis", ambulatory=amb((1, 5, "K70.3"), (1, 50, "R18")))
        assert case_day(res, 1) == 50


def test_hepatitis_b_window():
    assert ids(apply("tonelli.hepatitis_b", hospital=hospital((1, 0, "B18.1"), (1, 183, "B18.1")))) == {1}
    assert apply("tonelli.hepatitis_b", hospital=hospital((1, 0, "B18.1"), (1, 184, "B18.1"))).empty
    assert apply("tonelli.hepatitis_b", hospital=hospital((1, 0, "B18.1"))).empty


def test_chronic_pain_gap():
    assert case_day(apply("tonelli.chronic_pain", claims=claims((1, 0, "724.2"), (1, 30, "724.2"))), 1) == 30
    assert apply("tonelli.chronic_pain", claims=claims((1, 0, "724.2"), (1, 29, "724.2"))).empty


def test_atrial_fibrillation_claims_use_427_3():
    assert ids(apply("tonelli.atrial_fibrillation", claims=claims((1, 0, "427.3"), (1, 10, "427.3")))) == {1}
    assert apply("tonelli.atrial_fibrillation", hospital=hospital((1, 0, "427.32")), hospital_coding="icd9").empty
    assert ids(apply("tonelli.atrial_fibrillation", hospital=hospital((1, 0, "427.31")), hospital_coding="icd9")) == {1}


class TestDxTypes:
    def typed(self, code, dx_type):
        df = hospital((1, 0, code))
        df["dx_type_1"] = dx_type
        return df

    def test_mi_most_responsible_only(self):
        assert ids(apply("tonelli.myocardial_infarction", hospital=self.typed("I21.0", "M"))) == {1}
        assert apply("tonelli.myocardial_infarction", hospital=self.typed("I21.0", "3")).empty

    def test_stroke_post_admission_counts(self):
        assert ids(apply("tonelli.stroke_tia", hospital=self.typed("I63.9", "2"))) == {1}
        assert apply("tonelli.stroke_tia", hospital=self.typed("I63.9", "1")).empty

    def test_epilepsy_ambulatory_most_responsible(self):
        assert ids(apply("tonelli.epilepsy", ambulatory=amb((1, 0, "G40.9"), dx_type="M"))) == {1}
        assert apply("tonelli.epilepsy", ambulatory=amb((1, 0, "G40.9"), dx_type="3")).empty


def test_psoriasis_dermatologist_claim():
    df = claims((1, 3, "696.1"), (2, 3, "696.1"))
    df["specialty"] = ["DERM", "GP"]
    assert ids(apply("tonelli.psoriasis", claims=df)) == {1}


class TestIncomplete:
    def test_ckd_warns(self):
        with pytest.warns(IncompleteDefinitionWarning, match="tonelli.chronic_kidney_disease"):
            res = apply("tonelli.chronic_kidney_disease", claims=claims((1, 0, "585"), (1, 100, "585"), (1, 200, "585")))
        assert case_day(res, 1) == 200

    def test_ibs_person_exclusion(self):
        res = quiet(definition="tonelli.irritable_bowel_syndrome",
                    claims=claims((1, 0, "564.1"), (1, 10, "564.1"), (2, 0, "564.1"), (2, 10, "564.1"), (2, 900, "555")))
        assert ids(res) == {1}

    def test_constipation_exclusion_from_hospital(self):
        res = quiet(definition="tonelli.severe_constipation",
                    claims=claims((1, 0, "564.0"), (1, 10, "564.0")), hospital=hospital((1, 500, "C18.2")))
        assert res.empty
