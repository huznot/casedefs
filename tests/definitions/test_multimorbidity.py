from casedefs import apply, get_definition

from ..conftest import case_day, claims, hospital, ids, people


def test_metadata():
    two, three = get_definition("ccdss.multimorbidity_2plus"), get_definition("ccdss.multimorbidity_3plus")
    assert len(two.components) == 16 and two.components == three.components
    assert (two.min_conditions, three.min_conditions, two.min_age) == (2, 3, 35)
    assert "ccdss.ami" not in two.components and "ccdss.autism" not in two.components


def test_two_conditions():
    hosp = hospital((1, 0, "E11"), (1, 300, "J45"), (2, 0, "E11"))
    pp = people((1, "1960-01-01", "F"), (2, "1960-01-01", "F"))
    res = apply("ccdss.multimorbidity_2plus", hospital=hosp, people=pp)
    assert ids(res) == {1}
    assert case_day(res, 1) == 300
    assert apply("ccdss.multimorbidity_3plus", hospital=hosp, people=pp).empty


def test_three_conditions_mixing_claims_and_hospital():
    hosp = hospital((1, 0, "I10"), (1, 50, "I50"))
    cl = claims((1, 100, "715"), (1, 200, "715"))
    res = apply("ccdss.multimorbidity_3plus", hospital=hosp, claims=cl, people=people((1, "1950-01-01", "M")))
    assert case_day(res, 1) == 200


def test_under_35():
    hosp = hospital((1, 0, "E11"), (1, 10, "J45"))
    assert apply("ccdss.multimorbidity_2plus", hospital=hosp, people=people((1, "1990-01-01", "F"))).empty

