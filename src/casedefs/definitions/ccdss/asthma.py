from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.asthma",
    name="Asthma",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(11),
    verified=True,
    icd9=("493",),
    icd10ca=("J45", "J46"),
    # one or more hospital separation records, or two or more physician
    # claims within two years. two years is read as 730 days.
    rule=Rule(min_hospital=1, min_claims=2, window_days=730),
    min_age=1,
    notes=(
        "all hospital diagnosis fields are used, but only the first diagnosis field of each "
        "physician claim. if your claims have several diagnosis fields, pass only the first one. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
