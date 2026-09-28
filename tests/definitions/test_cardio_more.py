import pandas as pd
import pytest

from casedefs import MissingFieldWarning, apply, get_definition

from ..conftest import case_day, claims, day, hospital, ids, people

ADULT = people((1, "1960-01-01", "M"))


class TestIschemicHeartDisease:
    ID = "ccdss.ischemic_heart_disease"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("410", "411", "412", "413", "414")
        assert d.icd10ca == ("I20", "I21", "I22", "I23", "I24", "I25")
        assert d.procedure_cci == ("1.IJ.50", "1.IJ.57.GQ", "1.IJ.54", "1.IJ.76")
        assert len(d.procedure_icd9cm) == 12 and len(d.procedure_ccp) == 10
        assert (d.rule.window_days, d.min_age) == (365, 20)

    @pytest.mark.parametrize("code", ["I20", "I21.4", "I25.10"])
    def test_hospital(self, code):
        assert ids(apply(self.ID, hospital=hospital((1, 0, code)), people=ADULT)) == {1}

    def test_near_miss_icd10(self):
        assert apply(self.ID, hospital=hospital((1, 0, "I26")), people=ADULT).empty

    def test_claims_365_vs_366(self):
        assert ids(apply(self.ID, claims=claims((1, 0, "414"), (1, 365, "414")), people=ADULT)) == {1}
        assert apply(self.ID, claims=claims((1, 0, "414"), (1, 366, "414")), people=ADULT).empty

    def test_procedure_path(self):
        procs = pd.DataFrame({"person_id": [1], "procedure_date": [day(9)], "proc_code": ["1.IJ.57.GQ-AZ"]})
        assert case_day(apply(self.ID, procedures=procs, people=ADULT), 1) == 9

    def test_other_cci_rubric(self):
        procs = pd.DataFrame({"person_id": [1], "procedure_date": [day(9)], "proc_code": ["1.IJ.57.LA"]})
        assert apply(self.ID, procedures=procs, people=ADULT).empty


class TestAmi:
    ID = "ccdss.ami"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.icd9 == ("410",) and d.icd10ca == ("I21", "I22")
        assert d.rule.min_claims is None and d.hospital_date == "admission"
        assert set(d.hospital_dx_types) == {"M", "W", "X", "Y", "1", "2"}

    def test_mrdx(self):
        df = hospital((1, 20, "I21.0"))
        df["dx_type_1"], df["admit_date"] = "M", day(12)
        assert case_day(apply(self.ID, hospital=df, people=ADULT), 1) == 12

    def test_type_3_does_not_count(self):
        df = hospital((1, 20, "J18", "I21.0"))
        df["dx_type_1"], df["dx_type_2"], df["admit_date"] = "M", "3", day(12)
        assert apply(self.ID, hospital=df, people=ADULT).empty

    def test_claims_do_not_count(self):
        assert apply(self.ID, claims=claims((1, 0, "410"), (1, 10, "410")), people=ADULT).empty

    def test_old_mi_i25_2_not_ami(self):
        df = hospital((1, 20, "I25.2"))
        df["dx_type_1"], df["admit_date"] = "M", day(12)
        assert apply(self.ID, hospital=df, people=ADULT).empty

    def test_warns_without_types(self):
        with pytest.warns(MissingFieldWarning):
            apply(self.ID, hospital=hospital((1, 0, "I21")), people=ADULT)


class TestStroke:
    ID = "ccdss.stroke"

    def test_metadata(self):
        d = get_definition(self.ID)
        assert d.excluded_codes == ("G45.4",)
        assert "433.01" in d.icd9 and "433.91" in d.icd9 and "362.3" in d.icd9
        assert d.claims_codes[0] == ("325", "430", "431", "432.9", "434", "435", "436", "437.6")
        assert (d.rule.window_days, d.min_age) == (365, 20)

    @pytest.mark.parametrize("code", ["G08", "G45.0", "G45.9", "H34.1", "I61.9", "I62.9", "I63.5", "I64", "I67.6"])
    def test_icd10_hits(self, code):
        assert ids(apply(self.ID, hospital=hospital((1, 0, code)), people=ADULT)) == {1}

    @pytest.mark.parametrize("code", ["G45.4", "H34.2", "I62.0", "I65", "I67.5"])
    def test_icd10_near_misses(self, code):
        assert apply(self.ID, hospital=hospital((1, 0, code)), people=ADULT).empty

    @pytest.mark.parametrize("code, hit", [("433.11", True), ("433.10", False), ("362.34", True), ("432.1", False)])
    def test_hospital_icd9(self, code, hit):
        res = apply(self.ID, hospital=hospital((1, 0, code)), people=ADULT, hospital_coding="icd9")
        assert (not res.empty) == hit

    def test_claims_433_does_not_count(self):
        assert apply(self.ID, claims=claims((1, 0, "433"), (1, 10, "433")), people=ADULT).empty

    def test_claims_two_within_a_year(self):
        assert case_day(apply(self.ID, claims=claims((1, 0, "436"), (1, 100, "436")), people=ADULT), 1) == 100
