from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.schizophrenia",
    name="Schizophrenia",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(9),
    verified=True,
    icd9=("295",),
    icd10ca=("F20", "F21", "F23", "F25"),
    # one or more hospital separation records, or two or more physician
    # claims within two years, with at least 30 days between each claim
    rule=Rule(min_hospital=1, min_claims=2, window_days=730, min_days_between=30),
    min_age=10,
    notes=(
        "all hospital diagnosis fields, first physician diagnosis field only. "
        "case date is the hospital record or the second physician claim, whichever comes first. "
        "source warning: validation suggests this definition may misclassify a significant "
        "proportion of cases, and PHAC plans to reassess it."
    ),
)
