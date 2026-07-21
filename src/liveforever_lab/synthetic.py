"""Deterministic fictional data for the public Build Week demonstration."""

from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

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

SYNTHETIC_GENOME = """# Fictional Build Week fixture; not a real person's DNA
# rsid\tchromosome\tposition\tgenotype
rs762551\t15\t75041917\tAC
"""


def generate_records(days: int = 84, seed: int = 56) -> list[dict[str, Any]]:
    """Generate a plausible but entirely fictional wearable and habit history."""
    rng = random.Random(seed)
    start = date(2026, 4, 28)
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
