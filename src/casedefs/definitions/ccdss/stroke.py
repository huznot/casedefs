from ...definition import Definition, Rule
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.stroke",
    name="Stroke",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(19),
    verified=True,
    # hospital ICD-9 as listed: 325, 362.3x, 430, 431, 432.9, 433.x1,
    # 434 (or 434.x1), 435.x, 436, 437.6. 433.x1 is spelled out digit by digit.
    icd9=("325", "362.3", "430", "431", "432.9")
    + tuple(f"433.{x}1" for x in range(10))
    + ("434", "435", "436", "437.6"),
    icd10ca=("G08", "G45", "H34.0", "H34.1", "I60", "I61", "I62.9", "I63", "I64", "I67.6"),
    # physician ICD-9 is a shorter list; ICD-10-CA is the same
    claims_icd9=("325", "430", "431", "432.9", "434", "435", "436", "437.6"),
    excluded_codes=("G45.4",),
    # one or more hospital separation records, or two or more physician
    # claims within one year
    rule=Rule(min_hospital=1, min_claims=2, window_days=365),
    min_age=20,
    notes=(
        "G45 excludes G45.4 (transient global amnesia). ICD-9 434 is used as a 3 digit prefix; "
        "the source adds 'or 434.x1' for ICD-9-CM data, which this does not narrow to. "
        "source footnote e: 432.9 and I62.9 were used for haemorrhagic stroke before 2015/16 and "
        "are collected only before 2015/16; they are kept for all years here. "
        "all hospital diagnosis fields, first physician diagnosis field only. "
        "case date is the hospital record or the second physician claim, whichever comes first."
    ),
)
