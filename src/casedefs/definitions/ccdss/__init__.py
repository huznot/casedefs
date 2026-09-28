"""shared source details for the ccdss definitions."""

from ...definition import Exclusion, code_range

SOURCE_TITLE = (
    "Public Health Agency of Canada. Canadian Chronic Disease Surveillance System (CCDSS) "
    "Disease-Specific Case Definitions, v2024 (last modified November 19, 2025)"
)
SOURCE_URL = "https://health-infobase.canada.ca/ccdss/publication/CCDSS_Case_Definitions_v2024.xlsx"
VERSION = "v2024"


def row(n: int) -> str:
    return f"sheet 'CCDSS Case definitions (GRID)', row {n}"


# pregnancy and obstetrical codes, from the special exclusions column (AC)
# of the diabetes (row 6) and hypertension (row 14) rows. the source lists
# ICD-9 as 641-676, V27 and ICD-9-CM as 641-679, V27. we use the ICD-9-CM
# range: 677-679 do not exist in ICD-9, so this is the same for ICD-9 data.
PREGNANCY_ICD9 = code_range("641", "679") + ("V27",)
PREGNANCY_ICD10CA = code_range("O10", "O16") + code_range("O21", "O95") + ("O98", "O99", "Z37")


def pregnancy_exclusion(min_age: int, max_age: int, condition: str) -> Exclusion:
    return Exclusion(
        name=f"gestational {condition}",
        icd9=PREGNANCY_ICD9,
        icd10ca=PREGNANCY_ICD10CA,
        days_before=120,
        days_after=180,
        sex="F",
        min_age=min_age,
        max_age=max_age,
        description=(
            f"women aged {min_age} to {max_age} cannot qualify as incident {condition} cases "
            f"120 days before and up to 180 days following a hospital record with a "
            f"pregnancy-related or obstetrical code"
        ),
    )
