"""Age and sex reference points for reading a personal metric in context.

Approximate age-band figures written as checked-in constants with a note.
They are not drawn from a cited cohort study; they are rough reference
values for context, never targets. HRV in particular is device- and
method-dependent.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

# rMSSD-style nightly HRV median by age band (ms); population medians for context.
HRV_BY_AGE = {20: 60, 30: 50, 40: 42, 50: 35, 60: 30, 70: 26}
# A fit-but-not-athlete resting heart rate reference is fairly age-flat.
RHR_REFERENCE = 60
# Sleep: the adult recommendation is 7 to 9 hours; 7.0 is used as the single reference point.
SLEEP_REFERENCE_HOURS = 7.0

REFERENCE_NOTES = {
    "hrv_ms": "Approximate age-band figure, a checked-in constant rather than a cited cohort; HRV is device- and method-dependent.",
    "resting_hr": "A fit-but-not-athlete reference, roughly flat across adult ages.",
    "sleep_hours": "Lower edge of the common 7 to 9 hour adult recommendation.",
}


def _band(age: float, table: dict[int, float]) -> float:
    key = min(table, key=lambda k: abs(k - age))
    return table[key]


def cohort_reference(metric: str, age: float, sex: str) -> float | None:
    if metric == "hrv_ms":
        return _band(age, HRV_BY_AGE)
    if metric == "resting_hr":
        return RHR_REFERENCE
    if metric == "sleep_hours":
        return SLEEP_REFERENCE_HOURS
    return None


def comparison(records: list[dict[str, Any]], age: float, sex: str, *, days: int = 90) -> list[dict[str, Any]]:
    """The persona's last-N-day mean beside the cohort reference for each metric."""
    last = date.fromisoformat(records[-1]["date"])
    start = (last - timedelta(days=days - 1)).isoformat()
    rows = []
    for metric, label, unit, digits in (
        ("hrv_ms", "Nightly HRV", "ms", 1), ("resting_hr", "Resting heart rate", "bpm", 1), ("sleep_hours", "Sleep duration", "h", 2),
    ):
        values = [float(r[metric]) for r in records if r["date"] >= start and r.get(metric) is not None]
        reference = cohort_reference(metric, age, sex)
        rows.append({
            "metric": metric, "label": label, "unit": unit, "digits": digits,
            "persona_mean": round(statistics.mean(values), digits) if values else None,
            "n": len(values), "window_days": days,
            "reference": reference, "reference_note": REFERENCE_NOTES[metric],
            "age": age, "sex": sex,
        })
    return rows
