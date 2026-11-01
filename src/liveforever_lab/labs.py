"""Bloodwork across years: PhenoAge per draw and each biomarker against a
reference range.

Reference ranges are general adult laboratory conventions written here as
checked-in constants with a note; they vary by laboratory and are context
for reading a chart, not clinical thresholds for this fictional person.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .phenoage import calculate

# key: label, unit, (low, high) typical adult reference range, note
MARKERS: dict[str, dict[str, Any]] = {
    "albumin": {"label": "Albumin", "unit": "g/dL", "range": [3.5, 5.0], "phenoage": True},
    "creatinine": {"label": "Creatinine", "unit": "mg/dL", "range": [0.6, 1.1], "phenoage": True},
    "glucose": {"label": "Fasting glucose", "unit": "mg/dL", "range": [70, 99], "phenoage": True},
    "crp": {"label": "hs-CRP", "unit": "mg/L", "range": [0, 3.0], "phenoage": True, "note": "Under 1 mg/L is often read as lower cardiovascular risk; 1 to 3 average."},
    "lymphocyte_pct": {"label": "Lymphocytes", "unit": "%", "range": [20, 40], "phenoage": True},
    "mcv": {"label": "MCV", "unit": "fL", "range": [80, 100], "phenoage": True},
    "rdw": {"label": "RDW", "unit": "%", "range": [11.5, 14.5], "phenoage": True},
    "alk_phosphatase": {"label": "Alkaline phosphatase", "unit": "U/L", "range": [40, 120], "phenoage": True},
    "wbc": {"label": "White blood cells", "unit": "K/uL", "range": [4.0, 10.5], "phenoage": True},
    "total_cholesterol": {"label": "Total cholesterol", "unit": "mg/dL", "range": [0, 200]},
    "ldl": {"label": "LDL cholesterol", "unit": "mg/dL", "range": [0, 100]},
    "hdl": {"label": "HDL cholesterol", "unit": "mg/dL", "range": [50, 100]},
    "triglycerides": {"label": "Triglycerides", "unit": "mg/dL", "range": [0, 150]},
    "apob": {"label": "ApoB", "unit": "mg/dL", "range": [0, 90]},
    "hba1c": {"label": "HbA1c", "unit": "%", "range": [4.0, 5.6]},
    "vitamin_d": {"label": "Vitamin D (25-OH)", "unit": "ng/mL", "range": [30, 100]},
    "ferritin": {"label": "Ferritin", "unit": "ng/mL", "range": [15, 150]},
}


def age_on(birth_date: str, day: str) -> float:
    born = date.fromisoformat(birth_date)
    when = date.fromisoformat(day)
    return round((when - born).days / 365.25, 1)


def lab_record(draws: list[dict[str, Any]], birth_date: str) -> dict[str, Any]:
    """PhenoAge for every draw with all nine inputs, plus per-marker series."""
    ordered = sorted(draws, key=lambda draw: draw["date"])
    out_draws: list[dict[str, Any]] = []
    for draw in ordered:
        age = age_on(birth_date, draw["date"])
        values = {key: draw[key] for key in MARKERS if draw.get(key) is not None}
        entry: dict[str, Any] = {"date": draw["date"], "age": age, "values": values}
        try:
            result = calculate({**values, "age": age})
            entry["phenoage"] = result.phenoage
            entry["gap_years"] = result.difference_years
        except ValueError as exc:
            entry["phenoage"] = None
            entry["gap_years"] = None
            entry["note"] = str(exc)
        flags = []
        for key, value in values.items():
            low, high = MARKERS[key]["range"]
            if value < low or value > high:
                flags.append(key)
        entry["outside_range"] = flags
        out_draws.append(entry)

    markers = {}
    for key, spec in MARKERS.items():
        series = [{"date": draw["date"], "value": draw["values"][key]} for draw in out_draws if key in draw["values"]]
        if series:
            markers[key] = {**spec, "series": series}
    with_pheno = [draw for draw in out_draws if draw["phenoage"] is not None]
    return {
        "draws": out_draws,
        "markers": markers,
        "latest": with_pheno[-1] if with_pheno else None,
        "first": with_pheno[0] if with_pheno else None,
        "boundary": "PhenoAge (Levine et al. 2018) is an educational biomarker summary, not a clinical age or mortality prediction. Reference ranges are general laboratory conventions, not thresholds for this person.",
    }
