from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.ami",
    name="Acute myocardial infarction (AMI)",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(16) + "; diagnosis types from footnote d (row 52)",
    verified=True,
    icd9=("410",),
    icd10ca=("I21", "I22"),
    # one or more hospital admission records, no physician claims path
    rule=Rule(min_hospital=1, min_claims=None),
    min_age=20,
    # most responsible diagnosis, service transfer types W, X, Y, and types 1 and 2
    hospital_dx_types=("M", "W", "X", "Y", "1", "2"),
    hospital_date="admission",
    notes=(
        "hospital records only. only diagnoses of type MRDx (M), W, X, Y, 1 or 2 count, which "
        "needs dx_type columns; without them every diagnosis field is used and a warning is shown. "
        "case date is the first admission date. this gives the first AMI; the ccdss also reports "
        "AMI events per year, which casedefs does not."
    ),
)
