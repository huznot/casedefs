"""tests for claim gaps, split code lists, dx types, procedures, drugs and composites."""

import pandas as pd
import pytest

from casedefs import (
    CasedefsInputError, ClaimsExclusion, Composite, Definition, MissingFieldWarning, MissingPeopleWarning,
    Rule, apply,
)
from casedefs.engine import chain_ends

from .conftest import BASE, case_day, claims, day, hospital, ids, people


def make(rule, **kw):
    base = dict(
        id="test.fake", name="fake", version="t1", source_title="t", source_url="https://example.org",
        source_location="n/a", verified=True, icd9=("999",), icd10ca=("X99",), rule=rule,
    )
    base.update(kw)
    return Definition(**base)


def dates(*offsets):
    return pd.DataFrame({"person_id": 1, "date": [BASE + pd.Timedelta(days=d) for d in offsets]})


class TestChainEnds:
    def ends(self, offsets, n, window, gap):
        out = chain_ends(dates(*offsets), "person_id", n, window, gap)
        return sorted((d - BASE).days for d in out["date"])

    def test_gap_exactly_met(self):
        assert self.ends([0, 30], 2, 730, 30) == [30]

    def test_gap_one_short(self):
        assert self.ends([0, 29], 2, 730, 30) == []

    def test_gap_skips_a_close_claim(self):
        # 0 and 10 are too close, but 0 and 40 work, and so do 10 and 40
        assert self.ends([0, 10, 40], 2, 730, 30) == [40]

    def test_three_claims_each_gap(self):
        assert self.ends([0, 30, 60], 3, 730, 30) == [60]
        assert self.ends([0, 30, 59], 3, 730, 30) == []

    def test_three_claims_window_uses_latest_start(self):
        # chain 10, 40, 740 fits in 730 days; a chain starting at 0 would not
        assert self.ends([0, 10, 40, 740], 3, 730, 30) == [740]

    def test_three_claims_window_too_wide(self):
        assert self.ends([0, 30, 731], 3, 730, 30) == []

    def test_same_day_claims_do_not_satisfy_a_one_day_gap(self):
        assert self.ends([5, 5], 2, 1825, 1) == []
        assert self.ends([5, 6], 2, 1825, 1) == [6]

    def test_people_do_not_mix(self):
        df = pd.DataFrame({"person_id": [1, 2], "date": [BASE, BASE + pd.Timedelta(days=40)]})
        assert chain_ends(df, "person_id", 2, 730, 30).empty

    def test_empty(self):
        assert chain_ends(dates(), "person_id", 2, 730, 30).empty


class TestSplitCodes:
    defn = make(Rule(1, 2, 730), icd9=("999.1",), claims_icd9=("999",))

    def test_claims_use_their_own_list(self):
        assert ids(apply(self.defn, claims=claims((1, 0, "999.5"), (1, 10, "999.5")))) == {1}

    def test_hospital_uses_hospital_list(self):
        assert apply(self.defn, hospital=hospital((1, 0, "999.5")), hospital_coding="icd9").empty
        assert ids(apply(self.defn, hospital=hospital((1, 0, "999.1")), hospital_coding="icd9")) == {1}

    def test_hospital_only_definition_ignores_claims(self):
        d = make(Rule(1, None), icd9=(), icd10ca=("X99",))
        assert apply(d, claims=claims((1, 0, "X99"), (1, 5, "X99")), claims_coding="icd10ca").empty

    def test_claims_only_definition_ignores_hospital(self):
        d = make(Rule(None, 1), icd9=(), icd10ca=(), claims_icd9=("999",))
        assert apply(d, hospital=hospital((1, 0, "999")), hospital_coding="icd9").empty


def test_excluded_codes():
    d = make(Rule(1, None), icd10ca=("X99",), excluded_codes=("X99.4",))
    res = apply(d, hospital=hospital((1, 0, "X99.4"), (2, 0, "X99.3"), (3, 0, "X994")))
    assert ids(res) == {2}


class TestHospitalMinAge:
    defn = make(Rule(1, 3, 730, min_days_between=30, hospital_min_age=20), min_age=1)

    def test_child_hospital_record_does_not_count(self):
        assert apply(self.defn, hospital=hospital((1, 0, "X99")), people=people((1, "2005-01-01", "F"))).empty

    def test_child_claims_count(self):
        res = apply(
            self.defn,
            claims=claims((1, 0, "999"), (1, 30, "999"), (1, 60, "999")),
            people=people((1, "2005-01-01", "F")),
        )
        assert case_day(res, 1) == 60

    def test_adult_hospital_record_counts(self):
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), people=people((1, "1990-01-01", "F")))
        assert case_day(res, 1) == 0

    def test_without_people_hospital_counts_and_warns(self):
        with pytest.warns(MissingPeopleWarning):
            res = apply(self.defn, hospital=hospital((1, 0, "X99")))
        assert ids(res) == {1}


class TestDxTypes:
    defn = make(Rule(1, None), hospital_dx_types=("M", "1"))

    def wide(self, types):
        df = hospital((1, 0, "A00", "X99"))
        df["dx_type_1"], df["dx_type_2"] = types
        return df

    def test_type_allowed(self):
        assert ids(apply(self.defn, hospital=self.wide(["M", "1"]))) == {1}

    def test_type_not_allowed(self):
        assert apply(self.defn, hospital=self.wide(["M", "3"])).empty

    def test_mrdx_spelling(self):
        df = hospital((1, 0, "X99"))
        df["dx_type_1"] = "MRDx"
        assert ids(apply(self.defn, hospital=df)) == {1}

    def test_long_format_dx_type(self):
        df = pd.DataFrame({"person_id": [1, 2], "date": [day(0), day(0)], "dx_code": ["X99", "X99"],
                           "dx_type": ["1", "3"]})
        assert ids(apply(self.defn, hospital=df)) == {1}

    def test_custom_type_columns(self):
        df = pd.DataFrame({"person_id": [1], "date": [day(0)], "D1": ["A00"], "D2": ["X99"], "T1": ["M"], "T2": ["9"]})
        cols = {"hospital_dx_columns": ["D1", "D2"], "hospital_dx_type_columns": ["T1", "T2"]}
        assert apply(self.defn, hospital=df, columns=cols).empty

    def test_type_columns_must_line_up(self):
        df = pd.DataFrame({"person_id": [1], "date": [day(0)], "D1": ["X99"], "T1": ["M"], "T2": ["1"]})
        with pytest.raises(CasedefsInputError, match="line up"):
            apply(self.defn, hospital=df, columns={"hospital_dx_columns": ["D1"], "hospital_dx_type_columns": ["T1", "T2"]})

    def test_missing_types_warn_and_use_all_fields(self):
        with pytest.warns(MissingFieldWarning, match="dx_type"):
            res = apply(self.defn, hospital=hospital((1, 0, "A00", "X99")))
        assert ids(res) == {1}


class TestAdmissionDate:
    defn = make(Rule(1, None), hospital_date="admission")

    def test_uses_admit_date(self):
        df = hospital((1, 20, "X99"))
        df["admit_date"] = day(5)
        assert case_day(apply(self.defn, hospital=df), 1) == 5

    def test_blank_admit_date_falls_back(self):
        df = hospital((1, 20, "X99"), (2, 20, "X99"))
        df["admit_date"] = [day(5), None]
        res = apply(self.defn, hospital=df)
        assert case_day(res, 1) == 5 and case_day(res, 2) == 20

    def test_admit_only_table(self):
        df = pd.DataFrame({"person_id": [1], "admit_date": [day(3)], "dx_code_1": ["X99"]})
        assert case_day(apply(self.defn, hospital=df), 1) == 3

    def test_warns_without_admit_date(self):
        with pytest.warns(MissingFieldWarning, match="admission"):
            apply(self.defn, hospital=hospital((1, 20, "X99")))

    def test_separation_definitions_ignore_admit_date(self):
        df = hospital((1, 20, "X99"))
        df["admit_date"] = day(5)
        assert case_day(apply(make(Rule(1, None)), hospital=df), 1) == 20


class TestProcedures:
    defn = make(Rule(None, None, min_procedures=1), icd9=(), icd10ca=(),
                procedure_cci=("1.IJ.50",), procedure_ccp=("48.02",), procedure_icd9cm=("36.01",))

    def procs(self, *rows, **extra):
        df = pd.DataFrame([{"person_id": p, "procedure_date": day(d), "proc_code": c} for p, d, c in rows])
        for k, v in extra.items():
            df[k] = v
        return df

    def test_cci_prefix(self):
        assert case_day(apply(self.defn, procedures=self.procs((1, 7, "1.IJ.50.GQ-AZ"))), 1) == 7

    def test_systems_do_not_mix(self):
        # 48.02 is a CCP code; read as CCI it should not match
        assert apply(self.defn, procedures=self.procs((1, 0, "48.02"))).empty
        assert ids(apply(self.defn, procedures=self.procs((1, 0, "48.02")), procedure_coding="ccp")) == {1}

    def test_per_row_system(self):
        df = self.procs((1, 0, "36.01"), (2, 0, "36.01"), proc_system=["icd9cm", "ccp"])
        assert ids(apply(self.defn, procedures=df)) == {1}

    def test_wide_procedures(self):
        df = pd.DataFrame({"person_id": [1], "date": [day(0)], "proc_code_1": ["1.AA.00"], "proc_code_2": ["1.IJ.50"]})
        assert ids(apply(self.defn, procedures=df)) == {1}

    def test_bad_system(self):
        with pytest.raises(CasedefsInputError, match="proc_system"):
            apply(self.defn, procedures=self.procs((1, 0, "x"), proc_system=["snomed"]))
        with pytest.raises(CasedefsInputError, match="coding must be one of"):
            apply(self.defn, procedures=self.procs((1, 0, "x")), procedure_coding="snomed")

    def test_missing_code_column(self):
        with pytest.raises(CasedefsInputError, match="proc_code"):
            apply(self.defn, procedures=pd.DataFrame({"person_id": [1], "date": [day(0)]}))


class TestDrugs:
    defn = make(Rule(None, None, min_drugs=1), icd9=(), icd10ca=(), drug_dins=("02232043",))

    def test_din_match(self):
        df = pd.DataFrame({"person_id": [1, 2], "dispense_date": [day(4), day(4)], "din": ["02232043", "02232044"]})
        assert case_day(apply(self.defn, drugs=df), 1) == 4
        assert ids(apply(self.defn, drugs=df)) == {1}

    def test_din_read_as_number_gets_zeros_back(self):
        df = pd.DataFrame({"person_id": [1], "date": [day(0)], "din": [2232043]})
        assert ids(apply(self.defn, drugs=df)) == {1}

    def test_missing_din_column(self):
        with pytest.raises(CasedefsInputError, match="din"):
            apply(self.defn, drugs=pd.DataFrame({"person_id": [1], "date": [day(0)]}))


class TestClaimsExclusion:
    excl = ClaimsExclusion(name="other", icd9=("710",), icd10ca=("M32.1", "M33"), window_days=730,
                           min_days_between=1)
    defn = make(Rule(1, None), exclusions=(excl,))

    def test_repeat_claims_after_qualifying_exclude(self):
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), claims=claims((1, 10, "710"), (1, 20, "710.1")))
        assert res.empty

    def test_single_claim_does_not_exclude(self):
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), claims=claims((1, 10, "710")))
        assert ids(res) == {1}

    def test_claims_before_qualifying_ignored(self):
        res = apply(self.defn, hospital=hospital((1, 100, "X99")), claims=claims((1, 10, "710"), (1, 20, "710")))
        assert ids(res) == {1}

    def test_claims_too_far_apart(self):
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), claims=claims((1, 10, "710"), (1, 741, "710")))
        assert ids(res) == {1}

    def test_same_day_claims_do_not_exclude(self):
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), claims=claims((1, 10, "710"), (1, 10, "710.2")))
        assert ids(res) == {1}

    def test_icd10_codes_must_match_at_4_characters(self):
        cl = claims((1, 10, "M33.1"), (1, 20, "M33.2"))
        res = apply(self.defn, hospital=hospital((1, 0, "X99")), claims=cl, claims_coding="icd10ca")
        assert ids(res) == {1}
        cl = claims((1, 10, "M33.1"), (1, 20, "M33.19"))
        assert apply(self.defn, hospital=hospital((1, 0, "X99")), claims=cl, claims_coding="icd10ca").empty

    def test_different_icd9_codes_do_not_combine(self):
        excl = ClaimsExclusion(name="other", icd9=("710", "446"), icd10ca=())
        d = make(Rule(1, None), exclusions=(excl,))
        res = apply(d, hospital=hospital((1, 0, "X99")), claims=claims((1, 10, "710"), (1, 20, "446")))
        assert ids(res) == {1}


class TestComposite:
    a = make(Rule(1, None), id="test.a", icd10ca=("A01",))
    b = make(Rule(1, None), id="test.b", icd10ca=("B01",))
    c = make(Rule(1, None), id="test.c", icd10ca=("C01",))

    def comp(self, n, min_age=None):
        return Composite(id="test.multi", name="multi", version="t1", source_title="t",
                         source_url="https://example.org", source_location="n/a", verified=True,
                         components=("test.a", "test.b", "test.c"), min_conditions=n, min_age=min_age)

    @pytest.fixture(autouse=True)
    def registry(self, monkeypatch):
        import casedefs
        from casedefs import registry
        defs = {d.id: d for d in (self.a, self.b, self.c)}
        monkeypatch.setattr(registry, "get_definition", lambda i: defs[i])
        monkeypatch.setattr(casedefs, "get_definition", lambda i: defs[i])

    def test_date_of_second_condition(self):
        hosp = hospital((1, 0, "A01"), (1, 50, "C01"), (1, 90, "B01"), (2, 0, "A01"))
        res = apply(self.comp(2), hospital=hosp)
        assert ids(res) == {1}
        assert case_day(res, 1) == 50

    def test_three_needed(self):
        hosp = hospital((1, 0, "A01"), (1, 50, "C01"), (2, 0, "A01"), (2, 5, "B01"), (2, 9, "C01"))
        res = apply(self.comp(3), hospital=hosp)
        assert ids(res) == {2}
        assert case_day(res, 2) == 9

    def test_repeat_of_one_condition_is_not_two(self):
        assert apply(self.comp(2), hospital=hospital((1, 0, "A01"), (1, 9, "A01"))).empty

    def test_age_at_case_date(self):
        hosp = hospital((1, 0, "A01"), (1, 10, "B01"))
        assert apply(self.comp(2, min_age=35), hospital=hosp, people=people((1, "1990-01-01", "F"))).empty
        assert ids(apply(self.comp(2, min_age=35), hospital=hosp, people=people((1, "1970-01-01", "F")))) == {1}

    def test_warns_without_people(self):
        with pytest.warns(MissingPeopleWarning):
            apply(self.comp(2), hospital=hospital((1, 0, "A01")))


def test_apply_several_and_all():
    hosp = hospital((1, 0, "E11"), (1, 0, "I10"))
    pp = people((1, "1960-01-01", "M"))
    res = apply(["ccdss.diabetes", "ccdss.hypertension", "ccdss.copd"], hospital=hosp, people=pp)
    assert set(res["definition_id"]) == {"ccdss.diabetes", "ccdss.hypertension"}
    res_all = apply("all", hospital=hosp, people=pp)
    assert {"ccdss.diabetes", "ccdss.hypertension", "ccdss.multimorbidity_2plus"} <= set(res_all["definition_id"])
    assert "ccdss.multimorbidity_3plus" not in set(res_all["definition_id"])


def test_need_some_input():
    with pytest.raises(CasedefsInputError, match="at least one"):
        apply("ccdss.diabetes")
