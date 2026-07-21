"""PhenoAge calculation from Levine et al. (2018).

The calculation is deterministic and intended for longitudinal educational
context. It is not a diagnosis, mortality prediction, or substitute for a
clinician's interpretation of laboratory results.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

INTERCEPT = -19.907
GAMMA = 0.0076927
COEFFICIENTS = {
    "albumin": -0.0336,
    "creatinine": 0.0095,
    "glucose": 0.1953,
    "log_crp": 0.0954,
    "lymphocyte_pct": -0.0120,
    "mcv": 0.0268,
    "rdw": 0.3306,
    "alk_phosphatase": 0.00188,
    "wbc": 0.0554,
    "age": 0.0804,
}
REQUIRED = [
    "albumin", "creatinine", "glucose", "crp", "lymphocyte_pct",
    "mcv", "rdw", "alk_phosphatase", "wbc", "age",
]
CONVENTIONAL_TO_SI = {
    "albumin": 10.0,
    "creatinine": 88.4017,
    "glucose": 0.0555,
    "crp": 0.1,
}


@dataclass(frozen=True)
class PhenoAgeResult:
    phenoage: float
    chronological_age: float
    difference_years: float
    completeness: str
    boundary: str

    def as_dict(self) -> dict:
        return asdict(self)


def calculate(biomarkers: dict[str, float], *, si_units: bool = False) -> PhenoAgeResult:
    missing = [key for key in REQUIRED if biomarkers.get(key) is None]
    if missing:
        raise ValueError(f"Missing PhenoAge inputs: {', '.join(missing)}")

    albumin = biomarkers["albumin"] if si_units else biomarkers["albumin"] * CONVENTIONAL_TO_SI["albumin"]
    creatinine = biomarkers["creatinine"] if si_units else biomarkers["creatinine"] * CONVENTIONAL_TO_SI["creatinine"]
    glucose = biomarkers["glucose"] if si_units else biomarkers["glucose"] * CONVENTIONAL_TO_SI["glucose"]
    crp = biomarkers["crp"] if si_units else biomarkers["crp"] * CONVENTIONAL_TO_SI["crp"]
    terms = {
        "albumin": albumin,
        "creatinine": creatinine,
        "glucose": glucose,
        "log_crp": math.log(max(crp, 0.01)),
        "lymphocyte_pct": biomarkers["lymphocyte_pct"],
        "mcv": biomarkers["mcv"],
        "rdw": biomarkers["rdw"],
        "alk_phosphatase": biomarkers["alk_phosphatase"],
        "wbc": biomarkers["wbc"],
        "age": biomarkers["age"],
    }
    linear = INTERCEPT + sum(COEFFICIENTS[key] * value for key, value in terms.items())
    mortality_score = 1 - math.exp(-math.exp(linear) * (math.exp(120 * GAMMA) - 1) / GAMMA)
    mortality_score = min(max(mortality_score, 1e-12), 1 - 1e-12)
    phenoage = 141.50225 + math.log(-0.00553 * math.log(1 - mortality_score)) / 0.090165
    chronological = float(biomarkers["age"])
    return PhenoAgeResult(
        phenoage=round(phenoage, 2),
        chronological_age=chronological,
        difference_years=round(phenoage - chronological, 2),
        completeness="10 of 10 required inputs present",
        boundary="Educational biomarker summary, not a clinical age or mortality prediction.",
    )

