from __future__ import annotations

import unittest
from datetime import date, timedelta

from liveforever_lab.analysis import (
    analyze_dataset,
    binary_effect,
    pearson_with_interval,
    quality_report,
)
from liveforever_lab.synthetic import generate_records


class AnalysisTests(unittest.TestCase):
    def test_synthetic_primary_signal_is_recovered(self) -> None:
        analysis = analyze_dataset(generate_records())
        effect = analysis["primary_effect"]
        self.assertGreater(effect["effect"], 2.0)
        self.assertGreater(effect["ci_low"], 0.0)
        self.assertGreaterEqual(effect["n_on"], 30)
        self.assertGreaterEqual(effect["n_off"], 30)

    def test_lag_pairs_exposure_with_next_day(self) -> None:
        start = date(2026, 1, 1)
        records = []
        conditions = [1, 0, 1, 0, 1, 0]
        outcomes = [0, 10, 1, 10, 1, 10]
        for index, (condition, outcome) in enumerate(zip(conditions, outcomes)):
            records.append({
                "date": (start + timedelta(days=index)).isoformat(),
                "cutoff": condition,
                "outcome": outcome,
            })
        effect = binary_effect(records, "cutoff", "outcome", lag_days=1, minimum_per_group=1)
        self.assertEqual(effect.n_on, 3)
        self.assertEqual(effect.n_off, 2)
        self.assertGreater(effect.effect, 8)

    def test_small_groups_are_labeled_early(self) -> None:
        records = generate_records(days=18)
        effect = binary_effect(records, "caffeine_cutoff_2pm", "hrv_ms")
        self.assertIn("minimum sample", effect.interpretation)

    def test_quality_report_flags_missing_calendar_days(self) -> None:
        records = generate_records()
        quality = quality_report(records, "caffeine_cutoff_2pm", "hrv_ms")
        self.assertLess(quality["coverage"], 1.0)
        self.assertTrue(any("coverage" in warning.lower() for warning in quality["warnings"]))

    def test_quality_report_preserves_observational_boundary(self) -> None:
        quality = quality_report(generate_records(), "caffeine_cutoff_2pm", "hrv_ms")
        self.assertTrue(any("not a randomized causal" in warning for warning in quality["warnings"]))

    def test_pearson_interval_contains_ordered_bounds(self) -> None:
        result = pearson_with_interval(generate_records(), "caffeine_mg", "sleep_hours")
        self.assertIsNotNone(result["r"])
        self.assertLess(result["ci_low"], result["r"])
        self.assertLess(result["r"], result["ci_high"])


if __name__ == "__main__":
    unittest.main()

