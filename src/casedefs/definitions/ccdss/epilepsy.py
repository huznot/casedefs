from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.epilepsy",
    name="Epilepsy",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(22),
    verified=True,
    icd9=("345.0", "345.1", "345.4", "345.5", "345.6", "345.7", "345.8", "345.9"),
    icd10ca=("G40",),
    claims_icd9=("345",),
    # ages 1-19: three or more physician claims within two years, at least
    # 30 days between each. ages 20+: that, or one or more hospital records.
    rule=Rule(min_hospital=1, min_claims=3, window_days=730, min_days_between=30, hospital_min_age=20),
    min_age=1,
    notes=(
        "hospital records only count from age 20 (on the hospital date). "
        "all hospital and all physician diagnosis fields are used. case date is the hospital "
        "record or the third physician claim, whichever comes first."
    ),
)
