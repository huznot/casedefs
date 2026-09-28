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

you can also pass a list of ids, a whole source like `"tonelli.*"`, or `"all"`:

```python
cases = apply("tonelli.*", claims=claims, hospital=hospital, people=people)
```

and charlson or elixhauser comorbidity scores, one row per person:

```python
from casedefs import comorbidity_score

scores = comorbidity_score("charlson", hospital=hospital, index_dates=index_dates, lookback_days=365)
```

to try it on made up data, run `python examples/run_example.py`.

## command line

```bash
casedefs list                   # all 99 definitions
casedefs list --source tonelli  # just one source
casedefs show ccdss.diabetes    # codes, rule, ages, exclusions, citation
casedefs run ccdss.diabetes --claims examples/claims.csv --hospital examples/hospital.csv --people examples/people.csv -o cases.csv
casedefs run all --claims examples/claims.csv --hospital examples/hospital.csv --people examples/people.csv \
    --procedures examples/procedures.csv --drugs examples/drugs.csv -o all_cases.csv
casedefs score charlson --hospital examples/hospital.csv -o charlson.csv
```

if your columns have other names, map them instead of renaming:

```bash
casedefs run ccdss.copd --claims ohip.csv --map person_id=IKN --map service_date=svc_dt --map dx_code=dx -o copd.csv
```

## definitions

99 definitions from four canadian sources. every code was read from the source and every definition cites where it came from. [docs/definitions.md](docs/definitions.md) lists all of them with their codes, and `casedefs show <id>` prints one.

| source | ids | count | what it is |
|---|---|---|---|
| [phac ccdss case definitions, v2024](https://health-infobase.canada.ca/ccdss/publication/CCDSS_Case_Definitions_v2024.xlsx) | `ccdss.*` | 21 | national chronic disease surveillance definitions |
| [tonelli et al. 2015](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-015-0155-5), with the [2019 correction](https://bmcmedinformdecismak.biomedcentral.com/articles/10.1186/s12911-019-0900-2) | `tonelli.*` | 30 | validated algorithms for 30 chronic conditions, alberta |
| [quan et al. 2005](https://pubmed.ncbi.nlm.nih.gov/16224307/), charlson | `quan.charlson.*` | 17 | charlson comorbidities for hospital data, with scores |
| [quan et al. 2005](https://pubmed.ncbi.nlm.nih.gov/16224307/), elixhauser | `quan.elixhauser.*` | 31 | elixhauser comorbidities for hospital data |

**ccdss** (the national surveillance definitions): diabetes, hypertension, heart failure, ischemic heart disease, acute mi, stroke, asthma, copd, dementia, epilepsy, multiple sclerosis, parkinsonism, schizophrenia, autism, osteoarthritis, rheumatoid arthritis, juvenile idiopathic arthritis, gout, osteoporosis, and multimorbidity (2+ and 3+ of 16 conditions).

**tonelli** (the alberta multimorbidity set): alcohol misuse, asthma, atrial fibrillation, three cancer groups, chronic heart failure, chronic kidney disease, chronic pain, chronic pulmonary disease, cirrhosis, dementia, depression, diabetes, epilepsy, hepatitis b, hypertension, hypothyroidism, inflammatory bowel disease, irritable bowel syndrome, multiple sclerosis, myocardial infarction, parkinson's disease, peptic ulcer disease, peripheral vascular disease, psoriasis, rheumatoid arthritis, schizophrenia, severe constipation, stroke or tia.

**quan**: the 17 charlson and 31 elixhauser comorbidities, as icd-10 and enhanced icd-9-cm code lists. the charlson icd-10 codes are also checked against quan's own sas code.

some conditions appear in more than one source with different rules, for example `ccdss.diabetes` and `tonelli.diabetes`. that's on purpose: pick the one your study cites.

three tonelli definitions are only partly implemented, and `casedefs list` marks them with a `*`:
- chronic kidney disease: the lab path (egfr, albuminuria) isn't implemented
- irritable bowel syndrome and severe constipation: the "without surgery" and conditional exclusions aren't implemented

you get a warning whenever you use one of these.

cite the source of each definition you use, not casedefs. the citation is in `casedefs show <id>`.

## comorbidity scores

```python
comorbidity_score("charlson", hospital=hospital)               # weighted charlson score
comorbidity_score("elixhauser", hospital=hospital)             # count of elixhauser conditions
comorbidity_score("charlson", hospital=hospital,
                  index_dates=index_dates, lookback_days=365)  # only the year before each index date
comorbidity_score("charlson", hospital=hospital, claims=claims, include_claims=True)
```

you get one row per person, with a 0/1 column for each condition plus `score`. charlson weights are 1 for the first ten conditions, 2 for diabetes with complications, hemiplegia, renal disease and malignancy, 3 for moderate or severe liver disease, and 6 for metastatic tumor and aids/hiv. these are the weights used by the manitoba centre for health policy. elixhauser is a plain count, as mchp uses it. no hierarchy is applied: a person can have both mild and severe liver disease, for example.

## input data

| table | columns | notes |
|---|---|---|
| claims | `person_id`, `service_date`, `dx_code` | one row per claim. icd-9 by default |
| hospital | `person_id`, a date, and codes | wide (`dx_code_1`, `dx_code_2`, ...) or long (`dx_code`). icd-10-ca by default |
| people | `person_id`, `birth_date`, `sex` (optional) | needed for age limits and gestational exclusions |
| procedures | `person_id`, `procedure_date`, `proc_code` | only for ischemic heart disease. cci by default |
| drugs | `person_id`, `dispense_date`, `din` | only for ccdss dementia |
| ambulatory | `person_id`, `visit_date`, and codes | ed and clinic visits (nacrs, accs), same layout as hospital. used by tonelli |

- **hospital dates**: `separation_date`, `admit_date` or `date`. give both separation and admission if you have them, since ami and osteoporosis count from admission.
- **physician specialty**: add a `specialty` column to claims (`GP`, `GAST`, `DERM`) for tonelli ibd and psoriasis. without it, all claims count and you get a warning.
- **diagnosis types**: for ami, add `dx_type_1`, `dx_type_2`, ... (or `dx_type` in long format) with values like `M` (or `MRDx`), `1`, `2`, `3`, `W`. without them every field is used and you get a warning.
- **codes**: dots, spaces and case don't matter, and codes match by prefix. `250` matches `250.1`, and `E11` matches `E11.9`.
- **mixed icd versions**: add an `icd_version` column (9 or 10), or pass `hospital_coding="both"`. for procedures, use `procedure_coding` or a `proc_system` column (`cci`, `ccp`, `icd9cm`).
- **column names**: `columns={"person_id": "PHN"}`. for wide hospital data with other names: `columns={"hospital_dx_columns": ["DIAG1", "DIAG2"]}` (cli: `--hospital-dx DIAG1,DIAG2`).
- **dates**: iso dates just work. for anything else pass `date_format="%d/%m/%Y"`. blank or unreadable dates raise an error that names the rows.
- **warnings**: you get a warning when a check can't be done, like an age limit with no people table.

it's fast enough for full provincial extracts: all 99 definitions on 2 million claims take about 25 seconds on a laptop.

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
