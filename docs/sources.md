# Sources

Every code in casedefs comes from a source someone read. This file records where, so anyone can check.

## CCDSS (Public Health Agency of Canada)

**Primary source:** CCDSS Disease-Specific Case Definitions, v2024 spreadsheet.
- URL: https://health-infobase.canada.ca/ccdss/publication/CCDSS_Case_Definitions_v2024.xlsx
- Linked from: https://health-infobase.canada.ca/ccdss/Methods ("CCDSS case definitions documentation")
- Sheet: `CCDSS Case definitions (GRID)`. The header says "Data up to 2022-2023" and "Last modified: November 19, 2025".
- Read on: 2026-09-27

Columns used: C (case definition), D/E/F (hospital / physician / other counts), M (case date), N to W (ICD codes and digits), X (other data), Y/Z (diagnostic fields), AB (ages), AC (special exclusions), AD (notes). Footnotes are in rows 49 to 62.

| casedefs id | Row | Hospital ICD-9 | Hospital ICD-10-CA | Physician ICD-9 (if different) | Rule | Ages | Physician dx field |
|---|---|---|---|---|---|---|---|
| ccdss.diabetes | 6 | 250 | E10, E11, E13, E14 | | 1+ hosp or 2+ claims within 2 years | 1+ | All |
| ccdss.schizophrenia | 9 | 295 | F20, F21, F23, F25 | | 1+ hosp or 2+ claims within 2 years, 30 days between each | 10+ | First |
| ccdss.asthma | 11 | 493 | J45, J46 | | 1+ hosp or 2+ claims within 2 years | 1+ | First |
| ccdss.copd | 13 | 491, 492, 496 | J41, J42, J43, J44 | | 1+ hosp or 1+ claim | 35+ | First |
| ccdss.hypertension | 14 | 401 to 405 | I10, I11, I12, I13, I15 | | 1+ hosp or 2+ claims within 2 years | 20+ | All |
| ccdss.ischemic_heart_disease | 15 | 410 to 414 | I20 to I25 | | 1+ hosp or procedure (footnote c), or 2+ claims within 1 year | 20+ | All |
| ccdss.ami | 16 | 410 | I21, I22 | (no claims) | 1+ hospital admission; dx types MRDx, W, X, Y, 1, 2 (footnote d) | 20+ | n/a |
| ccdss.heart_failure | 18 | 428 | I50 | | 1+ hosp or 2+ claims within 1 year | 40+ | All |
| ccdss.stroke | 19 | 325, 362.3x, 430, 431, 432.9, 433.x1, 434 (or 434.x1), 435.x, 436, 437.6 | G08, G45.x (exclude G45.4), H34.0, H34.1, I60.x, I61.x, I62.9, I63.x, I64, I67.6 | 325, 430, 431, 432.9, 434, 435, 436, 437.6 | 1+ hosp or 2+ claims within 1 year | 20+ | First |
| ccdss.dementia | 21 | 046.1, 290.0 to 290.4, 294.1, 294.2, 331.0, 331.1, 331.5 (or 331.82 in ICD-9-CM) | G30, F00, F01, F02, F03 | 290, 331 (298 in SK only) | 1+ hosp, or 3+ claims within 2 years 30 days between each, or 1+ Rx (footnote f) | 65+ | All |
| ccdss.epilepsy | 22 | 345.0, 345.1, 345.4 to 345.9 | G40 | 345 | ages 1 to 19: 3+ claims within 2 years, 30 days between each. ages 20+: that or 1+ hosp | 1+ | All |
| ccdss.multiple_sclerosis | 24 | 340 | G35 | | 1+ hosp or 5+ claims within 2 years | 20+ | All |
| ccdss.parkinsonism | 25 | (not used) | (not used) | 332; ICD-10-CA F02.3, G20, G21, G22 | 2+ claims within 1 year, 30 days between first and second | 40+ | All |
| ccdss.osteoporosis | 26 | 733 (4 digits, see below) | M80, M81 | 733 (3 digits) | 1+ hosp or 1+ claim | 40+ | First |
| ccdss.osteoarthritis | 36 | 715 | M15 to M19 | | 1+ hosp or 2+ claims (at least 1 day apart) within 5 years | 20+ | First |
| ccdss.rheumatoid_arthritis | 37 | 714 | M05, M06 | | 1+ hosp or 2+ claims (> 8 weeks apart) within 2 years, with exclusion | 16+ | First |
| ccdss.gout | 38 | 274, 712 | M10, M11 | | 1+ hosp or 2+ claims (at least 1 day apart) within 5 years | 20+ | First |
| ccdss.juvenile_idiopathic_arthritis | 40 | 714, 720 | M05, M06, M07.0 to M07.3, M08, M45 | 714, 720 (721 in ON only) | 1+ hosp or 2+ claims (> 8 weeks apart) within 2 years | 15 and under | First |
| ccdss.multimorbidity_2plus | 42 | | | | case of 2+ of the 16 conditions listed in column AD | 35+ | |
| ccdss.multimorbidity_3plus | 43 | | | | case of 3+ of the same 16 | 35+ | |
| ccdss.autism | 44 | 299 | F84 | | 1+ hosp or 2+ claims | 1 to 19 | First |

Hospital records use all diagnosis fields for every definition except AMI.

Other text used verbatim from the source:

- **Pregnancy codes** for the gestational exclusions (column AC, rows 6 and 14): "ICD-9: 641-676, V27 / ICD-9-CM: 641-679, V27 / ICD-10 and ICD-10-CA: O10-16, O21-95, O98, O99, Z37". The window is 120 days before to 180 days after the hospital record. The age band is 10 to 54 for diabetes and 20 to 54 for hypertension.
- **IHD procedures** (footnote c): ICD-9-CM 36.01, 36.02, 36.05, 36.10 to 36.17, 36.19. CCP 48.02, 48.03, 48.11 to 48.17, 48.19. CCI 1.IJ.50, 1.IJ.57.GQ, 1.IJ.54, 1.IJ.76.
- **AMI diagnosis types** (footnote d): MRDx, service transfer types W, X, Y, and types 1 and 2.
- **Dementia drugs** (footnote f): 223 DINs, copied by script into `src/casedefs/definitions/ccdss/_dementia_dins.py`.
- **RA exclusion** (column AC, row 37). ICD-9: 710, 446, 725, 696, 720, 713. ICD-10-CA: M32.1, M32.8, M32.9, M33.x, M34.x, M35.1, M35.8, M35.9, M30.x to M31.x, M35.3, L40.5, M07.0 to M07.3, M45.x, M46.1, M46.8, M46.9, M07.4 to M07.6. The two claims must share a code at 3 characters for ICD-9 and 4 for ICD-10-CA.

## How casedefs reads the source

The spreadsheet does not spell these out. They are interpretations, and each one is also in the definition's `notes`.

1. **Windows.** "Within one / two / five years" is 365 / 730 / 1825 days from the first claim to the last.
2. **Minimum gaps.** "More than 8 weeks apart" is at least 57 days. "Separated by at least 1 day" means different days. "30 days between each claim" applies to every pair of consecutive claims used.
3. **Case date.** The case date is the earliest of the hospital date, the procedure or drug date, and the claim that completes the claims rule.
4. **Age limits** apply to age on the case date. For epilepsy, the hospital path counts from age 20 on the hospital date.
5. **Gestational exclusion.** This follows the v2024 wording ("cannot qualify as incident cases ... 120 days before and up to 180 days following"). A case date inside the window is rejected, but the person can still qualify later. Records are not deleted. ICD-9 pregnancy codes use the ICD-9-CM range 641-679. Codes 677 to 679 do not exist in ICD-9, so ICD-9 data gives the same result. When sex is unknown, the exclusion still applies.
6. **Duplicate claims.** Exact duplicates (same person, date and code) count once.
7. **Osteoporosis hospital ICD-9.** Row 26 lists 733 at 4 digits. Footnote h gives the hospital osteoporosis code as 733.0, so hospital records use 733.0. Physician claims use 733 at 3 digits, as listed.
8. **Stroke.**
   - ICD-9 434 is matched as a 3-digit prefix. The source adds "(or 434.x1)" for ICD-9-CM, and casedefs does not narrow to that.
   - 433.x1 is written out as 433.01, 433.11, ... 433.91.
   - Footnote e says 432.9 and I62.9 are only collected before 2015/16. casedefs keeps them for all years.
9. **Dementia.** Both 331.5 and 331.82 are included for hospital ICD-9. In ICD-9-CM, 331.5 is normal pressure hydrocephalus, so check this if your hospital data is ICD-9-CM. Saskatchewan's extra 298 code is not included.
10. **Rheumatoid arthritis.**
    - The CCDSS sets its RA case date 730 days after the hospital record or the last claim. casedefs returns the date the rule is first met.
    - The exclusion looks at claims on or after that date, anywhere in the data. A person is excluded if any two such claims fall within 730 days of each other.
11. **Juvenile idiopathic arthritis.** Ontario's extra 721 code is not included.
12. **AMI.** casedefs returns the first AMI admission. The CCDSS also reports AMI events per year, which casedefs does not do.
13. **Multimorbidity.** Each of the 16 conditions uses its own casedefs definition, with its own age limits. The case date is when the person meets the 2nd (or 3rd) condition, and they must be 35+ on that date.

## Not included from this source

- **"Active" and "annual" measures:** asthma (active), epilepsy (active), gout (active), AMI (annual), hospitalized stroke, and the three "use of health services" mental health rows. These count people per year, not who has the condition.
- **Osteoporosis fracture and care gap measures (rows 27 to 35):** these count fracture episodes and follow-up care, not cases.

## Cross-check against a second source (diabetes only)

The 2019 PHAC article "At-a-glance: Twenty years of diabetes surveillance using the CCDSS" (https://www.canada.ca/en/public-health/services/reports-publications/health-promotion-chronic-disease-prevention-canada-research-policy-practice/vol-39-no-11-2019/twenty-years-diabetes-surveillance.html) agrees on the rule, the ages and the 120 days before. It differs in three places:

- It lists ICD-10-CA **E12** as well. The v2024 spreadsheet does not.
- It gives **190** days after the pregnancy record. The spreadsheet says 180.
- It says diabetes **records are removed** in the window. The spreadsheet says people "cannot qualify" in the window.

casedefs follows the v2024 spreadsheet, the newer and official definitions document. If you need to match results published around 2019, check these three points.
