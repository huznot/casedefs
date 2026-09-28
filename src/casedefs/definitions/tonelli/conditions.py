"""the 30 chronic conditions of tonelli 2015, from the corrected table 1 (2019).

codes are copied from the table as printed and expanded with expand_codes,
which only spells out ranges. any reading of the table that was needed is in
the notes of that definition.
"""

from ...definition import Composite, Definition, PersonExclusion, Rule, expand_codes
from . import FAMILY_NOTES, LOCATION, SOURCE_TITLE, SOURCE_URL, VERSION

TWO_YEARS = 730


def _d(key, name, row, icd9, icd10, rule, notes="", **kw):
    return Definition(
        id=f"tonelli.{key}",
        name=name,
        version=VERSION,
        source_title=SOURCE_TITLE,
        source_url=SOURCE_URL,
        source_location=LOCATION + row,
        verified=True,
        icd9=expand_codes(icd9),
        icd10ca=expand_codes(icd10),
        rule=rule,
        notes=(notes + " " + FAMILY_NOTES).strip(),
        **kw,
    )


# 1 hospitalization or 2 claims in 2 years or less
HOSP_OR_2_CLAIMS = Rule(min_hospital=1, min_claims=2, window_days=TWO_YEARS)

CIRRHOSIS_DX = _d(
    "cirrhosis_part_dx", "Cirrhosis (diagnosis part)", "Cirrhosis",
    "571.2, 571.5, 571.6",
    "K70.3, K74.3, K74.4, K74.5, K74.6",
    Rule(min_hospital=1, min_claims=1, min_ambulatory=1),
)
CIRRHOSIS_DECOMP = _d(
    "cirrhosis_part_decompensation", "Cirrhosis (hepatic decompensation part)", "Cirrhosis",
    "456.0, 456.1, 456.20, 456.21, 567.0, 567.2, 567.21, 567.29, 567.8, 567.9, 572.2, 572.4, 789.5",
    "I85.0, I85.9, I98.2, I98.3, K65.0, K65.8, K65.9, K67.0, K67.1, K67.2, K67.3, K67.8, K76.7, K93.0, R18",
    Rule(min_hospital=1, min_claims=1, min_ambulatory=1),
    # the table excludes 567.81, 567.82 and 789.51, and says 567.2 was not
    # meant to include 567.22 or 567.23
    excluded_codes=("567.81", "567.82", "789.51", "567.22", "567.23"),
)

DEFINITIONS = [
    _d(
        "alcohol_misuse", "Alcohol misuse", "Alcohol misuse",
        "265.2, 291.1-291.3, 291.5-291.9, 303.0, 303.9, 305.0, 357.5, 425.5, 535.3, 571.0-571.3, 980, V11.3",
        "E52, F10, G62.1, I42.6, K29.2, K70.0, K70.3, K70.9, T51, Z50.2, Z71.4, Z72.1",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "asthma", "Asthma", "Asthma",
        "493", "J45",
        # 1 hospitalization or 3 ACCS in 2 years or less; no physician claims path
        Rule(min_hospital=1, min_claims=None, min_ambulatory=3, window_days=TWO_YEARS),
        "physician claims are not used; the second path is 3 ambulatory records within 2 years.",
    ),
    _d(
        "atrial_fibrillation", "Atrial fibrillation", "Atrial fibrillation",
        "427.31", "I48.0",
        HOSP_OR_2_CLAIMS,
        "the table lists 427.3 with a footnote that 427.31 was not in use in claims, so claims use 427.3 "
        "(which includes atrial flutter). hospital records use 427.31.",
        claims_icd9=("4273",),
    ),
    _d(
        "cancer_lymphoma", "Cancer, lymphoma", "Cancer, lymphoma",
        "200-202, 203.0, 238.6", "C81-C85, C88, C90.0, C90.2, C96",
        HOSP_OR_2_CLAIMS,
        "not permanent in the source: considered to remit after 5 years without claims. casedefs gives "
        "the first date only.",
    ),
    _d(
        "cancer_metastatic", "Cancer, metastatic", "Cancer, metastatic",
        "196-199", "C77-C80",
        HOSP_OR_2_CLAIMS,
        "not permanent in the source (remits after 5 years without claims).",
    ),
    _d(
        "cancer_non_metastatic", "Cancer, non-metastatic (breast, cervical, colorectal, lung, prostate)",
        "Cancer, non-metastatic",
        "153-154, 162-163, 174, 180, 185, 230.3-230.6, 231.2, 233.0-233.1, 233.4",
        "C18-C21, C33-C34, C38.4, C45.0, C46.71, C50, C53, C61, D01.0-D01.3, D02.2, D05-D06, D07.5",
        HOSP_OR_2_CLAIMS,
        "not permanent in the source (remits after 5 years without claims).",
    ),
    _d(
        "chronic_heart_failure", "Chronic heart failure", "Chronic heart failure",
        "398.91, 402.01, 402.11, 402.91, 404.01, 404.03, 404.11, 404.13, 404.91, 404.93, 425.4-425.9, 428",
        "I09.9, I25.5, I42.0, I42.5-I42.9, I43, I50",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "chronic_kidney_disease", "Chronic kidney disease", "Chronic kidney disease",
        "583, 584, 585, 586, 592, 593.9", "N00-N23",
        # or 1 hospitalization or 3 claims in 1 year
        Rule(min_hospital=1, min_claims=3, window_days=365),
        "the lab path (mean eGFR < 60 or mean albuminuria > 30 mg/g over 12 months) is not implemented; "
        "only the diagnosis code path is.",
        complete=False,
    ),
    _d(
        "chronic_pain", "Chronic pain", "Chronic pain",
        "307.80, 307.89, 338.0, 338.2, 338.4, 719.41, 719.45, 719.46, 719.47, 719.49, 720.0, 720.2, 720.9, "
        "721.0, 721.1, 721.2, 721.3, 721.4, 721.6, 721.8, 721.9, 722, 723.0, 723.1, 723.3, 723.4, 723.5, "
        "723.6, 723.7, 723.8, 723.9, 724.0, 724.1, 724.2, 724.3, 724.4, 724.5, 724.6, 724.70, 724.79, "
        "724.8, 724.9, 729.0, 729.1, 729.2, 729.4, 729.5",
        "F45.4, G89.0, G89.2, G89.4, M08.1, M25.50, M25.51, M25.55, M25.56, M25.57, M43.2, M43.3, M43.4, "
        "M43.5, M43.6, M45, M46.1, M46.3, M46.4, M46.9, M47, M48.0, M48.1, M48.8, M48.9, M50.8, M50.9, M51, "
        "M53.1, M53.2, M53.3, M53.8, M53.9, M54, M60.8, M60.9, M63.3, M79.0, M79.1, M79.2, M79.6, M79.7, "
        "M96.1",
        # 2 hospitalizations or 2 claims or 2 ACCS in 30 days or more
        Rule(min_hospital=2, min_claims=2, min_ambulatory=2, min_days_between=30),
        "the corrected table says '30 days or more' (the original said 'or less'), read here as two "
        "records of the same kind at least 30 days apart. not permanent in the source (remits after 2 "
        "years without claims).",
    ),
    _d(
        "chronic_pulmonary_disease", "Chronic pulmonary disease", "Chronic pulmonary disease",
        "416.8, 416.9, 490-492, 494-505, 506.4, 508.1, 508.8",
        "I27.8, I27.9, J40-J44, J46-J47, J60-J67, J68.4, J70.1, J70.3",
        HOSP_OR_2_CLAIMS,
        "493 and J45 were removed by the authors because they belong to asthma.",
    ),
    _d(
        "hepatitis_b", "Chronic viral hepatitis B", "Chronic viral hepatitis B",
        "070.2-070.3", "B16, B18.0-B18.1",
        # 2 hospitalizations or 2 claims or 2 ACCS, within 6 months
        Rule(min_hospital=2, min_claims=2, min_ambulatory=2, window_days=183),
        "the table prints the ICD-9 codes as 70.2-70.3, read as 070.2-070.3 (viral hepatitis B). "
        "6 months is read as 183 days.",
    ),
    Composite(
        id="tonelli.cirrhosis",
        name="Cirrhosis",
        version=VERSION,
        source_title=SOURCE_TITLE,
        source_url=SOURCE_URL,
        source_location=LOCATION + "Cirrhosis",
        verified=True,
        components=(CIRRHOSIS_DX, CIRRHOSIS_DECOMP),
        min_conditions=2,
        notes=(
            "needs both a cirrhosis code and a hepatic decompensation code (each: 1 hospitalization or 1 "
            "claim or 1 ACCS). the case date is when the second of the two is first seen. " + FAMILY_NOTES
        ),
    ),
    _d(
        "dementia", "Dementia", "Dementia",
        "290, 294.1, 331.2", "F00-F03, F05.1, G30, G31.1",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "depression", "Depression", "Depression",
        "296.2, 296.3, 296.5, 300.4, 309, 311",
        "F20.4, F31.3-F31.5, F32, F33, F34.1, F41.2, F43.2",
        HOSP_OR_2_CLAIMS,
        "not permanent in the source (remits after 2 years without claims).",
    ),
    _d(
        "diabetes", "Diabetes", "Diabetes",
        "250", "E10-E14",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "epilepsy", "Epilepsy", "Epilepsy",
        "345", "G40-G41",
        # 1 most responsible hospitalization or 2 claims in 2 years or less or
        # 1 most responsible ACCS
        Rule(min_hospital=1, min_claims=2, min_ambulatory=1, window_days=TWO_YEARS),
        "hospital and ambulatory records count only as the most responsible diagnosis.",
        hospital_dx_types=("M",),
        ambulatory_dx_types=("M",),
    ),
    _d(
        "hypertension", "Hypertension", "Hypertension",
        "401-405", "I10-I13, I15",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "hypothyroidism", "Hypothyroidism", "Hypothyroidism",
        "240.9, 243, 244, 246.1, 246.8", "E00-E03, E89.0",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "inflammatory_bowel_disease", "Inflammatory bowel disease", "Inflammatory bowel disease",
        "555, 556", "K50, K51",
        # 2 hospitalizations or 2 GAST or GP claims in 3 years or less
        Rule(min_hospital=2, min_claims=2, window_days=1095),
        "only gastroenterologist (GAST) or general practitioner (GP) claims count; put those labels in a "
        "specialty column. 3 years is read as 1095 days.",
        claims_specialties=("GAST", "GP"),
    ),
    _d(
        "irritable_bowel_syndrome", "Irritable bowel syndrome", "Irritable bowel syndrome",
        "564.1", "K58",
        HOSP_OR_2_CLAIMS,
        "the 'hospitalization without surgery' condition is not implemented. people with any of the "
        "exclusion codes at any time are not cases (the table does not say when the exclusion applies).",
        complete=False,
        exclusions=(
            PersonExclusion(
                name="other bowel and abdominal disease",
                icd9=expand_codes("153-154, 157, 183.0, 197.5, 198.6, 235.2, 239.0, 555-556, 571.2, 571.5, "
                                  "577.1, 579"),
                icd10ca=expand_codes("C18-C21, C25, C56, C78.5, C79.6, D01.7, D01.9, D37.1-D37.5, K50-K51, "
                                     "K70.2-K70.3, K74.0, K74.2, K74.6, K86.0-K86.1, K90, K91.2"),
                description="any record with these codes, at any time, rules the person out",
            ),
        ),
    ),
    _d(
        "multiple_sclerosis", "Multiple sclerosis", "Multiple sclerosis",
        "323, 340, 341.0, 341.9, 377.3", "G35, G36, G37, H46",
        # 2 hospitalizations or 2 claims in 3 years or less
        Rule(min_hospital=2, min_claims=2, window_days=1095),
        "3 years is read as 1095 days.",
    ),
    _d(
        "myocardial_infarction", "Myocardial infarction", "Myocardial infarction",
        "410", "I21-I22",
        Rule(min_hospital=1, min_claims=None),
        "1 most responsible hospitalization (the correction added 'most responsible').",
        hospital_dx_types=("M",),
    ),
    _d(
        "parkinsons_disease", "Parkinson's disease", "Parkinson's disease",
        "332", "G20, G21, G22",
        Rule(min_hospital=1, min_claims=1),
    ),
    _d(
        "peptic_ulcer_disease", "Peptic ulcer disease", "Peptic ulcer disease",
        "531.7, 531.9, 532.7, 532.9, 533.7, 533.9, 534.7, 534.9",
        "K25.7, K25.9, K26.7, K26.9, K27.7, K27.9, K28.7, K28.9",
        HOSP_OR_2_CLAIMS,
        "not permanent in the source (remits after 2 years without claims).",
    ),
    _d(
        "peripheral_vascular_disease", "Peripheral vascular disease", "Peripheral vascular disease",
        "440.2", "I70.2",
        Rule(min_hospital=1, min_claims=1, min_ambulatory=1),
    ),
    _d(
        "psoriasis", "Psoriasis", "Psoriasis",
        "696.1", "L40.0-L40.4, L40.8, L40.9",
        Rule(min_hospital=1, min_claims=1),
        "only dermatologist (DERM) claims count; put that label in a specialty column.",
        claims_specialties=("DERM",),
    ),
    _d(
        "rheumatoid_arthritis", "Rheumatoid arthritis", "Rheumatoid arthritis",
        "446.5, 710.0-710.4, 714.0-714.2, 714.8, 725",
        "M05, M06, M31.5, M32-M34, M35.1, M35.3, M36.0",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "schizophrenia", "Schizophrenia", "Schizophrenia",
        "295", "F20, F21, F23.2, F25",
        HOSP_OR_2_CLAIMS,
    ),
    _d(
        "severe_constipation", "Severe constipation", "Severe constipation",
        "560.1, 560.30, 560.39, 560.9, 564.0, 569.83, 569.89",
        "K55.8, K56.0, K56.4, K56.7, K59.0, K63.1, K63.4, K63.81, K63.88, K92.80, K92.88",
        HOSP_OR_2_CLAIMS,
        "not implemented: 'hospitalization without surgery', the surgery exclusion from claims, and the "
        "conditional exclusions (560.9 with 789.01, 789.02 or 789.06; K56.6 with R10.1). people with any "
        "of the other exclusion codes at any time are not cases. not permanent in the source.",
        complete=False,
        exclusions=(
            PersonExclusion(
                name="other bowel, abdominal and pelvic disease",
                icd9=expand_codes("152-154, 158, 179-189, 197.5-197.6, 235.2, 239.0, 555-556, 568.0, 614.6"),
                icd10ca=expand_codes("C17-C21, C45.1, C48, C51-C58, C60-C68, C78.5-C78.6, D01.7, D01.9, "
                                     "D37.1-D37.5, K50-K51, K66.0, N73.6, N99.4"),
                description="any record with these codes, at any time, rules the person out",
            ),
        ),
    ),
    _d(
        "stroke_tia", "Stroke or TIA", "Stroke or TIA",
        "362.3, 430, 431, 433.01, 433.11, 433.21, 433.31, 433.41, 433.51, 433.61, 433.71, 433.81, 433.91, "
        "434.01, 434.11, 434.21, 434.31, 434.41, 434.51, 434.61, 434.71, 434.81, 434.91, 435, 436",
        "G45.0-G45.3, G45.8-G45.9, H34.1, I60, I61, I63, I64",
        # 1 most responsible or post-admittance hospitalization or 1 claim or
        # 1 most responsible ED ACCS
        Rule(min_hospital=1, min_claims=1, min_ambulatory=1),
        "433.x1 and 434.x1 are spelled out digit by digit. hospital records count as most responsible "
        "(M) or post-admission (2) diagnoses; ambulatory records as most responsible, and the source "
        "means emergency department records only, so pass ED visits.",
        hospital_dx_types=("M", "2"),
        ambulatory_dx_types=("M",),
    ),
]
