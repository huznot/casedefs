import pandas as pd
import pytest

from casedefs.codes import matches_any, normalize_code, normalize_series
from casedefs.definition import Rule, code_range


@pytest.mark.parametrize(
    "raw, clean",
    [("250.1", "2501"), (" e11.9 ", "E119"), ("E11", "E11"), (None, ""), (float("nan"), ""), (250, "250"), ("I 50", "I50")],
)
def test_normalize_code(raw, clean):
    assert normalize_code(raw) == clean


def test_normalize_series_handles_missing():
    out = normalize_series(pd.Series(["250.0", None, "e10"]))
    assert list(out) == ["2500", "", "E10"]


def test_prefix_matching_with_and_without_dots():
    codes = pd.Series(["250", "250.1", "2509", "E11.9", "e119", "E12", "25", "V27.0", "0250"])
    hit = matches_any(codes, ["250", "E11", "V27"])
    assert list(hit) == [True, True, True, True, True, False, False, True, False]


def test_prefix_matching_dotted_prefix():
    assert list(matches_any(pd.Series(["I500", "I51"]), ["I50.0"])) == [True, False]


def test_no_prefixes_matches_nothing():
    assert not matches_any(pd.Series(["250"]), []).any()


def test_code_range_expands_exactly():
    assert code_range("O10", "O16") == ("O10", "O11", "O12", "O13", "O14", "O15", "O16")
    assert code_range("641", "643") == ("641", "642", "643")
    assert code_range("O98", "O99") == ("O98", "O99")


@pytest.mark.parametrize("start, end", [("O10", "P16"), ("O1", "O16"), ("O16", "O10")])
def test_code_range_rejects_bad_ranges(start, end):
    with pytest.raises(ValueError):
        code_range(start, end)


def test_rule_describe():
    assert Rule(1, 2, 730).describe() == ">= 1 hospital record(s) OR >= 2 physician claim(s) within 730 days"
    assert Rule(1, 1, None).describe() == ">= 1 hospital record(s) OR >= 1 physician claim(s)"
    assert Rule(None, 3, 30).describe() == ">= 3 physician claim(s) within 30 days"
