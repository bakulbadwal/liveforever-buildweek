"""Command-line entry point for the synthetic LiveForever demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_dataset, load_csv
from .genomics import caffeine_hypothesis, parse_23andme
from .phenoage import calculate
from .planner import build_plan
from .synthetic import SYNTHETIC_LABS, generate_records, write_csv, write_supporting_fixtures


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
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fictional LiveForever evidence-lab demo")
    parser.add_argument("--data", type=Path, default=Path("examples/maya_daily.csv"))
    parser.add_argument("--output", type=Path, default=Path("demo/analysis.json"))
    args = parser.parse_args()
    payload = build_demo(args.data, args.output)
    effect = payload["analysis"]["primary_effect"]
    quality = payload["analysis"]["quality"]
    print(
        f"Built fictional demo: {effect['n_on'] + effect['n_off']} paired nights, "
        f"effect {effect['effect']:+.2f} ms, quality {quality['grade']} ({quality['score']}/100)."
    )


if __name__ == "__main__":
    main()
