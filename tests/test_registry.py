from casedefs import Composite, list_definitions
from casedefs.registry import all_definitions, get_definition

CCDSS = {
    "ccdss.ami", "ccdss.asthma", "ccdss.autism", "ccdss.copd", "ccdss.dementia", "ccdss.diabetes",
    "ccdss.epilepsy", "ccdss.gout", "ccdss.heart_failure", "ccdss.hypertension",
    "ccdss.ischemic_heart_disease", "ccdss.juvenile_idiopathic_arthritis", "ccdss.multimorbidity_2plus",
    "ccdss.multimorbidity_3plus", "ccdss.multiple_sclerosis", "ccdss.osteoarthritis", "ccdss.osteoporosis",
    "ccdss.parkinsonism", "ccdss.rheumatoid_arthritis", "ccdss.schizophrenia", "ccdss.stroke",
}
COUNTS = {"ccdss": 21, "tonelli": 30, "quan.charlson": 17, "quan.elixhauser": 31}


def test_all_ccdss_definitions_registered():
    assert {k for k in all_definitions() if k.startswith("ccdss.")} == CCDSS


def test_counts_per_source():
    ids = list(all_definitions())
    for prefix, n in COUNTS.items():
        assert sum(1 for i in ids if i.startswith(prefix + ".")) == n, prefix
    assert len(ids) == sum(COUNTS.values())


def test_list_definitions_table():
    df = list_definitions()
    assert list(df.columns) == ["id", "name", "version", "verified", "ages", "rule", "source"]
    assert set(df["id"]) == set(all_definitions())


def test_every_definition_has_citation_and_codes():
    for d in all_definitions().values():
        assert d.source_url.startswith(("https://", "http://")), d.id
        assert d.source_location, d.id
        assert d.version, d.id
        assert d.citation().endswith(d.source_url)
        if isinstance(d, Composite):
            for c in d.components:
                if isinstance(c, str):
                    get_definition(c)
        else:
            icd9, icd10 = d.claims_codes
            assert d.icd9 or d.icd10ca or icd9 or icd10, d.id


def test_codes_are_clean():
    # codes are stored normalized: uppercase, no dots, no spaces, no 'x'
    for d in all_definitions().values():
        if isinstance(d, Composite):
            continue
        for code in d.icd9 + d.icd10ca:
            assert code == code.strip(), d.id
            assert "X" not in code and " " not in code, (d.id, code)


def test_catalog_is_up_to_date():
    # regenerate with: python -m casedefs.catalog > docs/definitions.md
    from pathlib import Path

    from casedefs.catalog import render

    path = Path(__file__).parent.parent / "docs" / "definitions.md"
    assert path.read_text(encoding="utf-8").replace("\r\n", "\n") == render(), "run python -m casedefs.catalog"
