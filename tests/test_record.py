"""The post-submission full record must extend the judged window without touching it."""

from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from liveforever_lab.analysis import analyze_dataset, load_csv
from liveforever_lab.genomics import interpret_panel, parse_23andme
from liveforever_lab.habits import habit_effects, intervention_effects
from liveforever_lab.labs import lab_record
from liveforever_lab.phenoage import calculate
from liveforever_lab.record import build_record
from liveforever_lab.synthetic import (
    HABIT_COLUMNS,
    PERSONA,
    SYNTHETIC_GENOME,
    SYNTHETIC_INTERVENTIONS,
    SYNTHETIC_LAB_DRAWS,
    SYNTHETIC_LABS,
    WINDOW_START,
    generate_history,
    generate_records,
    generate_supplements,
)

ROOT = Path(__file__).resolve().parent.parent
FEATURED = {"effect": 3.94, "ci_low": 1.13, "ci_high": 6.42, "n_on": 36, "n_off": 37}


def _walk_numbers(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_numbers(item)
    elif isinstance(value, float):
        yield value


class FrozenWindowTests(unittest.TestCase):
    def test_history_tail_is_the_judged_window_verbatim(self) -> None:
        history = generate_history()
        window = generate_records()
        tail = [row for row in history if row["date"] >= WINDOW_START.isoformat()]
        self.assertEqual(len(tail), len(window))
        self.assertEqual([row["date"] for row in tail], [row["date"] for row in window])
        for extended, frozen in zip(tail, window):
            for key, value in frozen.items():
                self.assertEqual(extended[key], value, f"{frozen['date']} {key} changed")

    def test_checked_in_csv_matches_history_tail(self) -> None:
        with (ROOT / "examples" / "maya_daily.csv").open(newline="", encoding="utf-8") as handle:
            checked_in = list(csv.DictReader(handle))
        with (ROOT / "examples" / "maya_history.csv").open(newline="", encoding="utf-8") as handle:
            history = [row for row in csv.DictReader(handle) if row["date"] >= WINDOW_START.isoformat()]
        self.assertEqual(len(checked_in), 80)
        self.assertEqual(len(history), 80)
        for frozen, extended in zip(checked_in, history):
            for key, value in frozen.items():
                self.assertEqual(extended[key], value, f"{frozen['date']} {key} differs from maya_daily.csv")

    def test_featured_caffeine_numbers_are_recovered_from_the_history_tail(self) -> None:
        history = generate_history()
        tail = [row for row in history if row["date"] >= WINDOW_START.isoformat()]
        primary = analyze_dataset(tail)["primary_effect"]
        for key, expected in FEATURED.items():
            self.assertEqual(primary[key], expected, key)
        checked_in = json.loads((ROOT / "demo" / "analysis.json").read_text(encoding="utf-8"))
        for key, expected in FEATURED.items():
            self.assertEqual(checked_in["analysis"]["primary_effect"][key], expected, key)

    def test_history_is_deterministic(self) -> None:
        self.assertEqual(generate_history(), generate_history())
        self.assertEqual(generate_supplements(), generate_supplements())


class LabTests(unittest.TestCase):
    def test_phenoage_is_computed_for_every_draw_and_latest_matches_snapshot(self) -> None:
        labs = lab_record(SYNTHETIC_LAB_DRAWS, PERSONA["birth_date"])
        self.assertEqual(len(labs["draws"]), 7)
        self.assertTrue(all(draw["phenoage"] is not None for draw in labs["draws"]))
        self.assertEqual(labs["latest"]["phenoage"], calculate(SYNTHETIC_LABS).phenoage)
        self.assertEqual(labs["latest"]["age"], 34.0)
        gaps = [draw["gap_years"] for draw in labs["draws"]]
        self.assertGreater(gaps[0], 0)
        self.assertLess(gaps[-1], 0)

    def test_incomplete_draw_is_reported_not_imputed(self) -> None:
        partial = dict(SYNTHETIC_LAB_DRAWS[0])
        partial.pop("crp")
        labs = lab_record([partial], PERSONA["birth_date"])
        self.assertIsNone(labs["draws"][0]["phenoage"])
        self.assertIn("crp", labs["draws"][0]["note"])

    def test_out_of_range_flags_use_the_stated_ranges(self) -> None:
        labs = lab_record(SYNTHETIC_LAB_DRAWS, PERSONA["birth_date"])
        self.assertIn("crp", labs["draws"][0]["outside_range"])
        self.assertNotIn("crp", labs["draws"][-1]["outside_range"])


class HabitTests(unittest.TestCase):
    def test_effects_carry_intervals_and_honest_nulls(self) -> None:
        rows = habit_effects(generate_history(), HABIT_COLUMNS, ["hrv_ms"])
        self.assertEqual(len(rows), len(HABIT_COLUMNS))
        for row in rows:
            self.assertIsNotNone(row["ci_low"])
            self.assertLessEqual(row["ci_low"], row["effect"])
            self.assertLessEqual(row["effect"], row["ci_high"])
        readings = {row["habit"]: row["reading"] for row in rows}
        self.assertEqual(readings["evening_walk"], "nothing detected")
        self.assertEqual(readings["breathwork"], "nothing detected")

    def test_planted_cold_exposure_effect_on_resting_hr_is_recovered(self) -> None:
        rows = habit_effects(generate_history(), ["cold_exposure"], ["resting_hr"])
        self.assertLess(rows[0]["effect"], 0)
        self.assertLess(rows[0]["ci_high"], 0)

    def test_intervention_windows_report_counts_and_insufficient_data(self) -> None:
        history = generate_history()
        results = intervention_effects(history, SYNTHETIC_INTERVENTIONS)
        self.assertEqual(len(results), 3)
        for item in results:
            for effect in item["effects"]:
                self.assertGreaterEqual(effect["n_before"], 10)
        too_early = intervention_effects(history, [{"date": "2025-07-25", "title": "x", "category": "y"}])
        self.assertEqual(too_early[0]["effects"][0]["reading"], "insufficient")


class GenomeTests(unittest.TestCase):
    def _genotypes(self) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "genome.txt"
            path.write_text(SYNTHETIC_GENOME, encoding="utf-8")
            return parse_23andme(path)

    def test_panel_interprets_every_fixture_marker_with_apoe_first(self) -> None:
        findings = interpret_panel(self._genotypes())
        self.assertEqual(findings[0]["gene"], "APOE")
        self.assertEqual(findings[0]["call"], "e3/e3")
        self.assertEqual(len(findings), 10)
        self.assertTrue(all("never decides" in item["boundary"] for item in findings))

    def test_mthfr_strand_flip_is_only_a_fallback(self) -> None:
        flipped = interpret_panel({"rs1801133": "AG"})
        self.assertEqual(flipped[0]["genotype"], "CT")
        direct = interpret_panel({"rs1801133": "CT"})
        self.assertEqual(direct[0]["genotype"], "CT")

    def test_unknown_or_missing_genotypes_do_not_invent_findings(self) -> None:
        self.assertEqual(interpret_panel({}), [])
        self.assertEqual(interpret_panel({"rs762551": "GG"}), [])
        partial = interpret_panel({"rs429358": "TT"})
        self.assertEqual(partial, [])


class RecordTests(unittest.TestCase):
    def test_record_is_finite_and_featured_numbers_match(self) -> None:
        analysis = json.loads((ROOT / "demo" / "analysis.json").read_text(encoding="utf-8"))["analysis"]
        record = build_record(
            load_csv(ROOT / "examples" / "maya_history.csv"),
            lab_draws=SYNTHETIC_LAB_DRAWS,
            genotypes=parse_23andme(ROOT / "examples" / "maya_genome.txt"),
            supplements=generate_supplements(),
            analysis=analysis,
        )
        self.assertTrue(all(math.isfinite(value) for value in _walk_numbers(record)))
        self.assertEqual(record["featured"]["effect"], FEATURED["effect"])
        self.assertEqual(record["hero"]["phenoage"], analysis["longevity_snapshot"]["phenoage"])
        self.assertEqual(record["scope"]["calendar_days"], 365)
        checked_in = json.loads((ROOT / "demo" / "record.json").read_text(encoding="utf-8"))
        self.assertEqual(checked_in["hero"], record["hero"])
        self.assertEqual(checked_in["habits"]["effects"], record["habits"]["effects"])
        self.assertEqual(checked_in["daily"], record["daily"])

    def test_daily_mean_is_the_trailing_seven_day_mean(self) -> None:
        history = load_csv(ROOT / "examples" / "maya_history.csv")
        record = json.loads((ROOT / "demo" / "record.json").read_text(encoding="utf-8"))
        hrv = next(s for s in record["daily"] if s["key"] == "hrv_ms")
        self.assertEqual(len(hrv["series"]), len(history))
        i = 200
        window = [r["hrv_ms"] for r in history[i - 6: i + 1] if r["hrv_ms"] is not None]
        self.assertAlmostEqual(hrv["series"][i]["mean7"], round(sum(window) / len(window), 1))
        self.assertIsNone(hrv["series"][0]["mean7"])


if __name__ == "__main__":
    unittest.main()
