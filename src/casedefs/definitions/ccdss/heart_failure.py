from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.heart_failure",
    name="Heart failure",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(18),
    verified=True,
    icd9=("428",),
    icd10ca=("I50",),
    # one or more hospital separation records, or two or more physician
    # claims within one year. one year is read as 365 days.
    rule=Rule(min_hospital=1, min_claims=2, window_days=365),
    min_age=40,
    notes=(
        "all hospital diagnosis fields and all physician diagnosis fields are used. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
