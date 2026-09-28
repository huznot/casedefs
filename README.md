# casedefs

**apply published, validated health case definitions to physician claims and hospital data, with every code traced back to its source.**

researchers often retype case definitions by hand from pdfs, and small mistakes slip in: a missing code, a 2 year window read as 2 calendar years, a forgotten gestational exclusion. casedefs keeps each definition as a small, tested, versioned file with a citation, and applies it the same way every time.

## install

```bash
pip install casedefs
```

needs python 3.10+. the only dependencies are pandas and typer.

## quick start

```python
import pandas as pd
from casedefs import apply

claims = pd.read_csv("claims.csv", dtype=str)      # person_id, service_date, dx_code
hospital = pd.read_csv("hospital.csv", dtype=str)  # person_id, separation_date, dx_code_1..n
people = pd.read_csv("people.csv", dtype=str)      # person_id, birth_date, sex
cases = apply("ccdss.diabetes", claims=claims, hospital=hospital, people=people)
```

you get one row per case:

| person_id | case_date | definition_id | definition_version |
|---|---|---|---|
| P003 | 2017-08-02 | ccdss.diabetes | v2024 |
| P001 | 2020-01-15 | ccdss.diabetes | v2024 |

`case_date` is the date the definition was first met.

you can also pass a list of ids, or `"all"`:

```python
cases = apply("all", claims=claims, hospital=hospital, people=people)
```

to try it on made up data, run `python examples/run_example.py`.

## command line

```bash
casedefs list                   # every definition, its version and source
casedefs show ccdss.diabetes    # codes, rule, ages, exclusions, citation
casedefs run ccdss.diabetes --claims examples/claims.csv --hospital examples/hospital.csv --people examples/people.csv -o cases.csv
casedefs run all --claims examples/claims.csv --hospital examples/hospital.csv --people examples/people.csv \
    --procedures examples/procedures.csv --drugs examples/drugs.csv -o all_cases.csv
```

if your columns have other names, map them instead of renaming:

```bash
casedefs run ccdss.copd --claims ohip.csv --map person_id=IKN --map service_date=svc_dt --map dx_code=dx -o copd.csv
```

## definitions

all 21 come from the public health agency of canada's [ccdss disease-specific case definitions, v2024](https://health-infobase.canada.ca/ccdss/publication/CCDSS_Case_Definitions_v2024.xlsx) (last modified november 19, 2025). every code was checked against that file. [docs/sources.md](docs/sources.md) has the row for each one, and `casedefs show <id>` prints the full code lists.

| id | condition | rule | ages |
|---|---|---|---|
| `ccdss.diabetes` | diabetes, excluding gestational | 1 hospital or 2 claims in 2 years | 1+ |
| `ccdss.hypertension` | hypertension, excluding gestational | 1 hospital or 2 claims in 2 years | 20+ |
| `ccdss.heart_failure` | heart failure | 1 hospital or 2 claims in 1 year | 40+ |
| `ccdss.ischemic_heart_disease` | ischemic heart disease | 1 hospital, 1 procedure, or 2 claims in 1 year | 20+ |
| `ccdss.ami` | acute myocardial infarction | 1 hospital admission (main diagnosis types) | 20+ |
| `ccdss.stroke` | stroke | 1 hospital or 2 claims in 1 year | 20+ |
| `ccdss.asthma` | asthma | 1 hospital or 2 claims in 2 years | 1+ |
| `ccdss.copd` | copd | 1 hospital or 1 claim | 35+ |
| `ccdss.dementia` | dementia, including alzheimer disease | 1 hospital, 1 drug, or 3 claims in 2 years, 30+ days apart | 65+ |
| `ccdss.epilepsy` | epilepsy | 3 claims in 2 years, 30+ days apart, or 1 hospital (20+ only) | 1+ |
| `ccdss.multiple_sclerosis` | multiple sclerosis | 1 hospital or 5 claims in 2 years | 20+ |
| `ccdss.parkinsonism` | parkinsonism, including parkinson disease | 2 claims in 1 year, 30+ days apart | 40+ |
| `ccdss.schizophrenia` | schizophrenia | 1 hospital or 2 claims in 2 years, 30+ days apart | 10+ |
| `ccdss.autism` | autism | 1 hospital or 2 claims | 1 to 19 |
| `ccdss.osteoarthritis` | osteoarthritis | 1 hospital or 2 claims in 5 years, on different days | 20+ |
| `ccdss.rheumatoid_arthritis` | rheumatoid arthritis | 1 hospital or 2 claims in 2 years, over 8 weeks apart, minus other inflammatory arthritis | 16+ |
| `ccdss.juvenile_idiopathic_arthritis` | juvenile idiopathic arthritis | 1 hospital or 2 claims in 2 years, over 8 weeks apart | up to 15 |
| `ccdss.gout` | gout and other crystal arthropathies | 1 hospital or 2 claims in 5 years, on different days | 20+ |
| `ccdss.osteoporosis` | osteoporosis | 1 hospital or 1 claim | 40+ |
| `ccdss.multimorbidity_2plus` | 2 or more of 16 chronic conditions | case of 2 of the 16 | 35+ |
| `ccdss.multimorbidity_3plus` | 3 or more of 16 chronic conditions | case of 3 of the 16 | 35+ |

all 21 are marked verified. the ones where the source leaves room for interpretation are listed below.

cite as: public health agency of canada. *canadian chronic disease surveillance system (ccdss) disease-specific case definitions*, v2024. health infobase.

## input data

| table | columns | notes |
|---|---|---|
| claims | `person_id`, `service_date`, `dx_code` | one row per claim. icd-9 by default |
| hospital | `person_id`, a date, and codes | wide (`dx_code_1`, `dx_code_2`, ...) or long (`dx_code`). icd-10-ca by default |
| people | `person_id`, `birth_date`, `sex` (optional) | needed for age limits and gestational exclusions |
| procedures | `person_id`, `procedure_date`, `proc_code` | only for ischemic heart disease. cci by default |
| drugs | `person_id`, `dispense_date`, `din` | only for dementia |

- **hospital dates**: `separation_date`, `admit_date` or `date`. give both separation and admission if you have them, since ami and osteoporosis count from admission.
- **diagnosis types**: for ami, add `dx_type_1`, `dx_type_2`, ... (or `dx_type` in long format) with values like `M` (or `MRDx`), `1`, `2`, `3`, `W`. without them every field is used and you get a warning.
- **codes**: dots, spaces and case don't matter, and codes match by prefix. `250` matches `250.1`, and `E11` matches `E11.9`.
- **mixed icd versions**: add an `icd_version` column (9 or 10), or pass `hospital_coding="both"`. for procedures, use `procedure_coding` or a `proc_system` column (`cci`, `ccp`, `icd9cm`).
- **column names**: `columns={"person_id": "PHN"}`. for wide hospital data with other names: `columns={"hospital_dx_columns": ["DIAG1", "DIAG2"]}` (cli: `--hospital-dx DIAG1,DIAG2`).
- **dates**: iso dates just work. for anything else pass `date_format="%d/%m/%Y"`. blank or unreadable dates raise an error that names the rows.
- **warnings**: you get a warning when a check can't be done, like an age limit with no people table.

it's fast enough for full provincial extracts: all 21 definitions on 2 million claims take about 13 seconds on a laptop.

## how rules are read

- "within 2 years" is 730 days and "within 1 year" is 365, counted from first to last claim. 5 years is 1825 days.
- "more than 8 weeks apart" is at least 57 days.
- the case date is the earliest of: the hospital date, the procedure or drug date, or the claim that completes the claims rule.
- age limits use age on the case date.
- gestational exclusions: a woman in the age band can't qualify on a date from 120 days before to 180 days after a hospital record with a pregnancy code. she can still qualify on a later date.
- rheumatoid arthritis: the ccdss sets its case date 730 days after qualifying. casedefs uses the qualifying date instead, and still applies the exclusion.
- physician claims should hold the first diagnosis field only when the source says "first" (asthma, copd, stroke, the arthritis definitions and others). `casedefs show` says which.

[docs/sources.md](docs/sources.md) lists every interpretation, plus a few known differences from older phac publications.

## disclaimer

casedefs is a research tool. it applies published definitions as written, but provinces differ in coding, billing rules, diagnostic fields and data coverage. **you are responsible for checking that the results are valid for your data, province and study period**, for example by comparing against published counts. the validation studies behind these definitions used specific populations and may not carry over to yours. this is not a clinical tool.

## contributing

new definitions are welcome. each one is one file with its source. see [CONTRIBUTING.md](CONTRIBUTING.md).

## license

mit
