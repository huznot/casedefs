from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, pregnancy_exclusion, row

DEFINITION = Definition(
    id="ccdss.diabetes",
    name="Diabetes mellitus (types combined), excluding gestational diabetes",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(6),
    verified=True,
    # hospital and physician billing codes are the same in the source, 3 digits
    icd9=("250",),
    icd10ca=("E10", "E11", "E13", "E14"),
    # one or more hospital separation records, or two or more physician
    # claims within two years. two years is read as 730 days.
    rule=Rule(min_hospital=1, min_claims=2, window_days=730),
    min_age=1,
    exclusions=(pregnancy_exclusion(10, 54, "diabetes"),),
    notes=(
        "all hospital diagnosis fields and all physician diagnosis fields are used. "
        "case date is the hospital record or the second physician claim, whichever comes first. "
        "source note: Nova Scotia found the CCDSS overestimates diabetes in children and youth, "
        "and its data for ages 1 to 19 are excluded from national reporting. "
        "a 2019 PHAC article lists E12 and a 190 day window; this follows the v2024 "
        "spreadsheet (see docs/sources.md)."
    ),
)
