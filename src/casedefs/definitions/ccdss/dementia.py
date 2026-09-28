from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row
from ._dementia_dins import DEMENTIA_DINS

DEFINITION = Definition(
    id="ccdss.dementia",
    name="Dementia, including Alzheimer disease",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(21) + "; drug list from footnote f (row 54)",
    verified=True,
    icd9=("046.1", "290.0", "290.1", "290.2", "290.3", "290.4", "294.1", "294.2", "331.0", "331.1",
          "331.5", "331.82"),
    icd10ca=("G30", "F00", "F01", "F02", "F03"),
    claims_icd9=("290", "331"),
    drug_dins=DEMENTIA_DINS,
    # one or more hospital separation records; or three or more physician
    # claims within two years, with at least 30 days between each claim; or
    # one drug prescription or more
    rule=Rule(min_hospital=1, min_claims=3, window_days=730, min_days_between=30, min_drugs=1),
    min_age=65,
    notes=(
        "hospital ICD-9 lists 331.5, or 331.82 in ICD-9-CM; both are included. in ICD-9-CM data "
        "331.5 is normal pressure hydrocephalus, so check this if your hospital data is ICD-9-CM. "
        "source: Saskatchewan also counts ICD-9 298 in physician claims; not included here. "
        "the drug path needs a drugs table (person_id, dispense_date, din). "
        "case date is the hospital record, third physician claim or drug date, whichever comes first."
    ),
)
