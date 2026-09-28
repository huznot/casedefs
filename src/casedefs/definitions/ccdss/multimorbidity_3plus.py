from ...definition import Composite
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row
from .multimorbidity import CONDITIONS, NOTES

DEFINITION = Composite(
    id="ccdss.multimorbidity_3plus",
    name="Multimorbidity, 3+ of 16 selected CCDSS chronic conditions",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(43),
    verified=True,
    components=CONDITIONS,
    min_conditions=3,
    min_age=35,
    notes=NOTES,
)
