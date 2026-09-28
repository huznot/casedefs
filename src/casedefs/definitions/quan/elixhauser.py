"""elixhauser comorbidities, quan 2005 table 1 (ICD-10 and enhanced ICD-9-CM columns).

the MCHP copy of the table has a few print errors in the ICD-10 column, read
against the page image: '142.5' is I42.5, 'ROO.O' 'ROO.1' 'ROO.8' are R00.0
R00.1 R00.8, 'Q23.OQ23.3' is Q23.0-Q23.3, 'G 13.x' is G13.x, 'NI9.x' is N19.x,
'Z1 99.2' (a footnote mark) is Z99.2, and '127.9' is I27.9.
"""

from . import quan

URL = "http://mchp-appserv.cpe.umanitoba.ca/concept/Elixhauser%20Comorbidities%20-%20Coding%20Algorithms%20for%20ICD-9-CM%20and%20ICD-10.pdf"


def _e(key, name, icd10, icd9, notes=""):
    return quan("elixhauser", key, name, URL, icd10, icd9, notes)


DEFINITIONS = [
    _e(
        "congestive_heart_failure", "Congestive heart failure",
        "I09.9, I11.0, I13.0, I13.2, I25.5, I42.0, I42.5-I42.9, I43.x, I50.x, P29.0",
        "398.91, 402.01, 402.11, 402.91, 404.01, 404.03, 404.11, 404.13, 404.91, 404.93, 425.4-425.9, 428.x",
    ),
    _e(
        "cardiac_arrhythmias", "Cardiac arrhythmias",
        "I44.1-I44.3, I45.6, I45.9, I47.x-I49.x, R00.0, R00.1, R00.8, T82.1, Z45.0, Z95.0",
        "426.0, 426.13, 426.7, 426.9, 426.10, 426.12, 427.0-427.4, 427.6-427.9, 785.0, 996.01, 996.04, V45.0, "
        "V53.3",
    ),
    _e(
        "valvular_disease", "Valvular disease",
        "A52.0, I05.x-I08.x, I09.1, I09.8, I34.x-I39.x, Q23.0-Q23.3, Z95.2, Z95.4",
        "093.2, 394.x-397.x, 424.x, 746.3-746.6, V42.2, V43.3",
    ),
    _e(
        "pulmonary_circulation_disorders", "Pulmonary circulation disorders",
        "I26.x, I27.x, I28.0, I28.8, I28.9",
        "415.0, 415.1, 416.x, 417.0, 417.8, 417.9",
    ),
    _e(
        "peripheral_vascular_disorders", "Peripheral vascular disorders",
        "I70.x, I71.x, I73.1, I73.8, I73.9, I77.1, I79.0, I79.2, K55.1, K55.8, K55.9, Z95.8, Z95.9",
        "093.0, 437.3, 440.x, 441.x, 443.1-443.9, 447.1, 557.1, 557.9, V43.4",
    ),
    _e("hypertension_uncomplicated", "Hypertension, uncomplicated", "I10.x", "401.x"),
    _e("hypertension_complicated", "Hypertension, complicated", "I11.x-I13.x, I15.x", "402.x-405.x"),
    _e(
        "paralysis", "Paralysis",
        "G04.1, G11.4, G80.1, G80.2, G81.x, G82.x, G83.0-G83.4, G83.9",
        "334.1, 342.x, 343.x, 344.0-344.6, 344.9",
    ),
    _e(
        "other_neurological_disorders", "Other neurological disorders",
        "G10.x-G13.x, G20.x-G22.x, G25.4, G25.5, G31.2, G31.8, G31.9, G32.x, G35.x-G37.x, G40.x, G41.x, "
        "G93.1, G93.4, R47.0, R56.x",
        "331.9, 332.0, 332.1, 333.4, 333.5, 333.92, 334.x-335.x, 336.2, 340.x, 341.x, 345.x, 348.1, 348.3, "
        "780.3, 784.3",
    ),
    _e(
        "chronic_pulmonary_disease", "Chronic pulmonary disease",
        "I27.8, I27.9, J40.x-J47.x, J60.x-J67.x, J68.4, J70.1, J70.3",
        "416.8, 416.9, 490.x-505.x, 506.4, 508.1, 508.8",
    ),
    _e(
        "diabetes_uncomplicated", "Diabetes, uncomplicated",
        "E10.0, E10.1, E10.9, E11.0, E11.1, E11.9, E12.0, E12.1, E12.9, E13.0, E13.1, E13.9, E14.0, E14.1, "
        "E14.9",
        "250.0-250.3",
    ),
    _e(
        "diabetes_complicated", "Diabetes, complicated",
        "E10.2-E10.8, E11.2-E11.8, E12.2-E12.8, E13.2-E13.8, E14.2-E14.8",
        "250.4-250.9",
    ),
    _e("hypothyroidism", "Hypothyroidism", "E00.x-E03.x, E89.0", "240.9, 243.x, 244.x, 246.1, 246.8"),
    _e(
        "renal_failure", "Renal failure",
        "I12.0, I13.1, N18.x, N19.x, N25.0, Z49.0-Z49.2, Z94.0, Z99.2",
        "403.01, 403.11, 403.91, 404.02, 404.03, 404.12, 404.13, 404.92, 404.93, 585.x, 586.x, 588.0, V42.0, "
        "V45.1, V56.x",
    ),
    _e(
        "liver_disease", "Liver disease",
        "B18.x, I85.x, I86.4, I98.2, K70.x, K71.1, K71.3-K71.5, K71.7, K72.x-K74.x, K76.0, K76.2-K76.9, Z94.4",
        "070.22, 070.23, 070.32, 070.33, 070.44, 070.54, 070.6, 070.9, 456.0-456.2, 570.x, 571.x, "
        "572.2-572.8, 573.3, 573.4, 573.8, 573.9, V42.7",
    ),
    _e(
        "peptic_ulcer_disease", "Peptic ulcer disease excluding bleeding",
        "K25.7, K25.9, K26.7, K26.9, K27.7, K27.9, K28.7, K28.9",
        "531.7, 531.9, 532.7, 532.9, 533.7, 533.9, 534.7, 534.9",
    ),
    _e("aids_hiv", "AIDS/HIV", "B20.x-B22.x, B24.x", "042.x-044.x"),
    _e("lymphoma", "Lymphoma", "C81.x-C85.x, C88.x, C96.x, C90.0, C90.2", "200.x-202.x, 203.0, 238.6"),
    _e("metastatic_cancer", "Metastatic cancer", "C77.x-C80.x", "196.x-199.x"),
    _e(
        "solid_tumor_without_metastasis", "Solid tumor without metastasis",
        "C00.x-C26.x, C30.x-C34.x, C37.x-C41.x, C43.x, C45.x-C58.x, C60.x-C76.x, C97.x",
        "140.x-172.x, 174.x-195.x",
    ),
    _e(
        "rheumatoid_arthritis_collagen_vascular", "Rheumatoid arthritis/collagen vascular diseases",
        "L94.0, L94.1, L94.3, M05.x, M06.x, M08.x, M12.0, M12.3, M30.x, M31.0-M31.3, M32.x-M35.x, M45.x, "
        "M46.1, M46.8, M46.9",
        "446.x, 701.0, 710.0-710.4, 710.8, 710.9, 711.2, 714.x, 719.3, 720.x, 725.x, 728.5, 728.89, 729.30",
    ),
    _e("coagulopathy", "Coagulopathy", "D65-D68.x, D69.1, D69.3-D69.6", "286.x, 287.1, 287.3-287.5"),
    _e("obesity", "Obesity", "E66.x", "278.0"),
    _e("weight_loss", "Weight loss", "E40.x-E46.x, R63.4, R64", "260.x-263.x, 783.2, 799.4"),
    _e("fluid_electrolyte_disorders", "Fluid and electrolyte disorders", "E22.2, E86.x, E87.x", "253.6, 276.x"),
    _e("blood_loss_anemia", "Blood loss anemia", "D50.0", "280.0"),
    _e("deficiency_anemia", "Deficiency anemia", "D50.8, D50.9, D51.x-D53.x", "280.1-280.9, 281.x"),
    _e(
        "alcohol_abuse", "Alcohol abuse",
        "F10, E52, G62.1, I42.6, K29.2, K70.0, K70.3, K70.9, T51.x, Z50.2, Z71.4, Z72.1",
        "265.2, 291.1-291.3, 291.5-291.9, 303.0, 303.9, 305.0, 357.5, 425.5, 535.3, 571.0-571.3, 980.x, V11.3",
    ),
    _e(
        "drug_abuse", "Drug abuse",
        "F11.x-F16.x, F18.x, F19.x, Z71.5, Z72.2",
        "292.x, 304.x, 305.2-305.9, V65.42",
    ),
    _e(
        "psychoses", "Psychoses",
        "F20.x, F22.x-F25.x, F28.x, F29.x, F30.2, F31.2, F31.5",
        "293.8, 295.x, 296.04, 296.14, 296.44, 296.54, 297.x, 298.x",
    ),
    _e(
        "depression", "Depression",
        "F20.4, F31.3-F31.5, F32.x, F33.x, F34.1, F41.2, F43.2",
        "296.2, 296.3, 296.5, 300.4, 309.x, 311",
    ),
]
