"""Do the practices move recovery? Habit effects, input correlations, and
intervention before/after windows, all with explicit uncertainty.

Every function here reuses the frozen estimators in ``analysis.py`` so the
habit panel and the featured experiment share one definition of an effect
and one bootstrap.
"""

from __future__ import annotations

import math
import statistics
from datetime import date, timedelta
from typing import Any

from .analysis import Z_95, binary_effect, pearson_with_interval

OUTCOMES: dict[str, dict[str, Any]] = {
    "hrv_ms": {"label": "Next-day HRV", "unit": "ms", "digits": 1, "higher_is_better": True},
    "sleep_hours": {"label": "Sleep duration", "unit": "h", "digits": 2, "higher_is_better": True},
    "resting_hr": {"label": "Resting heart rate", "unit": "bpm", "digits": 1, "higher_is_better": False},
}

HABIT_LABELS: dict[str, str] = {
    "meditation": "Meditation",
    "breathwork": "Breathwork",
    "cold_exposure": "Cold exposure",
    "morning_light": "Morning light",
    "evening_walk": "Evening walk",
    "caffeine_cutoff_2pm": "Caffeine stopped by 2 PM",
    "alcohol_units": "Alcohol",
}

INPUT_LABELS: dict[str, str] = {
    "caffeine_mg": "Caffeine (mg)",
    "training_load": "Training load",
    "alcohol_units": "Alcohol",
    "meditation": "Meditation",
}


def habit_effects(
    records: list[dict[str, Any]], habits: list[str], outcomes: list[str] | None = None, *, lag_days: int = 1
) -> list[dict[str, Any]]:
    """For each 0/1 habit and outcome: next-day mean on done minus not-done days,
    the bootstrap 95% interval, sample counts, and Pearson r."""
    outcomes = outcomes or list(OUTCOMES)
    rows: list[dict[str, Any]] = []
    for habit in habits:
        for outcome in outcomes:
            effect = binary_effect(records, habit, outcome, lag_days=lag_days)
            correlation = pearson_with_interval(records, habit, outcome, lag_days=lag_days)
            crosses_zero = (
                effect.ci_low is None or effect.ci_high is None or (effect.ci_low <= 0 <= effect.ci_high)
            )
            rows.append({
                "habit": habit, "label": HABIT_LABELS.get(habit, habit),
                "outcome": outcome, "outcome_label": OUTCOMES[outcome]["label"], "unit": OUTCOMES[outcome]["unit"],
                "effect": effect.effect, "ci_low": effect.ci_low, "ci_high": effect.ci_high,
                "n_on": effect.n_on, "n_off": effect.n_off,
                "mean_on": effect.mean_on, "mean_off": effect.mean_off,
                "r": correlation["r"],
                "reading": "nothing detected" if crosses_zero else "association",
                "interpretation": effect.interpretation,
            })
    return rows


def input_correlations(
    records: list[dict[str, Any]], inputs: list[str], outcomes: list[str] | None = None, *, lag_days: int = 1
) -> list[dict[str, Any]]:
    """Rank every logged input against every next-day outcome by |r|, keeping nulls visible."""
    outcomes = outcomes or list(OUTCOMES)
    rows: list[dict[str, Any]] = []
    for key in inputs:
        for outcome in outcomes:
            result = pearson_with_interval(records, key, outcome, lag_days=lag_days)
            rows.append({
                "input": key, "label": INPUT_LABELS.get(key, HABIT_LABELS.get(key, key)),
                "outcome": outcome, "outcome_label": OUTCOMES[outcome]["label"],
                "r": result["r"], "ci_low": result["ci_low"], "ci_high": result["ci_high"], "n": result["n"],
            })
    rows.sort(key=lambda row: -abs(row["r"]) if row["r"] is not None else 1.0)
    return rows


def habit_calendar(records: list[dict[str, Any]], habits: list[str]) -> dict[str, Any]:
    """Week-by-week adherence for the heatmap: per habit, per ISO week, done and logged counts."""
    by_day = {record["date"]: record for record in records}
    first = date.fromisoformat(records[0]["date"])
    last = date.fromisoformat(records[-1]["date"])
    week_start = first - timedelta(days=first.weekday())
    weeks: list[dict[str, Any]] = []
    cursor = week_start
    while cursor <= last:
        week = {"start": cursor.isoformat(), "days": []}
        for offset in range(7):
            day = cursor + timedelta(days=offset)
            record = by_day.get(day.isoformat())
            week["days"].append({
                "date": day.isoformat(),
                "logged": record is not None,
                "done": {habit: (None if record is None or record.get(habit) is None else int(record[habit] >= 0.5)) for habit in habits},
            })
        weeks.append(week)
        cursor += timedelta(days=7)
    totals = {}
    for habit in habits:
        done = sum(1 for record in records if record.get(habit) is not None and record[habit] >= 0.5)
        logged = sum(1 for record in records if record.get(habit) is not None)
        streak = 0
        for record in reversed(records):
            value = record.get(habit)
            if value is None or value < 0.5:
                break
            streak += 1
        totals[habit] = {"label": HABIT_LABELS.get(habit, habit), "done": done, "logged": logged, "streak": streak}
    return {"weeks": weeks, "totals": totals, "first": records[0]["date"], "last": records[-1]["date"]}


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def intervention_effects(
    records: list[dict[str, Any]], interventions: list[dict[str, str]], outcomes: list[str] | None = None,
    *, before_days: int = 28, after_days: int = 28, minimum: int = 10,
) -> list[dict[str, Any]]:
    """Mean of each outcome in the 28 days after a dated intervention minus the 28
    days before, with an independent-groups 95% interval. Time-confounded by
    construction; labelled as the weakest evidence on the page."""
    outcomes = outcomes or list(OUTCOMES)
    by_day = {record["date"]: record for record in records}
    results: list[dict[str, Any]] = []
    for item in interventions:
        start = date.fromisoformat(item["date"])
        effects = []
        for outcome in outcomes:
            before = [float(by_day[d][outcome]) for d in (
                (start - timedelta(days=offset)).isoformat() for offset in range(1, before_days + 1)
            ) if d in by_day and by_day[d].get(outcome) is not None]
            after = [float(by_day[d][outcome]) for d in (
                (start + timedelta(days=offset)).isoformat() for offset in range(after_days)
            ) if d in by_day and by_day[d].get(outcome) is not None]
            mean_before, mean_after = _mean(before), _mean(after)
            if mean_before is None or mean_after is None or min(len(before), len(after)) < minimum:
                effects.append({"outcome": outcome, "outcome_label": OUTCOMES[outcome]["label"], "unit": OUTCOMES[outcome]["unit"],
                                "effect": None, "ci_low": None, "ci_high": None,
                                "n_before": len(before), "n_after": len(after), "reading": "insufficient"})
                continue
            delta = mean_after - mean_before
            se = math.sqrt(statistics.variance(before) / len(before) + statistics.variance(after) / len(after))
            low, high = delta - Z_95 * se, delta + Z_95 * se
            effects.append({
                "outcome": outcome, "outcome_label": OUTCOMES[outcome]["label"], "unit": OUTCOMES[outcome]["unit"],
                "effect": round(delta, 2), "ci_low": round(low, 2), "ci_high": round(high, 2),
                "mean_before": round(mean_before, 2), "mean_after": round(mean_after, 2),
                "n_before": len(before), "n_after": len(after),
                "reading": "nothing detected" if low <= 0 <= high else "change observed",
            })
        results.append({**item, "window_days": before_days, "effects": effects})
    return results
