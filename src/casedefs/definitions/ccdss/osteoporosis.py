from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.osteoporosis",
    name="Osteoporosis (population burden)",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(26) + "; hospital ICD-9 digits from footnote h (row 56)",
    verified=True,
    # row 26 lists hospital ICD-9 as 733 at 4 digits, and footnote h gives the
    # hospital ICD-9 osteoporosis code as 733.0, so hospitals use 733.0
    icd9=("733.0",),
    icd10ca=("M80", "M81"),
    # physician claims use 733 at 3 digits
    claims_icd9=("733",),
    # one or more hospital separation records or one or more physician claims
    rule=Rule(min_hospital=1, min_claims=1),
    min_age=40,
    hospital_date="admission",
    notes=(
        "hospital ICD-9 is 733.0: row 26 says 733 at 4 digits and footnote h names 733.0. "
        "physician ICD-9 733 is 3 digits in the source, so it also covers other 733 bone conditions. "
        "all hospital diagnosis fields, first physician diagnosis field only. "
        "case date is the hospital admission or physician claim, whichever comes first."
    ),
)
