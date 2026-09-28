"""shared source details for the quan 2005 charlson and elixhauser definitions."""

from ...definition import Definition, Rule, expand_codes

SOURCE_TITLE = (
    "Quan H, Sundararajan V, Halfon P, et al. Coding algorithms for defining comorbidities in ICD-9-CM and "
    "ICD-10 administrative data. Med Care. 2005;43(11):1130-9. Table 1 (ICD-10 and enhanced ICD-9-CM "
    "columns), as reproduced by the Manitoba Centre for Health Policy"
)
VERSION = "2005"

FAMILY_NOTES = (
    "comorbidity flag from hospital discharge abstracts, any diagnosis field. the source defines codes, "
    "not a claims rule, so physician claims are not used here (see casedefs.comorbidity_score for an "
    "option to include them)."
)


def quan(family, key, name, url, icd10, icd9, extra_notes=""):
    return Definition(
        id=f"quan.{family}.{key}",
        name=name,
        version=VERSION,
        source_title=SOURCE_TITLE,
        source_url=url,
        source_location=f"Table 1, {name}",
        verified=True,
        icd9=expand_codes(icd9),
        icd10ca=expand_codes(icd10),
        rule=Rule(min_hospital=1, min_claims=None),
        notes=(extra_notes + " " + FAMILY_NOTES).strip(),
    )
