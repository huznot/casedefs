import pandas as pd
import pytest
from typer.testing import CliRunner

from casedefs.cli import app

from .conftest import claims, hospital, people

runner = CliRunner()


@pytest.fixture
def files(tmp_path):
    cl = claims((1, 0, "250.00"), (1, 100, "250"), (2, 0, "250"), (2, 800, "250"))
    hosp = hospital((3, 10, "E11.9"))
    pp = people((1, "1970-01-01", "M"), (2, "1970-01-01", "F"), (3, "1970-01-01", "F"))
    paths = {}
    for name, df in [("claims", cl), ("hospital", hosp), ("people", pp)]:
        paths[name] = tmp_path / f"{name}.csv"
        df.to_csv(paths[name], index=False)
    paths["out"] = tmp_path / "out" / "cases.csv"
    return paths


def test_list():
    res = runner.invoke(app, ["list"])
    assert res.exit_code == 0
    assert "ccdss.diabetes" in res.output
    assert "health-infobase.canada.ca" in res.output


def test_show():
    res = runner.invoke(app, ["show", "ccdss.diabetes"])
    assert res.exit_code == 0
    for text in ["E10, E11, E13, E14", "250", "within 730 days", "gestational diabetes", "row 6"]:
        assert text in res.output


def test_show_unknown():
    res = runner.invoke(app, ["show", "ccdss.nope"])
    assert res.exit_code == 1
    assert "unknown definition" in res.output


def test_version():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert res.output.strip()


def test_run(files):
    res = runner.invoke(
        app,
        ["run", "ccdss.diabetes", "--claims", str(files["claims"]), "--hospital", str(files["hospital"]),
         "--people", str(files["people"]), "-o", str(files["out"])],
    )
    assert res.exit_code == 0, res.output
    assert "2 case(s)" in res.output
    out = pd.read_csv(files["out"], dtype=str)
    assert list(out.columns) == ["person_id", "case_date", "definition_id", "definition_version"]
    assert out.set_index("person_id")["case_date"].to_dict() == {"3": "2015-01-11", "1": "2015-04-11"}


def test_run_warns_without_people(files):
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--hospital", str(files["hospital"]), "-o", str(files["out"])])
    assert res.exit_code == 0
    assert "warning: ccdss.diabetes has an age limit" in res.output


def test_run_with_column_map(tmp_path):
    src = tmp_path / "c.csv"
    pd.DataFrame({"PHN": ["9", "9"], "svc_dt": ["2020-01-01", "2020-02-01"], "dx": ["250", "250"]}).to_csv(src, index=False)
    out = tmp_path / "o.csv"
    res = runner.invoke(
        app,
        ["run", "ccdss.diabetes", "--claims", str(src), "-o", str(out),
         "--map", "person_id=PHN", "--map", "service_date=svc_dt", "--map", "dx_code=dx"],
    )
    assert res.exit_code == 0, res.output
    assert "1 case(s)" in res.output


def test_run_hospital_dx_option(tmp_path):
    src = tmp_path / "h.csv"
    pd.DataFrame({"person_id": ["1"], "date": ["2020-01-01"], "D1": ["I10"], "D2": ["E11"]}).to_csv(src, index=False)
    out = tmp_path / "o.csv"
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--hospital", str(src), "--hospital-dx", "D1,D2", "-o", str(out)])
    assert res.exit_code == 0, res.output
    assert "1 case(s)" in res.output


def test_run_missing_column_message(tmp_path):
    src = tmp_path / "c.csv"
    pd.DataFrame({"id": ["1"], "service_date": ["2020-01-01"], "dx_code": ["250"]}).to_csv(src, index=False)
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--claims", str(src), "-o", str(tmp_path / "o.csv")])
    assert res.exit_code == 1
    assert "missing column(s): person_id" in res.output


def test_run_bad_dates_message(tmp_path):
    src = tmp_path / "c.csv"
    pd.DataFrame({"person_id": ["1"], "service_date": ["32/13/2020"], "dx_code": ["250"]}).to_csv(src, index=False)
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--claims", str(src), "-o", str(tmp_path / "o.csv")])
    assert res.exit_code == 1
    assert "could not read 1 date(s) in claims.service_date" in res.output


def test_run_needs_an_input(tmp_path):
    res = runner.invoke(app, ["run", "ccdss.diabetes", "-o", str(tmp_path / "o.csv")])
    assert res.exit_code == 1
    assert "--claims" in res.output and "--drugs" in res.output


def test_run_missing_file(tmp_path):
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--claims", str(tmp_path / "nope.csv"), "-o", str(tmp_path / "o.csv")])
    assert res.exit_code == 1
    assert "not found" in res.output


def test_run_unknown_definition(files):
    res = runner.invoke(app, ["run", "ccdss.nope", "--claims", str(files["claims"]), "-o", str(files["out"])])
    assert res.exit_code == 1


def test_run_bad_map(files):
    res = runner.invoke(app, ["run", "ccdss.diabetes", "--claims", str(files["claims"]), "--map", "oops", "-o", str(files["out"])])
    assert res.exit_code == 1
    assert "standard=yours" in res.output


def test_show_compacts_code_runs():
    res = runner.invoke(app, ["show", "ccdss.hypertension"])
    assert "O10-O16, O21-O95, O98, O99, Z37" in res.output
    assert "641-679, V27" in res.output
    assert "401-405" in res.output


def test_run_several_and_all(files):
    res = runner.invoke(
        app,
        ["run", "ccdss.diabetes", "ccdss.hypertension", "--claims", str(files["claims"]),
         "--hospital", str(files["hospital"]), "--people", str(files["people"]), "-o", str(files["out"])],
    )
    assert res.exit_code == 0, res.output
    assert "of 2 definitions" in res.output
    res = runner.invoke(app, ["run", "all", "--hospital", str(files["hospital"]), "--people", str(files["people"]),
                              "-o", str(files["out"])])
    assert res.exit_code == 0, res.output
    # repeated warnings are shown once
    assert res.output.count("no dx_type columns") == 1


def test_run_procedures_and_drugs(tmp_path):
    procs = tmp_path / "p.csv"
    pd.DataFrame({"person_id": ["1"], "procedure_date": ["2020-01-01"], "proc_code": ["1.IJ.50.GQ"]}).to_csv(procs, index=False)
    drugs = tmp_path / "d.csv"
    pd.DataFrame({"person_id": ["2"], "dispense_date": ["2020-01-01"], "din": ["02232043"]}).to_csv(drugs, index=False)
    out = tmp_path / "o.csv"
    res = runner.invoke(app, ["run", "ccdss.ischemic_heart_disease", "ccdss.dementia", "--procedures", str(procs),
                              "--drugs", str(drugs), "-o", str(out)])
    assert res.exit_code == 0, res.output
    got = pd.read_csv(out, dtype=str)
    assert set(zip(got["person_id"], got["definition_id"])) == {("1", "ccdss.ischemic_heart_disease"), ("2", "ccdss.dementia")}


@pytest.mark.parametrize("def_id", ["ccdss.ami", "ccdss.dementia", "ccdss.rheumatoid_arthritis", "ccdss.stroke",
                                    "ccdss.multimorbidity_2plus", "ccdss.parkinsonism"])
def test_show_every_kind(def_id):
    res = runner.invoke(app, ["show", def_id])
    assert res.exit_code == 0, res.output
    assert "source:" in res.output


def test_show_details():
    assert "never counts:        G45.4" in runner.invoke(app, ["show", "ccdss.stroke"]).output
    assert "223 DINs" in runner.invoke(app, ["show", "ccdss.dementia"]).output
    assert "conditions: ccdss.asthma" in runner.invoke(app, ["show", "ccdss.multimorbidity_3plus"]).output
    park = runner.invoke(app, ["show", "ccdss.parkinsonism"]).output
    assert "hospital ICD" not in park and "claims ICD-10-CA:    F02.3, G20-G22" in park
