import pandas as pd
import pytest

from casedefs import CasedefsInputError, apply
from casedefs.inputs import claims_events, hospital_events, people_table

from .conftest import claims, hospital, ids

DIAB = "ccdss.diabetes"

# these tests are about input handling; the missing age check is expected
pytestmark = pytest.mark.filterwarnings("ignore::casedefs.MissingPeopleWarning")


def test_column_mapping_for_claims():
    df = pd.DataFrame({"PHN": [1, 1], "svc": ["2020-01-01", "2020-06-01"], "diag": ["250", "250"]})
    res = apply(DIAB, claims=df, columns={"person_id": "PHN", "service_date": "svc", "dx_code": "diag"})
    assert ids(res) == {1}


def test_missing_column_error_names_the_column():
    df = pd.DataFrame({"id": [1], "service_date": ["2020-01-01"], "dx_code": ["250"]})
    with pytest.raises(CasedefsInputError, match="missing column.*person_id.*columns found: id"):
        apply(DIAB, claims=df)


def test_bad_date_error_shows_row_and_value():
    df = claims((1, 0, "250"))
    df.loc[0, "service_date"] = "not a date"
    with pytest.raises(CasedefsInputError, match=r"claims.service_date: row 0: 'not a date'"):
        apply(DIAB, claims=df)


def test_blank_date_is_an_error():
    df = claims((1, 0, "250"), (1, 1, "250"))
    df.loc[1, "service_date"] = None
    with pytest.raises(CasedefsInputError, match="could not read 1 date"):
        claims_events(df)


def test_date_format_option():
    df = pd.DataFrame({"person_id": [1, 1], "service_date": ["31/01/2020", "01/03/2020"], "dx_code": ["250", "250"]})
    ev = claims_events(df, date_format="%d/%m/%Y")
    assert list(ev["date"].dt.strftime("%Y-%m-%d")) == ["2020-01-31", "2020-03-01"]


def test_datetime_column_accepted():
    df = claims((1, 0, "250"))
    df["service_date"] = pd.to_datetime(df["service_date"])
    assert len(claims_events(df)) == 1


def test_blank_codes_dropped():
    df = claims((1, 0, "250"), (1, 1, None), (1, 2, "  "))
    assert len(claims_events(df)) == 1


def test_hospital_long_format():
    df = pd.DataFrame(
        {"person_id": [1, 1, 2], "date": ["2020-01-01", "2020-01-01", "2020-02-01"], "dx_code": ["I10", "E11.9", "J45"]}
    )
    ev = hospital_events(df)
    assert ev.groupby("person_id")["record_id"].nunique().to_dict() == {1: 1, 2: 1}
    assert ids(apply(DIAB, hospital=df)) == {1}


def test_hospital_wide_format_with_custom_columns():
    df = pd.DataFrame({"pid": [1], "sep": ["2020-01-01"], "DIAG1": ["I10"], "DIAG2": ["E11"]})
    cols = {"person_id": "pid", "separation_date": "sep", "hospital_dx_columns": ["DIAG1", "DIAG2"]}
    assert ids(apply(DIAB, hospital=df, columns=cols)) == {1}


def test_hospital_admit_date_accepted():
    df = pd.DataFrame({"person_id": [1], "admit_date": ["2020-01-01"], "dx_code_1": ["E11"]})
    assert ids(apply(DIAB, hospital=df)) == {1}


def test_hospital_wide_columns_sorted_numerically():
    df = pd.DataFrame({"person_id": [1], "date": ["2020-01-01"], "dx_code_10": ["A"], "dx_code_2": ["B"]})
    assert set(hospital_events(df)["code"]) == {"A", "B"}


def test_hospital_without_date_column():
    df = pd.DataFrame({"person_id": [1], "when": ["2020-01-01"], "dx_code": ["E11"]})
    with pytest.raises(CasedefsInputError, match="separation_date, admit_date, date"):
        apply(DIAB, hospital=df)


def test_hospital_without_dx_columns():
    df = pd.DataFrame({"person_id": [1], "date": ["2020-01-01"], "diag": ["E11"]})
    with pytest.raises(CasedefsInputError, match="dx_code_1"):
        apply(DIAB, hospital=df)


def test_hospital_mapped_dx_columns_must_exist():
    df = pd.DataFrame({"person_id": [1], "date": ["2020-01-01"], "D1": ["E11"]})
    with pytest.raises(CasedefsInputError, match="D2"):
        apply(DIAB, hospital=df, columns={"hospital_dx_columns": ["D1", "D2"]})


def test_bad_icd_version_values():
    df = hospital((1, 0, "E11"))
    df["icd_version"] = ["eleven"]
    with pytest.raises(CasedefsInputError, match="not 9 or 10"):
        apply(DIAB, hospital=df)


def test_bad_coding_argument():
    with pytest.raises(CasedefsInputError, match="coding must be one of"):
        apply(DIAB, hospital=hospital((1, 0, "E11")), hospital_coding="icd11")


def test_need_claims_or_hospital():
    with pytest.raises(CasedefsInputError, match="at least one"):
        apply(DIAB)


def test_unknown_definition():
    with pytest.raises(KeyError, match="available: ccdss"):
        apply("ccdss.nope", hospital=hospital((1, 0, "E11")))


def test_people_duplicate_ids():
    df = pd.DataFrame({"person_id": [1, 1], "birth_date": ["1970-01-01", "1970-01-01"]})
    with pytest.raises(CasedefsInputError, match="more than one row"):
        people_table(df)


def test_people_sex_is_optional_and_normalized():
    df = pd.DataFrame({"person_id": [1, 2], "birth_date": ["1970-01-01", ""], "sex": ["female", " m"]})
    out = people_table(df)
    assert list(out["sex"]) == ["F", "M"]
    assert pd.isna(out["birth_date"].iloc[1])
    assert people_table(df.drop(columns="sex"))["sex"].isna().all()


def test_mixed_person_id_types_are_matched():
    cl = claims(("1", 0, "250"), ("1", 100, "250"))
    pp = pd.DataFrame({"person_id": [1], "birth_date": ["1970-01-01"], "sex": ["M"]})
    res = apply(DIAB, claims=cl, people=pp)
    assert list(res["person_id"]) == ["1"]
