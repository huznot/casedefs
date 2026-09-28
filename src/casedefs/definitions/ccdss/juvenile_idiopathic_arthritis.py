from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.juvenile_idiopathic_arthritis",
    name="Juvenile idiopathic arthritis",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(40),
    verified=True,
    icd9=("714", "720"),
    icd10ca=("M05", "M06", "M07.0", "M07.1", "M07.2", "M07.3", "M08", "M45"),
    # one or more hospital separation records, or two or more physician
    # claims (more than 8 weeks apart) within two years. more than 56 days
    # apart means at least 57.
    rule=Rule(min_hospital=1, min_claims=2, window_days=730, min_days_between=57),
    max_age=15,
    notes=(
        "ages 15 and under on the case date. source footnote n: ICD-9 721 also counts in Ontario "
        "physician claims only; it is not included here. all hospital diagnosis fields, first "
        "physician diagnosis field only."
    ),
)
