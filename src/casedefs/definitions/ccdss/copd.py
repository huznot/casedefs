from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.copd",
    name="Chronic obstructive pulmonary disease (COPD)",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(13),
    verified=True,
    icd9=("491", "492", "496"),
    icd10ca=("J41", "J42", "J43", "J44"),
    # one or more hospital separation records or one or more physician claims
    rule=Rule(min_hospital=1, min_claims=1, window_days=None),
    min_age=35,
    notes=(
        "all hospital diagnosis fields are used, but only the first diagnosis field of each "
        "physician claim. if your claims have several diagnosis fields, pass only the first one. "
        "case date is the first hospital record or physician claim."
    ),
)
