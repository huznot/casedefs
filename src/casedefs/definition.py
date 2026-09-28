from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    """how many qualifying records a person needs to become a case.

    a person qualifies on the first date any path is met:
    - at least `min_hospital` hospital records
    - at least `min_claims` physician claims where the first and last are no
      more than `window_days` apart, and each claim is at least
      `min_days_between` days after the one before it
    - at least `min_procedures` procedure records
    - at least `min_drugs` drug dispensations
    set a count to None to switch that path off.
    """

    min_hospital: int | None = 1
    min_claims: int | None = 2
    window_days: int | None = None
    min_days_between: int = 0
    # the hospital path only counts from this age (used by epilepsy)
    hospital_min_age: int | None = None
    min_procedures: int | None = None
    min_drugs: int | None = None

    def describe(self) -> str:
        parts = []
        if self.min_hospital:
            text = f">= {self.min_hospital} hospital record(s)"
            if self.hospital_min_age is not None:
                text += f" (ages {self.hospital_min_age}+ only)"
            parts.append(text)
        if self.min_claims:
            text = f">= {self.min_claims} physician claim(s)"
            if self.min_claims > 1 and self.window_days:
                text += f" within {self.window_days} days"
            if self.min_claims > 1 and self.min_days_between:
                text += f", each at least {self.min_days_between} day(s) after the last"
            parts.append(text)
        if self.min_procedures:
            parts.append(f">= {self.min_procedures} procedure(s)")
        if self.min_drugs:
            parts.append(f">= {self.min_drugs} drug dispensation(s)")
        return " OR ".join(parts)


@dataclass(frozen=True)
class Exclusion:
    """blocks a case date that falls near a hospital record with certain codes.

    used for gestational diabetes and gestational hypertension. a person in
    the given sex and age range cannot become a case on a date from
    `days_before` days before to `days_after` days after a hospital record
    containing one of the listed codes.
    """

    name: str
    icd9: tuple[str, ...]
    icd10ca: tuple[str, ...]
    days_before: int
    days_after: int
    sex: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    description: str = ""


@dataclass(frozen=True)
class ClaimsExclusion:
    """removes a case who later has repeat claims for another condition.

    used for rheumatoid arthritis. on or after the qualifying date, a person
    with `min_claims` physician claims for the same code (compared at
    `icd9_digits` / `icd10ca_digits` characters), each at least
    `min_days_between` days apart and all within `window_days`, is not a case.
    """

    name: str
    icd9: tuple[str, ...]
    icd10ca: tuple[str, ...]
    min_claims: int = 2
    window_days: int = 730
    min_days_between: int = 1
    icd9_digits: int = 3
    icd10ca_digits: int = 4
    description: str = ""


def _age_text(min_age: int | None, max_age: int | None) -> str:
    if min_age is None and max_age is None:
        return "all ages"
    if max_age is None:
        return f"{min_age}+"
    if min_age is None:
        return f"up to {max_age}"
    return f"{min_age} to {max_age}"


@dataclass(frozen=True)
class Definition:
    id: str
    name: str
    version: str
    source_title: str
    source_url: str
    source_location: str
    verified: bool
    # hospital codes. claims use the same codes unless claims_icd9 or
    # claims_icd10ca are set.
    icd9: tuple[str, ...]
    icd10ca: tuple[str, ...]
    rule: Rule
    min_age: int | None = None
    max_age: int | None = None
    claims_icd9: tuple[str, ...] | None = None
    claims_icd10ca: tuple[str, ...] | None = None
    # codes that never count even though a listed prefix covers them
    excluded_codes: tuple[str, ...] = ()
    # only these hospital diagnosis types count, e.g. ("M", "1", "2", "W", "X", "Y")
    hospital_dx_types: tuple[str, ...] | None = None
    # "separation" or "admission": which hospital date is the record date
    hospital_date: str = "separation"
    procedure_cci: tuple[str, ...] = ()
    procedure_ccp: tuple[str, ...] = ()
    procedure_icd9cm: tuple[str, ...] = ()
    drug_dins: tuple[str, ...] = ()
    exclusions: tuple[Exclusion | ClaimsExclusion, ...] = field(default_factory=tuple)
    notes: str = ""

    @property
    def claims_codes(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        icd9 = self.icd9 if self.claims_icd9 is None else self.claims_icd9
        icd10 = self.icd10ca if self.claims_icd10ca is None else self.claims_icd10ca
        return icd9, icd10

    def citation(self) -> str:
        return f"{self.source_title}. {self.source_location}. {self.source_url}"

    def age_text(self) -> str:
        return _age_text(self.min_age, self.max_age)


@dataclass(frozen=True)
class Composite:
    """a case of this if a person is a case of at least `min_conditions` of `components`.

    the case date is the date the person meets their `min_conditions`-th
    component condition.
    """

    id: str
    name: str
    version: str
    source_title: str
    source_url: str
    source_location: str
    verified: bool
    components: tuple[str, ...]
    min_conditions: int
    min_age: int | None = None
    max_age: int | None = None
    notes: str = ""

    def citation(self) -> str:
        return f"{self.source_title}. {self.source_location}. {self.source_url}"

    def age_text(self) -> str:
        return _age_text(self.min_age, self.max_age)

    def describe(self) -> str:
        return f"case of >= {self.min_conditions} of {len(self.components)} listed conditions"


def code_range(start: str, end: str) -> tuple[str, ...]:
    """expand a published range like 641-679 or O21-O95 into code prefixes.

    both ends must share the same letter prefix and digit width. this only
    spells out a range exactly as written in the source; it never adds codes.
    """
    letters = start.rstrip("0123456789")
    if not end.startswith(letters) or letters != end.rstrip("0123456789"):
        raise ValueError(f"range ends do not share a prefix: {start}-{end}")
    lo, hi = start[len(letters):], end[len(letters):]
    if len(lo) != len(hi):
        raise ValueError(f"range ends differ in width: {start}-{end}")
    if int(lo) > int(hi):
        raise ValueError(f"range is backwards: {start}-{end}")
    return tuple(f"{letters}{n:0{len(lo)}d}" for n in range(int(lo), int(hi) + 1))
