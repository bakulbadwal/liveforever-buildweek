"""Deterministic N-of-1 analysis with explicit uncertainty and data checks.

This module calculates the numbers shown to the model and the user. It does
not diagnose, prescribe, or infer causality from observational data.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

Z_95 = 1.959963984540054


@dataclass(frozen=True)
class EffectEstimate:
    outcome: str
    exposure: str
    lag_days: int
    effect: float | None
    ci_low: float | None
    ci_high: float | None
    n_on: int
    n_off: int
    mean_on: float | None
    mean_off: float | None
    interpretation: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def load_csv(path: str | Path) -> list[dict[str, Any]]:
    """Load a daily CSV, converting numeric cells and preserving ISO dates."""
    records: list[dict[str, Any]] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            converted: dict[str, Any] = {"date": row["date"]}
            for key, value in row.items():
                if key == "date":
                    continue
                value = (value or "").strip()
                converted[key] = float(value) if value else None
            records.append(converted)
    return sorted(records, key=lambda record: record["date"])


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _variance(values: list[float]) -> float:
    return statistics.variance(values) if len(values) > 1 else 0.0


def _round(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def _lagged_groups(
    records: Iterable[dict[str, Any]], exposure: str, outcome: str, lag_days: int
) -> tuple[list[float], list[float], int]:
    by_day = {record["date"]: record for record in records}
    on: list[float] = []
    off: list[float] = []
    eligible = 0
    for day, record in by_day.items():
        exposure_value = record.get(exposure)
        if exposure_value is None:
            continue
        eligible += 1
        outcome_day = (date.fromisoformat(day) + timedelta(days=lag_days)).isoformat()
        outcome_value = by_day.get(outcome_day, {}).get(outcome)
        if outcome_value is None:
            continue
        (on if exposure_value >= 0.5 else off).append(float(outcome_value))
    return on, off, eligible


def _lagged_pairs(
    records: Iterable[dict[str, Any]], exposure: str, outcome: str, lag_days: int
) -> list[tuple[float, float]]:
    by_day = {record["date"]: record for record in records}
    pairs: list[tuple[float, float]] = []
    for day in sorted(by_day):
        exposure_value = by_day[day].get(exposure)
        outcome_day = (date.fromisoformat(day) + timedelta(days=lag_days)).isoformat()
        outcome_value = by_day.get(outcome_day, {}).get(outcome)
        if exposure_value is not None and outcome_value is not None:
            pairs.append((float(exposure_value), float(outcome_value)))
    return pairs


def _block_bootstrap_interval(
    pairs: list[tuple[float, float]], *, iterations: int = 3000, block_days: int = 7, seed: int = 56
) -> tuple[float, float] | None:
    """Moving-block bootstrap interval preserving short-range time structure."""
    if len(pairs) < 8:
        return None
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        sample: list[tuple[float, float]] = []
        while len(sample) < len(pairs):
            start = rng.randrange(len(pairs))
            sample.extend(pairs[(start + offset) % len(pairs)] for offset in range(block_days))
        sample = sample[:len(pairs)]
        on = [outcome_value for exposure_value, outcome_value in sample if exposure_value >= 0.5]
        off = [outcome_value for exposure_value, outcome_value in sample if exposure_value < 0.5]
        if on and off:
            estimates.append(statistics.mean(on) - statistics.mean(off))
    if not estimates:
        return None
    estimates.sort()
    low = estimates[round((len(estimates) - 1) * 0.025)]
    high = estimates[round((len(estimates) - 1) * 0.975)]
    return low, high


def binary_effect(
    records: list[dict[str, Any]],
    exposure: str,
    outcome: str,
    *,
    lag_days: int = 1,
    minimum_per_group: int = 10,
) -> EffectEstimate:
    """Estimate mean(outcome|exposed) - mean(outcome|unexposed).

    The 95% interval uses a deterministic seven-day moving-block bootstrap,
    with a normal approximation only for very short series. It is an
    uncertainty estimate for this observed comparison, not a causal interval.
    """
    pairs = _lagged_pairs(records, exposure, outcome, lag_days)
    on = [outcome_value for exposure_value, outcome_value in pairs if exposure_value >= 0.5]
    off = [outcome_value for exposure_value, outcome_value in pairs if exposure_value < 0.5]
    mean_on, mean_off = _mean(on), _mean(off)
    if mean_on is None or mean_off is None:
        interpretation = "Insufficient paired observations to compare conditions."
        return EffectEstimate(outcome, exposure, lag_days, None, None, None,
                              len(on), len(off), mean_on, mean_off, interpretation)

    effect = mean_on - mean_off
    interval = _block_bootstrap_interval(pairs)
    if interval is None:
        se = math.sqrt(_variance(on) / len(on) + _variance(off) / len(off))
        ci_low, ci_high = effect - Z_95 * se, effect + Z_95 * se
    else:
        ci_low, ci_high = interval

    if min(len(on), len(off)) < minimum_per_group:
        interpretation = "Early estimate: at least one condition is below the minimum sample target."
    elif ci_low <= 0 <= ci_high:
        interpretation = "Inconclusive: the interval includes no difference."
    elif effect > 0:
        interpretation = "Observed association with a higher outcome; replicate before acting."
    else:
        interpretation = "Observed association with a lower outcome; replicate before acting."

    return EffectEstimate(
        outcome, exposure, lag_days, _round(effect), _round(ci_low), _round(ci_high),
        len(on), len(off), _round(mean_on), _round(mean_off), interpretation,
    )


def pearson_with_interval(
    records: list[dict[str, Any]], x_key: str, y_key: str, *, lag_days: int = 1
) -> dict[str, Any]:
    """Pearson r with a Fisher-transformed 95% interval."""
    by_day = {record["date"]: record for record in records}
    xs: list[float] = []
    ys: list[float] = []
    for day, record in by_day.items():
        x = record.get(x_key)
        target_day = (date.fromisoformat(day) + timedelta(days=lag_days)).isoformat()
        y = by_day.get(target_day, {}).get(y_key)
        if x is None or y is None:
            continue
        xs.append(float(x))
        ys.append(float(y))

    if len(xs) < 6 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return {"x": x_key, "y": y_key, "lag_days": lag_days, "r": None,
                "ci_low": None, "ci_high": None, "n": len(xs),
                "interpretation": "Insufficient variation or paired observations."}

    r = max(-0.999999, min(0.999999, statistics.correlation(xs, ys)))
    if len(xs) <= 3:
        low = high = None
    else:
        fisher = math.atanh(r)
        width = Z_95 / math.sqrt(len(xs) - 3)
        low, high = math.tanh(fisher - width), math.tanh(fisher + width)
    return {
        "x": x_key, "y": y_key, "lag_days": lag_days,
        "r": _round(r, 3), "ci_low": _round(low, 3), "ci_high": _round(high, 3),
        "n": len(xs),
        "interpretation": "Association only; lagging does not establish causality.",
    }


def trend_summary(
    records: list[dict[str, Any]], metric: str, *, recent_days: int = 7, baseline_days: int = 28
) -> dict[str, Any]:
    """Compare the most recent window with the preceding baseline window."""
    available = [(date.fromisoformat(r["date"]), r.get(metric)) for r in records if r.get(metric) is not None]
    if not available:
        return {"metric": metric, "recent_mean": None, "baseline_mean": None,
                "change": None, "status": "insufficient"}
    end = max(day for day, _ in available)
    recent_start = end - timedelta(days=recent_days - 1)
    baseline_end = recent_start - timedelta(days=1)
    baseline_start = baseline_end - timedelta(days=baseline_days - 1)
    recent = [float(value) for day, value in available if recent_start <= day <= end]
    baseline = [float(value) for day, value in available if baseline_start <= day <= baseline_end]
    if len(recent) < 3 or len(baseline) < 10:
        status = "insufficient"
    else:
        status = "observed"
    recent_mean, baseline_mean = _mean(recent), _mean(baseline)
    change = recent_mean - baseline_mean if recent_mean is not None and baseline_mean is not None else None
    return {
        "metric": metric, "recent_mean": _round(recent_mean), "baseline_mean": _round(baseline_mean),
        "change": _round(change), "recent_n": len(recent), "baseline_n": len(baseline), "status": status,
    }


def quality_report(
    records: list[dict[str, Any]], exposure: str, outcome: str, *, lag_days: int = 1
) -> dict[str, Any]:
    """Return coverage, balance, paired-sample, and confounding warnings."""
    if not records:
        return {"score": 0, "grade": "F", "warnings": ["No records supplied."]}
    days = [date.fromisoformat(record["date"]) for record in records]
    calendar_days = (max(days) - min(days)).days + 1
    coverage = len(set(days)) / calendar_days
    on, off, eligible = _lagged_groups(records, exposure, outcome, lag_days)
    paired = len(on) + len(off)
    ratio = max(len(on), len(off)) / max(1, min(len(on), len(off)))
    warnings: list[str] = []
    score = 100

    if coverage < 0.9:
        warnings.append(f"Calendar coverage is {coverage:.0%}; missing days can bias the comparison.")
        score -= 15
    elif coverage < 0.97:
        warnings.append(f"Calendar coverage is {coverage:.0%}; review why days are missing.")
        score -= 7
    if min(len(on), len(off)) < 10:
        warnings.append("At least one condition has fewer than 10 paired observations.")
        score -= 20
    if ratio > 2:
        warnings.append(f"Conditions are imbalanced ({len(on)} vs {len(off)} paired days).")
        score -= 12
    if paired < eligible * 0.85:
        warnings.append(f"Only {paired} of {eligible} exposure days have a paired outcome.")
        score -= 12

    confound = _condition_difference(records, exposure, "alcohol_units")
    if confound is not None and abs(confound) >= 0.35:
        warnings.append("Alcohol exposure differs across conditions and may confound recovery outcomes.")
        score -= 12

    warnings.append("This is observational self-tracking data, not a randomized causal estimate.")
    score -= 8
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
    return {
        "score": max(0, score), "grade": grade, "coverage": round(coverage, 3),
        "calendar_days": calendar_days, "recorded_days": len(set(days)),
        "paired_days": paired, "condition_on_n": len(on), "condition_off_n": len(off),
        "balance_ratio": round(ratio, 2), "warnings": warnings,
    }


def _condition_difference(records: list[dict[str, Any]], exposure: str, metric: str) -> float | None:
    on = [float(r[metric]) for r in records if r.get(exposure) is not None and r.get(metric) is not None and r[exposure] >= 0.5]
    off = [float(r[metric]) for r in records if r.get(exposure) is not None and r.get(metric) is not None and r[exposure] < 0.5]
    return statistics.mean(on) - statistics.mean(off) if on and off else None


def analyze_dataset(
    records: list[dict[str, Any]],
    *,
    genomics_context: dict[str, Any] | None = None,
    longevity_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the complete deterministic analysis contract consumed by GPT-5.6."""
    exposure = "caffeine_cutoff_2pm"
    hrv = binary_effect(records, exposure, "hrv_ms")
    sleep = binary_effect(records, exposure, "sleep_hours")
    resting_hr = binary_effect(records, exposure, "resting_hr")
    quality = quality_report(records, exposure, "hrv_ms")
    return {
        "question": "Does stopping caffeine by 2 PM improve next-day recovery?",
        "analysis_type": "observational within-person comparison",
        "dataset": {
            "start_date": records[0]["date"], "end_date": records[-1]["date"],
            "recorded_days": len(records), "persona": "Maya Chen (fictional)",
        },
        "primary_effect": hrv.as_dict(),
        "secondary_effects": [sleep.as_dict(), resting_hr.as_dict()],
        "dose_response": pearson_with_interval(records, "caffeine_mg", "sleep_hours"),
        "trends": [trend_summary(records, "hrv_ms"), trend_summary(records, "sleep_hours")],
        "timeline": [
            {
                "date": record["date"],
                "hrv_ms": record.get("hrv_ms"),
                "sleep_hours": record.get("sleep_hours"),
                "caffeine_cutoff_2pm": record.get("caffeine_cutoff_2pm"),
            }
            for record in records[-56:]
        ],
        "quality": quality,
        "genomics_context": genomics_context or {},
        "longevity_snapshot": longevity_snapshot or {},
        "calculation_provenance": [
            "Effect = mean(next-day outcome | cutoff followed) - mean(next-day outcome | cutoff not followed).",
            "95% interval = deterministic seven-day moving-block bootstrap percentile interval.",
            "Pearson interval uses Fisher's z transformation.",
            "All labels and warnings are derived by src/liveforever_lab/analysis.py.",
        ],
        "claim_boundary": "Wellness experiment planning only. Observed associations are not diagnoses, prescriptions, or causal proof.",
    }
