"""Assemble ``demo/record.json``: the full synthetic record the redesigned
demo renders (hero, layers, labs, habits, supplements, interventions,
benchmarks, genome). ``demo/analysis.json`` stays the featured experiment's
contract and is unchanged by this module.

Every number in record.json is computed here or in the modules it calls.
The browser only draws.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from . import habits as habits_mod
from .analysis import _validated_records
from .benchmarks import comparison
from .genomics import interpret_panel
from .labs import MARKERS, age_on, lab_record
from .synthetic import HABIT_COLUMNS, PERSONA, SYNTHETIC_INTERVENTIONS, SUPPLEMENT_SPANS

TIMELINE_KEYS = ("hrv_ms", "sleep_hours", "resting_hr")

# Daily series drawn as small multiples: (key, label, unit, source, digits).
DAILY_SERIES = (
    ("caffeine_mg", "Caffeine", "mg", "logged", 0),
    ("alcohol_units", "Alcohol", "drinks", "logged", 1),
    ("training_load", "Training load", "0–3", "logged", 1),
    ("mood", "Mood", "1–10", "logged", 1),
    ("hrv_ms", "HRV", "ms", "wearable", 1),
    ("resting_hr", "Resting heart rate", "bpm", "wearable", 1),
    ("sleep_hours", "Sleep", "h", "wearable", 2),
)


def daily_series(history: list[dict[str, Any]], *, window: int = 7) -> list[dict[str, Any]]:
    """Each daily series with its trailing ``window``-day mean (at least three
    logged days in the window, otherwise no mean for that day)."""
    out = []
    for key, label, unit, source, digits in DAILY_SERIES:
        points = []
        for i, row in enumerate(history):
            recent = [r.get(key) for r in history[max(0, i - window + 1): i + 1]]
            recent = [v for v in recent if v is not None]
            value = row.get(key)
            points.append({
                "date": row["date"],
                "value": None if value is None else round(value, digits),
                "mean7": round(sum(recent) / len(recent), digits) if len(recent) >= 3 else None,
            })
        logged = [p["value"] for p in points if p["value"] is not None]
        out.append({
            "key": key, "label": label, "unit": unit, "source": source, "digits": digits,
            "days_logged": len(logged),
            "min": min(logged), "max": max(logged),
            "series": points,
        })
    return out


def supplement_summary(rows: list[dict[str, Any]], *, as_of: str) -> list[dict[str, Any]]:
    cutoff = (date.fromisoformat(as_of).toordinal() - 30)
    names = [key for key in rows[0] if key != "date"]
    out = []
    for name in names:
        days = [row["date"] for row in rows if row.get(name)]
        if not days:
            continue
        last = max(days)
        out.append({
            "name": name, "label": name.replace("_", " "),
            "days": len(days), "first": min(days), "last": last,
            "current": date.fromisoformat(last).toordinal() >= cutoff,
            "span_months": round((date.fromisoformat(last) - date.fromisoformat(min(days))).days / 30.44, 1),
        })
    out.sort(key=lambda item: -item["days"])
    return out


def build_record(
    history: list[dict[str, Any]],
    *,
    lab_draws: list[dict[str, Any]],
    genotypes: dict[str, str],
    supplements: list[dict[str, Any]],
    analysis: dict[str, Any],
    interventions: list[dict[str, str]] = SYNTHETIC_INTERVENTIONS,
) -> dict[str, Any]:
    history = _validated_records(history)
    end = history[-1]["date"]
    age_now = age_on(PERSONA["birth_date"], end)
    labs = lab_record(lab_draws, PERSONA["birth_date"])
    genome = interpret_panel(genotypes)
    supplement_rows = supplement_summary(supplements, as_of=end)
    nights = sum(1 for r in history if r.get("hrv_ms") is not None)
    habit_days = sum(1 for r in history if any(r.get(h) is not None for h in HABIT_COLUMNS))
    calendar_days = (date.fromisoformat(end) - date.fromisoformat(history[0]["date"])).days + 1

    effects = habits_mod.habit_effects(history, HABIT_COLUMNS)
    primary_effects = [row for row in effects if row["outcome"] == "hrv_ms"]
    detected = sum(1 for row in primary_effects if row["reading"] == "association")

    return {
        "persona": {**PERSONA, "age": age_now, "as_of": end},
        "scope": {
            "calendar_days": calendar_days,
            "nights_recorded": nights,
            "habit_days": habit_days,
            "lab_draws": len(labs["draws"]),
            "biomarkers_tracked": len(labs["markers"]),
            "years_of_labs": round((date.fromisoformat(labs["draws"][-1]["date"]) - date.fromisoformat(labs["draws"][0]["date"])).days / 365.25, 1),
            "supplements_tracked": len(supplement_rows),
            "supplement_days": sum(1 for row in supplements if any(row.get(k) for k in row if k != "date")),
            "supplement_first": min(row["first"] for row in supplement_rows) if supplement_rows else None,
            "genome_markers": len(genome),
            "interventions": len(interventions),
            "featured_paired_nights": analysis["primary_effect"]["n_on"] + analysis["primary_effect"]["n_off"],
            "first_night": history[0]["date"],
            "last_night": end,
        },
        "hero": {
            "phenoage": labs["latest"]["phenoage"],
            "chronological_age_at_draw": labs["latest"]["age"],
            "gap_years": labs["latest"]["gap_years"],
            "draw_date": labs["latest"]["date"],
            "first_gap_years": labs["first"]["gap_years"],
            "first_draw_date": labs["first"]["date"],
            "swing_years": round(labs["first"]["gap_years"] - labs["latest"]["gap_years"], 2),
            "trend": [{"date": d["date"], "phenoage": d["phenoage"], "age": d["age"], "gap_years": d["gap_years"]} for d in labs["draws"] if d["phenoage"] is not None],
        },
        "timeline": [
            {"date": r["date"], **{k: r.get(k) for k in TIMELINE_KEYS}, "caffeine_cutoff_2pm": r.get("caffeine_cutoff_2pm")}
            for r in history
        ],
        "labs": labs,
        "daily": daily_series(history),
        "habits": {
            "columns": HABIT_COLUMNS,
            "effects": effects,
            "detected_on_hrv": detected,
            "tested": len(primary_effects),
            "calendar": habits_mod.habit_calendar(history, HABIT_COLUMNS + ["caffeine_cutoff_2pm"]),
            "note": "Caffeine timing is excluded from this panel because it has its own pre-specified experiment on the fixed 84-day window below; mixing windows would show two different numbers for one question.",
        },
        "inputs": habits_mod.input_correlations(history, ["caffeine_mg", "training_load", "alcohol_units", "meditation"]),
        "interventions": habits_mod.intervention_effects(history, interventions),
        "supplements": supplement_rows,
        "benchmarks": comparison(history, age_now, PERSONA["sex"]),
        "genome": {
            "findings": genome,
            "markers_total": len(genotypes),
            "boundary": "Context, never verdicts. Single markers are probabilistic and population-dependent; in LiveForever a genotype can nominate a question or a lab to add, and nothing else.",
        },
        "featured": {
            "question": analysis["question"],
            "window_start": analysis["dataset"]["start_date"],
            "window_end": analysis["dataset"]["end_date"],
            "recorded_days": analysis["dataset"]["recorded_days"],
            "effect": analysis["primary_effect"]["effect"],
            "ci_low": analysis["primary_effect"]["ci_low"],
            "ci_high": analysis["primary_effect"]["ci_high"],
            "n_on": analysis["primary_effect"]["n_on"],
            "n_off": analysis["primary_effect"]["n_off"],
        },
        "provenance": [
            "record.json is generated by src/liveforever_lab/record.py from the same deterministic engine as analysis.json.",
            "Habit effects reuse analysis.binary_effect: next-day mean on done days minus not-done days, moving-block bootstrap 95% interval.",
            "Intervention windows compare the 28 days after a dated change with the 28 days before, independent-groups 95% interval; time-confounded by construction.",
            "PhenoAge per draw uses the published Levine et al. (2018) coefficients with the persona's age on the draw date.",
            "Genome findings come from a curated panel of public rsIDs; the fixture genotypes are invented.",
        ],
        "boundary": "Every value on this page describes Maya Chen, a fictional person. Associations are not causes; nothing here is a diagnosis or a recommendation.",
    }
