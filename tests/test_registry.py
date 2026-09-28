from casedefs import Composite, list_definitions
from casedefs.registry import all_definitions, get_definition

EXPECTED = {
    "ccdss.ami", "ccdss.asthma", "ccdss.autism", "ccdss.copd", "ccdss.dementia", "ccdss.diabetes",
    "ccdss.epilepsy", "ccdss.gout", "ccdss.heart_failure", "ccdss.hypertension",
    "ccdss.ischemic_heart_disease", "ccdss.juvenile_idiopathic_arthritis", "ccdss.multimorbidity_2plus",
    "ccdss.multimorbidity_3plus", "ccdss.multiple_sclerosis", "ccdss.osteoarthritis", "ccdss.osteoporosis",
    "ccdss.parkinsonism", "ccdss.rheumatoid_arthritis", "ccdss.schizophrenia", "ccdss.stroke",
}


def test_all_ccdss_definitions_registered():
    assert set(all_definitions()) == EXPECTED


def test_list_definitions_table():
    df = list_definitions()
    assert list(df.columns) == ["id", "name", "version", "verified", "ages", "rule", "source"]
    assert set(df["id"]) == EXPECTED


def test_every_definition_has_citation_and_codes():
    for d in all_definitions().values():
        assert d.source_url.startswith("https://"), d.id
        assert d.source_location, d.id
        assert d.version, d.id
        assert d.citation().endswith(d.source_url)
        if isinstance(d, Composite):
            for c in d.components:
                get_definition(c)
        else:
            icd9, icd10 = d.claims_codes
            assert d.icd9 or d.icd10ca or icd9 or icd10, d.id
