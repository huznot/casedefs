from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.parkinsonism",
    name="Parkinsonism, including Parkinson disease",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(25),
    verified=True,
    # the source does not use hospital records for this condition
    icd9=(),
    icd10ca=(),
    claims_icd9=("332",),
    claims_icd10ca=("F02.3", "G20", "G21", "G22"),
    # two or more physician claims within one year, with at least 30 days
    # between the first and the second claim
    rule=Rule(min_hospital=None, min_claims=2, window_days=365, min_days_between=30),
    min_age=40,
    notes="physician claims only, all diagnosis fields. case date is the second claim.",
)
