"""Command-line entry point for the synthetic LiveForever demonstration.

One command regenerates every file the demo reads:

    PYTHONPATH=src python3 -m liveforever_lab.cli

It writes the frozen 84-day window (``examples/maya_daily.csv``), the
supporting fixtures, the featured contract (``demo/analysis.json``), and the
full-record extension (``examples/maya_history.csv``,
``examples/maya_labs_history.json``, ``examples/maya_supplements.csv``,
``demo/record.json``).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_dataset, load_csv
from .genomics import caffeine_hypothesis, parse_23andme
from .phenoage import calculate
from .planner import build_plan
from .record import build_record
from .synthetic import (
    SYNTHETIC_LAB_DRAWS,
    SYNTHETIC_LABS,
    generate_history,
    generate_records,
    generate_supplements,
    write_csv,
    write_supporting_fixtures,
)


def build_demo(data_path: Path, output_path: Path) -> dict:
    records = generate_records()
    write_csv(data_path, records)
    labs_path = data_path.with_name("maya_labs.json")
    genome_path = data_path.with_name("maya_genome.txt")
    write_supporting_fixtures(labs_path, genome_path)
    analysis = analyze_dataset(
        load_csv(data_path),
        genomics_context=caffeine_hypothesis(parse_23andme(genome_path)),
        longevity_snapshot=calculate(SYNTHETIC_LABS).as_dict(),
    )
    payload = {"analysis": analysis, "plan": build_plan(analysis)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return payload


def build_record_demo(data_path: Path, output_path: Path, analysis: dict) -> dict:
    history_path = data_path.with_name("maya_history.csv")
    labs_history_path = data_path.with_name("maya_labs_history.json")
    supplements_path = data_path.with_name("maya_supplements.csv")
    genome_path = data_path.with_name("maya_genome.txt")
    write_csv(history_path, generate_history())
    labs_history_path.write_text(json.dumps(SYNTHETIC_LAB_DRAWS, indent=2) + "\n", encoding="utf-8")
    supplements = generate_supplements()
    write_csv(supplements_path, supplements)
    record = build_record(
        load_csv(history_path),
        lab_draws=json.loads(labs_history_path.read_text(encoding="utf-8")),
        genotypes=parse_23andme(genome_path),
        supplements=supplements,
        analysis=analysis,
    )
    output_path.write_text(json.dumps(record, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fictional LiveForever evidence-lab demo")
    parser.add_argument("--data", type=Path, default=Path("examples/maya_daily.csv"))
    parser.add_argument("--output", type=Path, default=Path("demo/analysis.json"))
    parser.add_argument("--record", type=Path, default=Path("demo/record.json"))
    args = parser.parse_args()
    payload = build_demo(args.data, args.output)
    effect = payload["analysis"]["primary_effect"]
    quality = payload["analysis"]["quality"]
    print(
        f"Built fictional demo: {effect['n_on'] + effect['n_off']} paired nights, "
        f"effect {effect['effect']:+.2f} ms, quality {quality['grade']} ({quality['score']}/100)."
    )
    record = build_record_demo(args.data, args.record, payload["analysis"])
    scope = record["scope"]
    print(
        f"Built full record: {scope['nights_recorded']} nights, {scope['lab_draws']} lab draws, "
        f"{scope['genome_markers']} genome findings, PhenoAge {record['hero']['phenoage']} "
        f"({record['hero']['gap_years']:+.2f} y)."
    )


if __name__ == "__main__":
    main()
