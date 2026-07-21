from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from liveforever_lab.genomics import caffeine_hypothesis, parse_23andme
from liveforever_lab.phenoage import calculate
from liveforever_lab.planner import build_plan
from liveforever_lab.synthetic import SYNTHETIC_LABS, generate_records
from liveforever_lab.analysis import analyze_dataset


class ContextTests(unittest.TestCase):
    def test_synthetic_genome_parser_normalizes_genotype(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "genome.txt"
            path.write_text("# synthetic\nrs762551\t15\t75041917\tCA\n", encoding="utf-8")
            genotypes = parse_23andme(path)
        self.assertEqual(genotypes["rs762551"], "AC")
        self.assertEqual(caffeine_hypothesis(genotypes)["confidence"], "hypothesis context only")

    def test_missing_genomic_marker_does_not_invent_a_call(self) -> None:
        context = caffeine_hypothesis({})
        self.assertIsNone(context["synthetic_genotype"])
        self.assertEqual(context["confidence"], "not available")

    def test_phenoage_requires_all_inputs(self) -> None:
        incomplete = dict(SYNTHETIC_LABS)
        incomplete.pop("crp")
        with self.assertRaisesRegex(ValueError, "crp"):
            calculate(incomplete)

    def test_phenoage_demo_result_is_plausible(self) -> None:
        result = calculate(SYNTHETIC_LABS)
        self.assertGreater(result.phenoage, 20)
        self.assertLess(result.phenoage, 45)
        self.assertIn("not a clinical age", result.boundary)

    def test_plan_is_balanced_and_reproducible(self) -> None:
        analysis = analyze_dataset(generate_records())
        first = build_plan(analysis)
        second = build_plan(analysis)
        conditions = [day["condition"] for day in first["schedule"]]
        self.assertEqual(first, second)
        self.assertEqual(conditions.count("Cutoff by 2 PM"), 7)
        self.assertEqual(conditions.count("Usual timing"), 7)
        self.assertIn("interval excludes zero", first["decision_rule"])


if __name__ == "__main__":
    unittest.main()

