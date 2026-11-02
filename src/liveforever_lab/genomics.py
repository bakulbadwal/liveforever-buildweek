"""Privacy-preserving parsing and cautious interpretation of a small SNP panel.

Real raw genomic files should remain local and gitignored. The public demo
contains one fictional 23andMe-format fixture and emits only derived,
uncertainty-aware context: what a genotype is often studied for, and which
part of the tracked record it points at. Never a verdict.

The genotype descriptions are general published knowledge about each
variant. Strand handling follows the convention that 23andMe reports the
dbSNP plus strand; the two MTHFR markers are checked both ways because some
chip versions reported them flipped.
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


# Curated single-SNP panel. Genotype keys are alphabetically sorted alleles.
# "uses" says which part of the tracked record the marker points at; it is
# written for the fictional demo persona and names only data the demo holds.
PANEL: dict[str, dict[str, Any]] = {
    "rs762551": {
        "gene": "CYP1A2", "name": "Caffeine metabolism", "category": "Pharmacogenomics",
        "chromosome": "15",
        "genotypes": {
            "AA": "Often studied as a faster caffeine-metabolism pattern.",
            "AC": "Often studied as an intermediate or slower pattern; caffeine may linger into the evening.",
            "CC": "Often studied as a slower pattern; late-day caffeine may affect sleep more.",
        },
        "uses": "This is why caffeine timing became the question tested on this page.",
    },
    "rs4680": {
        "gene": "COMT", "name": "Dopamine clearance (Val158Met)", "category": "Pharmacogenomics",
        "chromosome": "22",
        "genotypes": {
            "GG": "Val/Val, often studied as faster dopamine clearance and lower stimulant sensitivity.",
            "AG": "Val/Met, an intermediate pattern.",
            "AA": "Met/Met, often studied as slower clearance and higher stimulant sensitivity.",
        },
        "uses": "Reads alongside the caffeine dose column: total milligrams per day is logged, so sensitivity can be checked against next-day resting heart rate.",
    },
    "rs1801133": {
        "gene": "MTHFR", "name": "Folate metabolism (C677T)", "category": "Pharmacogenomics",
        "chromosome": "1",
        "genotypes": {
            "CC": "Typical enzyme activity.",
            "CT": "One copy of the variant; often studied as mildly reduced enzyme activity.",
            "TT": "Two copies; often studied as substantially reduced enzyme activity.",
        },
        "uses": "Homocysteine is not on any of the seven lab panels yet. This marker nominates it for the next draw; it does not justify a supplement.",
    },
    "rs1801131": {
        "gene": "MTHFR", "name": "Folate metabolism (A1298C)", "category": "Pharmacogenomics",
        "chromosome": "1",
        "genotypes": {
            "AA": "Typical.",
            "AC": "One copy of the variant; intermediate.",
            "CC": "Two copies; read together with C677T.",
        },
        "uses": "Read together with C677T above. Two typical copies here, so the C677T call carries the whole context.",
    },
    "rs7903146": {
        "gene": "TCF7L2", "name": "Glucose handling", "category": "Cardio-metabolic",
        "chromosome": "10",
        "genotypes": {
            "CC": "Lower studied type-2 diabetes risk.",
            "CT": "One copy of the risk allele; modestly higher studied risk.",
            "TT": "Two copies; higher studied risk.",
        },
        "uses": "Points at the fasting glucose and HbA1c series in the lab panel, which are tracked across all seven draws.",
    },
    "rs9939609": {
        "gene": "FTO", "name": "Appetite and adiposity", "category": "Cardio-metabolic",
        "chromosome": "16",
        "genotypes": {
            "TT": "Lower studied adiposity predisposition.",
            "AT": "One copy of the risk allele; intermediate.",
            "AA": "Two copies; higher studied appetite drive.",
        },
        "uses": "Weight is not tracked in this demo record, so there is nothing to test against yet. Noted, not acted on.",
    },
    "rs4988235": {
        "gene": "LCT", "name": "Lactase persistence", "category": "Traits",
        "chromosome": "2",
        "genotypes": {
            "TT": "Lactase-persistent; dairy is usually tolerated in adulthood.",
            "CT": "Lactase-persistent (dominant); dairy is usually tolerated.",
            "CC": "Often associated with reduced lactase in adulthood.",
        },
        "uses": "No dairy column in the habit log. A trait, not a question; nothing to test.",
    },
    "rs671": {
        "gene": "ALDH2", "name": "Alcohol metabolism", "category": "Traits",
        "chromosome": "12",
        "genotypes": {
            "GG": "Typical aldehyde clearance.",
            "AG": "Reduced clearance; often associated with flushing after alcohol.",
            "AA": "Near-absent clearance; alcohol is often poorly tolerated.",
        },
        "uses": "Alcohol is a logged input and a known recovery confounder in every comparison on this page. Typical clearance here, so any alcohol effect is about how much she drank, not how she clears it.",
    },
    "rs1815739": {
        "gene": "ACTN3", "name": "Muscle fiber type (R577X)", "category": "Fitness",
        "chromosome": "11",
        "genotypes": {
            "CC": "Two functional copies; often studied as a power or sprint bias.",
            "CT": "Mixed; no strong bias either way.",
            "TT": "Alpha-actinin-3 deficient; often studied as an endurance lean.",
        },
        "uses": "Training load is logged daily (0, 1, 2). The mixed call means the zone-2 cycling intervention was chosen on the data, not the genotype.",
    },
}

APOE_DIPLOTYPE = {
    ("CC", "CC"): "e4/e4", ("CT", "CC"): "e3/e4", ("TT", "CC"): "e3/e3",
    ("TT", "CT"): "e2/e3", ("TT", "TT"): "e2/e2", ("CT", "CT"): "e2/e4",
}
APOE_CONTEXT = {
    "e3/e3": "The most common combination; studied as the reference pattern for lipid handling and late-life neurological risk.",
    "e3/e4": "One e4 copy; studied as higher late-life neurological risk and less efficient LDL handling.",
    "e4/e4": "Two e4 copies; studied as substantially higher risk on both counts.",
    "e2/e3": "One e2 copy; studied as lower neurological risk, sometimes with higher triglycerides.",
    "e2/e2": "Two e2 copies; studied as lower neurological risk, with a rare lipid disorder association.",
    "e2/e4": "One protective and one risk allele.",
}
APOE_USES = "Points at the LDL and ApoB series in the lab panel. Anything clinically material here belongs with a dedicated test and a clinician, not a consumer file."

_COMPLEMENT = str.maketrans("ACGT", "TGCA")
STRAND_CHECK = {"rs1801133", "rs1801131"}


def _resolve_strand(rsid: str, genotype: str, valid: dict[str, str]) -> str:
    if genotype in valid or rsid not in STRAND_CHECK:
        return genotype
    flipped = "".join(sorted(genotype.translate(_COMPLEMENT)))
    return flipped if flipped in valid else genotype


def interpret_panel(genotypes: dict[str, str]) -> list[dict[str, Any]]:
    """Return one cautious finding per genotyped panel marker, APOE first."""
    findings: list[dict[str, Any]] = []
    a, b = genotypes.get("rs429358"), genotypes.get("rs7412")
    if a and b:
        diplotype = APOE_DIPLOTYPE.get((a, b))
        findings.append({
            "gene": "APOE", "name": "Lipid handling and late-life neurological risk",
            "category": "Longevity", "marker": "rs429358 + rs7412", "chromosome": "19",
            "genotype": f"{a}/{b}", "call": diplotype or "ambiguous",
            "context": APOE_CONTEXT.get(diplotype, "Unusual combination; confirm with a dedicated test.") if diplotype else "Unusual combination; confirm with a dedicated test.",
            "uses": APOE_USES,
        })
    for rsid, spec in PANEL.items():
        raw = genotypes.get(rsid)
        if not raw:
            continue
        genotype = _resolve_strand(rsid, raw, spec["genotypes"])
        context = spec["genotypes"].get(genotype)
        if context is None:
            continue
        findings.append({
            "gene": spec["gene"], "name": spec["name"], "category": spec["category"],
            "marker": rsid, "chromosome": spec["chromosome"], "genotype": genotype, "call": genotype,
            "context": context, "uses": spec["uses"],
        })
    for finding in findings:
        finding["boundary"] = "Context only. A single marker is probabilistic and population-dependent; it can raise a question, never settle one."
    return findings
