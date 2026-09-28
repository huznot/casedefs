import pandas as pd
import pytest

from casedefs.codes import matches_any, normalize_code, normalize_series
from casedefs.definition import Rule, code_range, expand_codes


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



@pytest.mark.parametrize("text, expected", [
    ("I42.5-I42.9, I43.x", ("I425", "I426", "I427", "I428", "I429", "I43")),
    ("456.0-456.21", ("4560", "4561", "45620", "45621")),
    ("196.x-199.1", ("196", "197", "198", "1990", "1991")),
    ("583-583.7", tuple(f"583{i}" for i in range(8))),
    ("042.x-044.x", ("042", "043", "044")),
    ("426.2-426.53", ("4262", "4263", "4264", "42650", "42651", "42652", "42653")),
    ("250, 250.1, 250", ("250", "2501")),
    ("O10-O16", tuple(f"O1{i}" for i in range(7))),
])
def test_expand_codes(text, expected):
    assert expand_codes(text) == expected


def test_expand_codes_long_range():
    out = expand_codes("174.x-195.8")
    assert out[0] == "174" and "194" in out and "195" not in out and out[-1] == "1958"


@pytest.mark.parametrize("bad", ["A10-B12", "I50-I40", "E1X1", "not a code"])
def test_expand_codes_rejects(bad):
    with pytest.raises(ValueError):
        expand_codes(bad)
