"""Deterministic fictional data for the public Build Week demonstration.

Two generators live here:

* ``generate_records`` is the original 84-day window (80 recorded days) that
  the judged caffeine analysis runs on. It is frozen: its output is the
  checked-in ``examples/maya_daily.csv`` and the featured numbers in the README.
* ``generate_history`` is the post-submission extension: one full year of
  wearable nights and coaching-log habits whose final 84 days reproduce
  ``generate_records`` exactly (same dates, same values for every shared
  column). Extra habit columns are drawn from a separate random stream so the
  frozen window is never disturbed. ``tests/test_record.py`` proves it.

Everything below describes Maya Chen, a fictional 34-year-old woman. No value
belongs to a real person.
"""

from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

PERSONA = {
    "name": "Maya Chen",
    "sex": "female",
    "birth_date": "1992-02-14",
    "note": "Fictional persona generated for this demonstration.",
}

SYNTHETIC_LABS = {
    "albumin": 4.2,
    "creatinine": 0.95,
    "glucose": 95.0,
    "crp": 1.5,
    "lymphocyte_pct": 27.0,
    "mcv": 92.0,
    "rdw": 13.2,
    "alk_phosphatase": 65.0,
    "wbc": 6.5,
    "age": 34.0,
}

# Seven fictional blood draws. The last one is SYNTHETIC_LABS, so the
# featured analysis's longevity snapshot is unchanged. Units are US
# conventional (the units phenoage.calculate expects by default).
SYNTHETIC_LAB_DRAWS: list[dict[str, Any]] = [
    {"date": "2019-03-12", "albumin": 4.0, "creatinine": 0.90, "glucose": 99.0, "crp": 3.4,
     "lymphocyte_pct": 23.0, "mcv": 90.0, "rdw": 13.9, "alk_phosphatase": 74.0, "wbc": 7.6,
     "total_cholesterol": 212.0, "ldl": 138.0, "hdl": 52.0, "triglycerides": 118.0, "apob": 104.0,
     "hba1c": 5.6, "vitamin_d": 21.0, "ferritin": 24.0},
    {"date": "2020-09-22", "albumin": 4.0, "creatinine": 0.92, "glucose": 98.0, "crp": 2.9,
     "lymphocyte_pct": 24.0, "mcv": 90.0, "rdw": 13.8, "alk_phosphatase": 72.0, "wbc": 7.3,
     "total_cholesterol": 206.0, "ldl": 134.0, "hdl": 54.0, "triglycerides": 112.0, "apob": 101.0,
     "hba1c": 5.5, "vitamin_d": 26.0, "ferritin": 27.0},
    {"date": "2021-11-08", "albumin": 4.1, "creatinine": 0.93, "glucose": 97.0, "crp": 2.6,
     "lymphocyte_pct": 25.0, "mcv": 91.0, "rdw": 13.7, "alk_phosphatase": 70.0, "wbc": 7.1,
     "total_cholesterol": 201.0, "ldl": 129.0, "hdl": 56.0, "triglycerides": 104.0, "apob": 97.0,
     "hba1c": 5.5, "vitamin_d": 31.0, "ferritin": 31.0},
    {"date": "2022-10-17", "albumin": 4.1, "creatinine": 0.94, "glucose": 97.0, "crp": 2.2,
     "lymphocyte_pct": 25.0, "mcv": 91.0, "rdw": 13.6, "alk_phosphatase": 69.0, "wbc": 7.0,
     "total_cholesterol": 194.0, "ldl": 122.0, "hdl": 58.0, "triglycerides": 96.0, "apob": 92.0,
     "hba1c": 5.4, "vitamin_d": 34.0, "ferritin": 36.0},
    {"date": "2023-10-30", "albumin": 4.2, "creatinine": 0.95, "glucose": 96.0, "crp": 1.9,
     "lymphocyte_pct": 26.0, "mcv": 92.0, "rdw": 13.4, "alk_phosphatase": 67.0, "wbc": 6.8,
     "total_cholesterol": 188.0, "ldl": 116.0, "hdl": 60.0, "triglycerides": 90.0, "apob": 88.0,
     "hba1c": 5.4, "vitamin_d": 38.0, "ferritin": 41.0},
    {"date": "2024-11-18", "albumin": 4.2, "creatinine": 0.95, "glucose": 95.0, "crp": 1.7,
     "lymphocyte_pct": 26.0, "mcv": 92.0, "rdw": 13.3, "alk_phosphatase": 66.0, "wbc": 6.6,
     "total_cholesterol": 184.0, "ldl": 111.0, "hdl": 61.0, "triglycerides": 86.0, "apob": 85.0,
     "hba1c": 5.3, "vitamin_d": 42.0, "ferritin": 45.0},
    {"date": "2026-02-14", "albumin": 4.2, "creatinine": 0.95, "glucose": 95.0, "crp": 1.5,
     "lymphocyte_pct": 27.0, "mcv": 92.0, "rdw": 13.2, "alk_phosphatase": 65.0, "wbc": 6.5,
     "total_cholesterol": 181.0, "ldl": 108.0, "hdl": 62.0, "triglycerides": 82.0, "apob": 83.0,
     "hba1c": 5.3, "vitamin_d": 44.0, "ferritin": 48.0},
]

# Fictional 23andMe-format panel. Positions are GRCh37 build coordinates for
# the public rsIDs; the genotypes are invented for Maya Chen.
SYNTHETIC_GENOME = """# Fictional Build Week fixture; not a real person's DNA
# rsid\tchromosome\tposition\tgenotype
rs762551\t15\t75041917\tAC
rs4680\t22\t19951271\tAG
rs1801133\t1\t11856378\tCT
rs1801131\t1\t11854476\tAA
rs7903146\t10\t114758349\tCT
rs9939609\t16\t53820527\tAT
rs4988235\t2\t136608646\tCT
rs671\t12\t112241766\tGG
rs1815739\t11\t66328095\tCT
rs429358\t19\t45411941\tTT
rs7412\t19\t45412079\tCC
"""

# Dated interventions in Maya's journal. Each has a planted effect in the
# history generator; the before/after analysis has to recover it (or not).
SYNTHETIC_INTERVENTIONS: list[dict[str, str]] = [
    {"date": "2025-10-06", "title": "Started magnesium glycinate at night", "category": "supplement",
     "planted": "none: the generator adds no effect, so an honest analysis should find nothing."},
    {"date": "2026-01-12", "title": "Moved bedtime 45 minutes earlier", "category": "behaviour",
     "planted": "sleep duration baseline rises by about 0.3 h."},
    {"date": "2026-03-02", "title": "Began zone-2 cycling three mornings a week", "category": "training",
     "planted": "HRV baseline rises by about 1 ms and resting heart rate falls by about 0.8 bpm."},
]

HABIT_COLUMNS = ["meditation", "breathwork", "cold_exposure", "morning_light", "evening_walk"]

HISTORY_START = date(2025, 7, 21)
WINDOW_START = date(2026, 4, 28)
HISTORY_DAYS = 365


def generate_records(days: int = 84, seed: int = 56) -> list[dict[str, Any]]:
    """Generate a plausible but entirely fictional wearable and habit history.

    Frozen: this is the judged 84-day window. Do not change its arithmetic.
    """
    rng = random.Random(seed)
    start = WINDOW_START
    missing_days = {13, 38, 61, 72}
    conditions: list[dict[str, float]] = []
    for index in range(days):
        cutoff = 1.0 if rng.random() > 0.43 else 0.0
        alcohol = 1.0 if rng.random() < 0.11 else 0.0
        training = float(rng.choice([0, 0, 1, 1, 1, 2]))
        conditions.append({"cutoff": cutoff, "alcohol": alcohol, "training": training})

    records: list[dict[str, Any]] = []
    for index in range(days):
        if index in missing_days:
            continue
        day = start + timedelta(days=index)
        current = conditions[index]
        prior = conditions[index - 1] if index else {"cutoff": 0.0, "alcohol": 0.0, "training": 0.0}
        weekly = math.sin(2 * math.pi * index / 7)
        hrv = 46.5 + 4.3 * prior["cutoff"] - 3.2 * prior["alcohol"] + 0.7 * prior["training"] + weekly + rng.gauss(0, 3.6)
        sleep = 6.85 + 0.34 * prior["cutoff"] - 0.42 * prior["alcohol"] + 0.08 * weekly + rng.gauss(0, 0.42)
        resting = 60.8 - 1.6 * prior["cutoff"] + 1.4 * prior["alcohol"] - 0.2 * prior["training"] + rng.gauss(0, 1.7)
        mood = 6.7 + 0.25 * prior["cutoff"] + rng.gauss(0, 0.8)
        record: dict[str, Any] = {
            "date": day.isoformat(),
            "caffeine_cutoff_2pm": current["cutoff"],
            "caffeine_mg": round(155 + (1 - current["cutoff"]) * 95 + rng.gauss(0, 35), 1),
            "training_load": current["training"],
            "alcohol_units": current["alcohol"],
            "meditation": 1.0 if rng.random() < 0.46 else 0.0,
            "hrv_ms": round(hrv, 1),
            "sleep_hours": round(sleep, 2),
            "resting_hr": round(resting, 1),
            "mood": round(max(1, min(10, mood)), 1),
        }
        if index in {24, 54}:
            record["hrv_ms"] = None
        records.append(record)
    return records


def _planted_baselines(day: date) -> dict[str, float]:
    """Baselines before the frozen window, stepping up at each planted intervention
    so the series ends at the frozen window's levels (HRV 46.5, sleep 6.85, RHR 60.8)."""
    hrv, sleep, resting = 45.5, 6.55, 61.6
    if day >= date(2026, 1, 12):
        sleep += 0.30
    if day >= date(2026, 3, 2):
        hrv += 1.0
        resting -= 0.8
    return {"hrv": hrv, "sleep": sleep, "resting": resting}


def generate_history(seed: int = 2026) -> list[dict[str, Any]]:
    """One year of fictional nights and habits ending on the frozen window.

    Days before WINDOW_START are generated here with modest planted effects:
    meditation +0.9 ms next-day HRV, cold exposure -0.8 bpm resting HR and
    +0.5 ms HRV, morning light +0.15 h sleep; breathwork and the evening
    walk do nothing. Days inside the window are taken verbatim from
    ``generate_records`` and only receive the four new habit columns.
    """
    rng = random.Random(seed)
    head_days = (WINDOW_START - HISTORY_START).days
    missing = {rng.randrange(head_days) for _ in range(11)}
    conditions: list[dict[str, float]] = []
    for index in range(head_days):
        conditions.append({
            "cutoff": 1.0 if rng.random() > 0.47 else 0.0,
            "alcohol": 1.0 if rng.random() < 0.12 else 0.0,
            "training": float(rng.choice([0, 0, 1, 1, 1, 2])),
            "meditation": 1.0 if rng.random() < 0.52 else 0.0,
            "breathwork": 1.0 if rng.random() < 0.38 else 0.0,
            "cold_exposure": 1.0 if rng.random() < 0.31 else 0.0,
            "morning_light": 1.0 if rng.random() < 0.58 else 0.0,
            "evening_walk": 1.0 if rng.random() < 0.44 else 0.0,
        })

    zero = {key: 0.0 for key in conditions[0]}
    records: list[dict[str, Any]] = []
    for index in range(head_days):
        day = HISTORY_START + timedelta(days=index)
        current = conditions[index]
        prior = conditions[index - 1] if index else zero
        base = _planted_baselines(day)
        weekly = math.sin(2 * math.pi * index / 7)
        hrv = (base["hrv"] + 4.3 * prior["cutoff"] - 3.2 * prior["alcohol"] + 0.7 * prior["training"]
               + 0.9 * prior["meditation"] + 0.5 * prior["cold_exposure"] + weekly + rng.gauss(0, 3.6))
        sleep = (base["sleep"] + 0.34 * prior["cutoff"] - 0.42 * prior["alcohol"] + 0.15 * prior["morning_light"]
                 + 0.08 * weekly + rng.gauss(0, 0.42))
        resting = (base["resting"] - 1.6 * prior["cutoff"] + 1.4 * prior["alcohol"] - 0.2 * prior["training"]
                   - 0.8 * prior["cold_exposure"] + rng.gauss(0, 1.7))
        mood = 6.6 + 0.25 * prior["cutoff"] + 0.2 * prior["meditation"] + rng.gauss(0, 0.8)
        record: dict[str, Any] = {
            "date": day.isoformat(),
            "caffeine_cutoff_2pm": current["cutoff"],
            "caffeine_mg": round(155 + (1 - current["cutoff"]) * 95 + rng.gauss(0, 35), 1),
            "training_load": current["training"],
            "alcohol_units": current["alcohol"],
            "meditation": current["meditation"],
            "hrv_ms": round(hrv, 1),
            "sleep_hours": round(sleep, 2),
            "resting_hr": round(resting, 1),
            "mood": round(max(1, min(10, mood)), 1),
            "breathwork": current["breathwork"],
            "cold_exposure": current["cold_exposure"],
            "morning_light": current["morning_light"],
            "evening_walk": current["evening_walk"],
        }
        if index in missing:
            continue
        if rng.random() < 0.02:
            record["hrv_ms"] = None
        records.append(record)

    extra_rng = random.Random(seed + 1)
    for record in generate_records():
        row = dict(record)
        row["breathwork"] = 1.0 if extra_rng.random() < 0.38 else 0.0
        row["cold_exposure"] = 1.0 if extra_rng.random() < 0.31 else 0.0
        row["morning_light"] = 1.0 if extra_rng.random() < 0.58 else 0.0
        row["evening_walk"] = 1.0 if extra_rng.random() < 0.44 else 0.0
        records.append(row)
    return records


SUPPLEMENT_SPANS: list[dict[str, Any]] = [
    # name, first day, last day (None = still current), weekly frequency 0..7
    {"name": "vitamin_d3", "first": "2023-01-09", "last": None, "per_week": 6, "winter_only": True},
    {"name": "omega_3", "first": "2023-03-20", "last": None, "per_week": 5},
    {"name": "magnesium_glycinate", "first": "2025-10-06", "last": None, "per_week": 6},
    {"name": "creatine", "first": "2024-03-04", "last": "2025-02-21", "per_week": 6},
    {"name": "electrolytes", "first": "2023-06-05", "last": None, "per_week": 2},
    {"name": "iron_bisglycinate", "first": "2023-02-13", "last": "2023-09-29", "per_week": 5},
    {"name": "probiotic", "first": "2024-08-12", "last": "2024-11-30", "per_week": 7},
]


def generate_supplements(end: date = date(2026, 7, 20), seed: int = 7) -> list[dict[str, Any]]:
    """Daily wide table: one column per supplement, 1 on days taken."""
    rng = random.Random(seed)
    start = date(2023, 1, 1)
    names = [spec["name"] for spec in SUPPLEMENT_SPANS]
    rows: list[dict[str, Any]] = []
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        row: dict[str, Any] = {"date": day.isoformat()}
        for spec in SUPPLEMENT_SPANS:
            first = date.fromisoformat(spec["first"])
            last = date.fromisoformat(spec["last"]) if spec["last"] else end
            taken = ""
            if first <= day <= last:
                in_season = not spec.get("winter_only") or day.month in (10, 11, 12, 1, 2, 3)
                if in_season and rng.random() < spec["per_week"] / 7:
                    taken = "1"
            row[spec["name"]] = taken
        rows.append(row)
    return rows if names else []


def write_csv(path: str | Path, records: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(records[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_supporting_fixtures(labs_path: str | Path, genome_path: str | Path) -> None:
    labs_path = Path(labs_path)
    genome_path = Path(genome_path)
    labs_path.parent.mkdir(parents=True, exist_ok=True)
    genome_path.parent.mkdir(parents=True, exist_ok=True)
    labs_path.write_text(json.dumps(SYNTHETIC_LABS, indent=2) + "\n", encoding="utf-8")
    genome_path.write_text(SYNTHETIC_GENOME, encoding="utf-8")
