from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.gout",
    name="Gout and other crystal arthropathies",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(38),
    verified=True,
    icd9=("274", "712"),
    icd10ca=("M10", "M11"),
    # one or more hospital separation records or two or more physician
    # claims (separated by at least 1 day) within five years
    rule=Rule(min_hospital=1, min_claims=2, window_days=1825, min_days_between=1),
    min_age=20,
    notes=(
        "five years is read as 1825 days. source footnote m: ICD-9 712 is not available in "
        "Saskatchewan. all hospital diagnosis fields, first physician diagnosis field only. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
