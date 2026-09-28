from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, pregnancy_exclusion, row

DEFINITION = Definition(
    id="ccdss.hypertension",
    name="Hypertension, excluding gestational hypertension",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(14),
    verified=True,
    icd9=("401", "402", "403", "404", "405"),
    icd10ca=("I10", "I11", "I12", "I13", "I15"),
    # one or more hospital separation records, or two or more physician
    # claims within two years. two years is read as 730 days.
    rule=Rule(min_hospital=1, min_claims=2, window_days=730),
    min_age=20,
    exclusions=(pregnancy_exclusion(20, 54, "hypertension"),),
    notes=(
        "all hospital diagnosis fields and all physician diagnosis fields are used. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
