import pandas as pd
import pytest

from casedefs import CasedefsInputError, comorbidity_score, get_definition
from casedefs.definitions.quan import charlson, elixhauser

from .quan_sas_codes import SAS_ICD10


@pytest.mark.parametrize("key", list(SAS_ICD10))
def test_charlson_icd10_matches_quan_sas_code(key):
    ours = get_definition(f"quan.charlson.{key}").icd10ca
    assert set(ours) == set(SAS_ICD10[key])


def test_weights_cover_every_condition():
    keys = {d.id.rsplit(".", 1)[1] for d in charlson.DEFINITIONS}
    assert set(charlson.WEIGHTS) == keys
    assert sorted(charlson.WEIGHTS.values()) == [1] * 10 + [2] * 4 + [3] + [6] * 2


def test_counts():
    assert len(charlson.DEFINITIONS) == 17 and len(elixhauser.DEFINITIONS) == 31


@pytest.mark.parametrize("def_id, code, hit", [
    ("quan.charlson.any_malignancy", "C44.9", False),  # skin excluded
    ("quan.charlson.any_malignancy", "C43.9", True),
    ("quan.charlson.any_malignancy", "C77.0", False),  # metastatic is its own group
    ("quan.charlson.renal_disease", "N03.1", False),
    ("quan.charlson.renal_disease", "N03.2", True),
    ("quan.elixhauser.cardiac_arrhythmias", "R00.0", True),
    ("quan.elixhauser.cardiac_arrhythmias", "R00.2", False),
    ("quan.elixhauser.valvular_disease", "Q23.3", True),
    ("quan.elixhauser.valvular_disease", "Q23.4", False),
    ("quan.elixhauser.renal_failure", "Z99.2", True),
    ("quan.elixhauser.other_neurological_disorders", "G13.1", True),
    ("quan.elixhauser.congestive_heart_failure", "I42.5", True),
    ("quan.elixhauser.coagulopathy", "D69.2", False),
])
def test_print_error_codes_and_edges(def_id, code, hit):
    from casedefs import apply
    hosp = pd.DataFrame({"person_id": [1], "separation_date": ["2020-01-01"], "dx_code_1": [code]})
    assert (not apply(def_id, hospital=hosp).empty) == hit


@pytest.mark.parametrize("def_id, code, hit", [
    ("quan.charlson.any_malignancy", "195.8", True),
    ("quan.charlson.any_malignancy", "195.9", False),
    ("quan.charlson.moderate_or_severe_liver_disease", "456.21", True),
    ("quan.charlson.moderate_or_severe_liver_disease", "456.3", False),
    ("quan.charlson.cerebrovascular_disease", "362.34", True),
    ("quan.charlson.cerebrovascular_disease", "362.35", False),
    ("quan.elixhauser.cardiac_arrhythmias", "426.11", False),
    ("quan.elixhauser.cardiac_arrhythmias", "426.12", True),
])
def test_icd9_edges(def_id, code, hit):
    from casedefs import apply
    hosp = pd.DataFrame({"person_id": [1], "separation_date": ["2020-01-01"], "dx_code_1": [code]})
    assert (not apply(def_id, hospital=hosp, hospital_coding="icd9").empty) == hit


def hosp(*rows):
    return pd.DataFrame(
        [{"person_id": p, "separation_date": d, "dx_code_1": c1, "dx_code_2": c2} for p, d, c1, c2 in rows]
    )


class TestScores:
    data = hosp(
        (1, "2020-01-01", "I21.4", "E11.2"),
        (1, "2020-06-01", "C78.0", None),
        (2, "2020-01-01", "E11.9", None),
        (3, "2020-01-01", "J44.9", "I10"),
    )

    def test_charlson(self):
        out = comorbidity_score("charlson", hospital=self.data).set_index("person_id")
        assert out.loc[1, "score"] == 1 + 2 + 6
        assert out.loc[2, "score"] == 1
        assert out.loc[3, "chronic_pulmonary_disease"] == 1 and out.loc[3, "score"] == 1

    def test_elixhauser_is_a_count(self):
        out = comorbidity_score("elixhauser", hospital=self.data).set_index("person_id")
        assert out.loc[1, "score"] == 2  # diabetes complicated, metastatic cancer
        assert out.loc[3, "score"] == 2  # chronic pulmonary, hypertension uncomplicated

    def test_index_dates_and_lookback(self):
        idx = pd.DataFrame({"person_id": [1, 2, 9], "index_date": ["2020-03-01", "2019-06-01", "2020-01-01"]})
        out = comorbidity_score("charlson", hospital=self.data, index_dates=idx).set_index("person_id")
        assert out.loc[1, "score"] == 3  # the metastatic record is after the index date
        assert out.loc[2, "score"] == 0
        assert out.loc[9, "score"] == 0  # everyone in index_dates gets a row
        out = comorbidity_score("charlson", hospital=self.data, index_dates=idx, lookback_days=30)
        assert out.set_index("person_id").loc[1, "score"] == 0

    def test_claims_need_opt_in(self):
        cl = pd.DataFrame({"person_id": [5], "service_date": ["2020-01-01"], "dx_code": ["428"]})
        with pytest.raises(CasedefsInputError, match="include_claims"):
            comorbidity_score("charlson", claims=cl)
        out = comorbidity_score("charlson", claims=cl, include_claims=True)
        assert out.loc[0, "congestive_heart_failure"] == 1

    def test_bad_inputs(self):
        with pytest.raises(CasedefsInputError, match="index must be"):
            comorbidity_score("apache", hospital=self.data)
        with pytest.raises(CasedefsInputError, match="pass hospital"):
            comorbidity_score("charlson")
        idx = pd.DataFrame({"person_id": [1, 1], "index_date": ["2020-01-01", "2020-02-01"]})
        with pytest.raises(CasedefsInputError, match="one row per person"):
            comorbidity_score("charlson", hospital=self.data, index_dates=idx)
