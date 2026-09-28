from ...definition import Definition, Rule, code_range
from . import SOURCE_TITLE, SOURCE_URL, VERSION, row

DEFINITION = Definition(
    id="ccdss.ischemic_heart_disease",
    name="Ischemic heart disease (IHD)",
    version=VERSION,
    source_title=SOURCE_TITLE,
    source_url=SOURCE_URL,
    source_location=row(15) + "; procedure codes from footnote c (row 51)",
    verified=True,
    icd9=code_range("410", "414"),
    icd10ca=code_range("I20", "I25"),
    # percutaneous coronary intervention and coronary artery bypass graft
    procedure_icd9cm=("36.01", "36.02", "36.05", "36.10", "36.11", "36.12", "36.13", "36.14", "36.15",
                      "36.16", "36.17", "36.19"),
    procedure_ccp=("48.02", "48.03", "48.11", "48.12", "48.13", "48.14", "48.15", "48.16", "48.17",
                   "48.19"),
    procedure_cci=("1.IJ.50", "1.IJ.57.GQ", "1.IJ.54", "1.IJ.76"),
    # one or more hospital separation records or procedure code, or two or
    # more physician claims within one year
    rule=Rule(min_hospital=1, min_claims=2, window_days=365, min_procedures=1),
    min_age=20,
    notes=(
        "the procedure path needs a procedures table (person_id, procedure_date, proc_code) with "
        "codes in CCI by default, or set procedure_coding / a proc_system column for CCP or "
        "ICD-9-CM. all hospital and all physician diagnosis fields are used. case date is the "
        "hospital record, procedure or second physician claim, whichever comes first."
    ),
)
