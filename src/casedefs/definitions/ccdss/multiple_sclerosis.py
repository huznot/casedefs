from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.multiple_sclerosis",
    name="Multiple sclerosis",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(24),
    verified=True,
    icd9=("340",),
    icd10ca=("G35",),
    # one or more hospital separation records, or five or more physician
    # claims within two years
    rule=Rule(min_hospital=1, min_claims=5, window_days=730),
    min_age=20,
    notes=(
        "all hospital and all physician diagnosis fields are used. "
        "case date is the hospital record or the fifth physician claim, whichever comes first."
    ),
)
