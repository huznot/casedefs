"""the example data in examples/ is hand built; this pins what it should produce."""

import warnings
from pathlib import Path

import pandas as pd

from casedefs import apply

EXAMPLES = Path(__file__).parent.parent / "examples"

EXPECTED = {
    "ccdss.ami": {"P014": "2022-11-03"},  # admission date; P016 has I21.9 only as a type 3 diagnosis
    "ccdss.asthma": {"P005": "2019-12-20"},
    "ccdss.copd": {"P004": "2016-11-11"},  # P008 is 31
    "ccdss.dementia": {"P011": "2019-05-01", "P013": "2021-02-02"},  # P013 by drug; P010 has another din
    "ccdss.diabetes": {"P001": "2020-01-15", "P003": "2017-08-02"},  # P002 gestational, P006 732 days
    "ccdss.heart_failure": {"P003": "2019-09-30", "P004": "2018-02-14"},
    "ccdss.hypertension": {"P001": "2018-05-20", "P003": "2017-08-02", "P010": "2021-01-31"},  # P007 one claim
    "ccdss.ischemic_heart_disease": {"P012": "2017-03-03", "P014": "2022-11-12", "P016": "2022-01-20"},
    "ccdss.multimorbidity_2plus": {
        "P001": "2020-01-15", "P003": "2017-08-02", "P004": "2018-02-14", "P011": "2019-05-01", "P012": "2020-03-01",
    },
    "ccdss.multimorbidity_3plus": {"P003": "2019-09-30"},
    "ccdss.osteoporosis": {"P011": "2018-06-06"},
    "ccdss.parkinsonism": {"P012": "2020-03-01"},
    "ccdss.rheumatoid_arthritis": {},  # P015 claims are only 40 days apart
}


def test_example_data_results():
    tables = {n: pd.read_csv(EXAMPLES / f"{n}.csv", dtype=str)
              for n in ["claims", "hospital", "people", "procedures", "drugs"]}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        res = apply("all", **tables)
    got: dict = {}
    for def_id, person, date in zip(res["definition_id"], res["person_id"], res["case_date"].dt.strftime("%Y-%m-%d")):
        got.setdefault(def_id, {})[person] = date
    for def_id, expected in EXPECTED.items():
        assert got.get(def_id, {}) == expected, def_id
    assert set(got) <= set(EXPECTED)
