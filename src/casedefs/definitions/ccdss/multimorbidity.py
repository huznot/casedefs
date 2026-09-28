"""ccdss multimorbidity: cases of 2+ or 3+ of the selected chronic conditions."""

from ...definition import Composite
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

# listed in the notes column (AD) of rows 42 and 43
CONDITIONS = (
    "ccdss.asthma",
    "ccdss.copd",
    "ccdss.dementia",
    "ccdss.diabetes",
    "ccdss.epilepsy",
    "ccdss.gout",
    "ccdss.heart_failure",
    "ccdss.hypertension",
    "ccdss.ischemic_heart_disease",
    "ccdss.multiple_sclerosis",
    "ccdss.osteoarthritis",
    "ccdss.osteoporosis",
    "ccdss.parkinsonism",
    "ccdss.rheumatoid_arthritis",
    "ccdss.schizophrenia",
    "ccdss.stroke",
)

NOTES = (
    "each condition uses its own casedefs definition, including its age limits. "
    "the case date is the date the person meets the needed number of conditions, "
    "and the person must be 35+ on that date."
)

DEFINITION = Composite(
    id="ccdss.multimorbidity_2plus",
    name="Multimorbidity, 2+ of 16 selected CCDSS chronic conditions",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(42),
    verified=True,
    components=CONDITIONS,
    min_conditions=2,
    min_age=35,
    notes=NOTES,
)
