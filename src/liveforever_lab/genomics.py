"""Privacy-preserving parsing for a small, explicitly synthetic demo panel.

Real raw genomic files should remain local and gitignored. The public demo
contains one fictional 23andMe-format fixture and emits only a derived,
uncertainty-aware hypothesis annotation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_23andme(path: str | Path) -> dict[str, str]:
    genotypes: dict[str, str] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) < 4:
            continue
        genotype = "".join(sorted(parts[3].upper()))
        if genotype not in {"--", "__", ""}:
            genotypes[parts[0]] = genotype
    return genotypes


def caffeine_hypothesis(genotypes: dict[str, str]) -> dict[str, Any]:
    genotype = genotypes.get("rs762551")
    if genotype is None:
        return {
            "gene": "CYP1A2", "marker": "rs762551", "synthetic_genotype": None,
            "annotation": "Marker absent; no genetic hypothesis annotation was produced.",
            "confidence": "not available",
        }
    context = {
        "AA": "Often studied as a faster-metabolism pattern, with effects varying by ancestry and context.",
        "AC": "Often studied as an intermediate or slower-metabolism pattern; late caffeine is a testable hypothesis.",
        "CC": "Often studied as a slower-metabolism pattern; late caffeine is a testable hypothesis.",
    }.get(genotype, "Genotype is outside this demo's curated annotation set.")
    return {
        "gene": "CYP1A2", "marker": "rs762551", "synthetic_genotype": genotype,
        "annotation": context,
        "confidence": "hypothesis context only",
        "boundary": "A single marker is probabilistic, population-dependent, and not diagnostic or prescriptive.",
    }

