# Contributing

Thanks for helping. The most useful contribution is a new case definition with a solid citation.

## Ground rules

1. **Every code must come from a source you read.** Don't copy codes from memory, from a similar definition, or from an AI tool. If you can't confirm the full code list from a primary source, set `verified=False` and say why in the PR.
2. **Cite the exact location**, such as a table, page, or spreadsheet row, so a reviewer can check each code in a few minutes.
3. **Use synthetic data only.** Never put real patient data in tests, examples or issues, even if it has been de-identified.

## Adding a definition

1. Copy an existing file with a similar rule, for example `src/casedefs/definitions/ccdss/heart_failure.py`. For a new source (not CCDSS), make a new folder such as `src/casedefs/definitions/<source>/`, with an empty `__init__.py`.
2. Fill in the fields:

   ```python
   DEFINITION = Definition(
       id="ccdss.heart_failure",          # <source>.<condition>, lowercase
       name="Heart failure",
       version="v2024",                    # the source's version, not ours
       source_title="...",                 # full citation
       source_url="https://...",
       source_location="table 3, page 12", # where exactly
       verified=True,
       icd9=("428",),                      # prefixes, as published
       icd10ca=("I50",),
       rule=Rule(min_hospital=1, min_claims=2, window_days=365),
       min_age=40,
       exclusions=(),
       notes="how you read anything the source leaves open",
   )
   ```

   - `Rule(min_hospital, min_claims, window_days)` means "at least `min_hospital` hospital records, or at least `min_claims` claims with the first and last no more than `window_days` apart". Use `None` to turn a path off.
   - Write out ranges with `code_range("O21", "O95")` from `casedefs.definition`. Use it only for ranges written that way in the source.
   - Exclusions work like the gestational ones in `definitions/ccdss/__init__.py`, or like the claims-based one in `rheumatoid_arthritis.py`.
   - Other options, each used by an existing file you can copy:
     - `claims_icd9` / `claims_icd10ca`: claims codes that differ from hospital codes (`dementia.py`)
     - `excluded_codes`: a subcode that never counts (`stroke.py`)
     - `Rule(min_days_between=30)`: a minimum gap between claims (`schizophrenia.py`)
     - `Rule(hospital_min_age=20)`: the hospital path only counts from an age (`epilepsy.py`)
     - `hospital_dx_types`, `hospital_date="admission"`: diagnosis types and admission dates (`ami.py`)
     - `procedure_cci` / `procedure_ccp` / `procedure_icd9cm` with `Rule(min_procedures=1)` (`ischemic_heart_disease.py`)
     - `drug_dins` with `Rule(min_drugs=1)` (`dementia.py`)
     - `Composite`: "a case of N of these definitions" (`multimorbidity.py`)

3. The registry finds any module that defines `DEFINITION`, so you don't need to register anything.
4. Add `tests/definitions/test_<condition>.py`. At minimum:
   - a test that checks the codes, rule and ages against the source
   - true cases for each code block, with and without dots
   - near misses: a neighbouring code, one day outside the window, one year under the age limit, an excluded record
5. Add a row to `docs/sources.md` and to the table in `README.md`.
6. Run the tests:

   ```bash
   pip install -e ".[dev]"
   pytest --cov=casedefs
   ```

## If your rule doesn't fit

Some definitions need logic that `Rule` can't express, such as a minimum gap between claims, drug data, or "first diagnosis field only". Open an issue first. We would rather add a small, tested option to the engine than special-case one file.

## Style

- Keep code simple and readable over clever.
- Write comments in lowercase and keep them short. Explain why, not what.
- The PR description should link the source and list anything you had to interpret.
