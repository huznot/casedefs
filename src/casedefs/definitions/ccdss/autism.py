from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.autism",
    name="Autism",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(44),
    verified=True,
    icd9=("299",),
    icd10ca=("F84",),
    # one or more hospital separation records, or two or more physician
    # claims. the source gives no time window.
    rule=Rule(min_hospital=1, min_claims=2, window_days=None),
    min_age=1,
    max_age=19,
    notes=(
        "all hospital diagnosis fields, first physician diagnosis field only. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
