from __future__ import annotations

import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from liveforever_lab.analysis import analyze_dataset, binary_effect, load_csv, quality_report
from liveforever_lab.synthetic import generate_records


class DataIntegrityTests(unittest.TestCase):
    def test_chart_exposure_uses_the_prior_calendar_day_not_prior_row(self):
        records = [
            {"date": "2026-01-01", "caffeine_cutoff_2pm": 1, "hrv_ms": 40},
            {"date": "2026-01-02", "caffeine_cutoff_2pm": 0, "hrv_ms": 50},
            {"date": "2026-01-04", "caffeine_cutoff_2pm": 1, "hrv_ms": 45},
        ]
        timeline = analyze_dataset(records)["timeline"]
        self.assertEqual([row["prior_day_caffeine_cutoff_2pm"] for row in timeline], [None, 1, None])

    def test_shuffling_records_preserves_window_timeline_and_results(self):
        records = generate_records()
        expected = analyze_dataset(records)
        shuffled = copy.deepcopy(records)
        random.Random(21).shuffle(shuffled)
        original = copy.deepcopy(shuffled)
        self.assertEqual(analyze_dataset(shuffled), expected)
        self.assertEqual(shuffled, original, "analysis must not reorder the caller's records")

    def test_duplicate_days_are_rejected_instead_of_silently_replacing_evidence(self):
        records = generate_records(days=18)
        records.append({**records[0], "hrv_ms": 999.0})
        for analyze in (
            analyze_dataset,
            lambda rows: binary_effect(rows, "caffeine_cutoff_2pm", "hrv_ms"),
            lambda rows: quality_report(rows, "caffeine_cutoff_2pm", "hrv_ms"),
        ):
            with self.subTest(analyze=analyze):
                with self.assertRaisesRegex(ValueError, "Duplicate date"):
                    analyze(records)

    def test_non_finite_values_are_rejected_before_statistics_or_json(self):
        for value in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value):
                records = generate_records(days=18)
                records[1]["hrv_ms"] = value
                with self.assertRaisesRegex(ValueError, "finite"):
                    analyze_dataset(records)

    def test_empty_analysis_has_an_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            analyze_dataset([])

    def test_dates_must_be_canonical_calendar_dates(self):
        for invalid in ["20260201", "2026-02-30", "2026-02-01T10:00:00", None]:
            with self.subTest(invalid=invalid):
                records = generate_records(days=18)
                records[0]["date"] = invalid
                with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                    analyze_dataset(records)

    def test_missing_outcomes_remain_missing_and_json_is_strict(self):
        records = generate_records(days=18)
        for record in records:
            record["hrv_ms"] = None
        result = analyze_dataset(records)
        self.assertIsNone(result["primary_effect"]["effect"])
        self.assertEqual(result["primary_effect"]["n_on"], 0)
        self.assertEqual(result["primary_effect"]["n_off"], 0)
        json.dumps(result, allow_nan=False)

    def test_single_observation_per_condition_has_no_precision_claim(self):
        records = [
            {"date": "2026-01-01", "cutoff": 1, "outcome": 100},
            {"date": "2026-01-02", "cutoff": 0, "outcome": 110},
            {"date": "2026-01-03", "cutoff": 0, "outcome": 90},
        ]
        result = binary_effect(records, "cutoff", "outcome", minimum_per_group=1)
        self.assertEqual(result.effect, 20)
        self.assertIsNone(result.ci_low)
        self.assertIsNone(result.ci_high)
        self.assertIn("interval", result.interpretation)

    def test_invalid_analysis_parameters_do_not_change_pairing_silently(self):
        records = generate_records(days=18)
        for lag in [-1, 0.5, True]:
            with self.subTest(lag=lag):
                with self.assertRaises(ValueError):
                    binary_effect(records, "caffeine_cutoff_2pm", "hrv_ms", lag_days=lag)
        with self.assertRaises(ValueError):
            binary_effect(records, "caffeine_cutoff_2pm", "hrv_ms", minimum_per_group=0)

    def test_csv_rejects_ambiguous_headers_and_non_finite_cells(self):
        folder = Path(tempfile.mkdtemp(prefix="liveforever-integrity-"))
        for index, text in enumerate([
            "date,hrv_ms,hrv_ms\n2026-01-01,40,50\n",
            "hrv_ms\n40\n",
            "date,hrv_ms\n2026-01-01,NaN\n",
            "date,hrv_ms\n2026-01-01,40,50\n",
        ]):
            with self.subTest(index=index):
                source = folder / f"invalid-{index}.csv"
                source.write_text(text)
                with self.assertRaises(ValueError):
                    load_csv(source)

    def test_csv_accepts_utf8_bom_and_preserves_blank_observations(self):
        source = Path(tempfile.mkdtemp(prefix="liveforever-integrity-")) / "data.csv"
        source.write_text("\ufeffdate,hrv_ms\n2026-01-02,\n2026-01-01,42\n")
        self.assertEqual(load_csv(source), [
            {"date": "2026-01-01", "hrv_ms": 42.0},
            {"date": "2026-01-02", "hrv_ms": None},
        ])
