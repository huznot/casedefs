from ...definition import ClaimsExclusion, Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

NON_RA = ClaimsExclusion(
    name="other inflammatory arthritides",
    # systemic autoimmune rheumatic diseases, polyarteritis nodosa and allied
    # conditions, polymyalgia rheumatica, psoriatic arthritis (and psoriasis
    # for ICD-9), ankylosing spondylitis and other inflammatory
    # spondylopathies, arthropathy associated with other disorders
    icd9=("710", "446", "725", "696", "720", "713"),
    icd10ca=("M32.1", "M32.8", "M32.9", "M33", "M34", "M35.1", "M35.8", "M35.9", "M30", "M31",
             "M35.3", "L40.5", "M07.0", "M07.1", "M07.2", "M07.3", "M45", "M46.1", "M46.8", "M46.9",
             "M07.4", "M07.5", "M07.6"),
    min_claims=2,
    window_days=730,
    min_days_between=1,
    icd9_digits=3,
    icd10ca_digits=4,
    description=(
        "after qualifying, a person with at least two physician claims (at least 1 day apart) "
        "within two years for the same non-RA inflammatory arthritis code is not a case"
    ),
)

DEFINITION = Definition(
    id="ccdss.rheumatoid_arthritis",
    name="Rheumatoid arthritis (RA)",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(37),
    verified=True,
    icd9=("714",),
    icd10ca=("M05", "M06"),
    # one or more hospital separation records, or two or more physician
    # claims (more than 8 weeks apart) within two years
    rule=Rule(min_hospital=1, min_claims=2, window_days=730, min_days_between=57),
    min_age=16,
    exclusions=(NON_RA,),
    notes=(
        "case_date here is the date the rule is first met. the ccdss sets its RA case date 730 "
        "days after that, to leave room for the exclusion. the exclusion looks at claims on or "
        "after the qualifying date for the rest of the data, and compares codes at 3 characters "
        "for ICD-9 and 4 for ICD-10-CA. source footnote m: ICD-9 713 is not available in "
        "Saskatchewan. all hospital diagnosis fields, first physician diagnosis field only."
    ),
)
