# Devpost Submission

## Project Details

**Title:** LiveForever

**Tagline:** A privacy-first personal evidence lab that turns health history into testable wellness experiments.

**Category:** Apps for Your Life

## Inspiration

Most health products either chart what happened or offer confident AI advice. LiveForever is for serious self-trackers who need evidence they can inspect, uncertainty they can see, and a safer next experiment. The product addresses a practical gap between fragmented personal health history and medical-sounding AI conclusions: helping someone ask one bounded question, understand the strength of the available signal, and test it more carefully.

## What It Does

LiveForever unifies longitudinal wearable signals, daily habits, laboratory trends, and cautious genomic context to answer one personal question at a time: what appears to affect my recovery, how uncertain is that signal, and how can I test it more carefully?

The demonstration follows Maya Chen, a fictional user investigating whether stopping caffeine by 2 PM is associated with better next-day recovery. Deterministic Python pairs exposure days with following-night outcomes, calculates effect sizes and 95% intervals, checks missingness and group balance, preserves confounder warnings, produces a transparent evidence grade, and generates a balanced 14-day replication plan. A synthetic CYP1A2 marker provides hypothesis context without determining the answer. Through the included Codex Skill, GPT-5.6 explains the bounded evidence, surfaces blind spots, reviews scientific context, and adapts the generated experiment to practical constraints without changing its calculations.

The product is for wellness experiment planning, not diagnosis or treatment. Every public record is synthetic, and real health or genomic inputs remain local.

## How We Built It

Before Build Week, a private personal-health prototype already existed. During the submission period, Codex and GPT-5.6 were used to create a separate public extension: a new evidence engine, Codex Agent Skill, synthetic dataset, test suite, experiment planner, and product interface. The earlier private prototype and its personal data are not part of this submission or presented as Codex work.

Codex was the primary Build Week environment. It inspected and tested the earlier private baseline without exposing its data, researched the hackathon and competitive landscape, helped choose the evidence-lab extension, designed the boundary between probabilistic model reasoning and deterministic calculations, implemented and tested the analysis engine, created the fictional fixtures, built the interactive dashboard, validated the Agent Skill, and prepared the submission materials.

GPT-5.6 is part of the actual product workflow through the LiveForever Codex Skill. It frames a tractable wellness question, chooses and verifies primary scientific sources, explains the immutable analysis output, distinguishes observation from inference, identifies alternative explanations, and adapts the generated experiment to practical constraints. It is explicitly prohibited from changing calculated values, inventing genotypes or laboratory results, hiding uncertainty, or converting association into medical advice.

## What Is Technically New

- Lagged within-person exposure/outcome pairing
- Effect sizes with deterministic seven-day moving-block bootstrap intervals
- Pearson correlations with Fisher-transformed intervals
- Minimum-sample and missing-data warnings
- Condition-balance and paired-outcome checks
- Targeted confounding checks
- Deterministic evidence score and grade
- Published PhenoAge calculation with completeness enforcement
- Genetics-to-hypothesis workflow with an explicit non-diagnostic boundary
- Balanced 14-day replication schedule and decision rule
- Responsive interface generated from an immutable `analysis.json` contract
- Eleven automated tests for the Build Week extension

## Challenges

The hardest product decision was separating what GPT-5.6 should reason about from what code should calculate. A model can synthesize a complicated personal history, but it should not silently improvise statistics, confidence, or causality. LiveForever gives GPT-5.6 the high-context work while deterministic code owns every number, warning, and grade.

The second challenge was making a meaningful health demonstration without publishing sensitive information. The repository therefore contains a complete fictional persona and deterministic synthetic generator, while private wearable, genomic, laboratory, medication, and profile records remain in a separate private system.

## Accomplishments

- Converted a broad longevity dashboard into an auditable personal evidence lab.
- Made uncertainty and null-result language first-class product features.
- Connected a genomic hypothesis to longitudinal self-tracking without using genotype as advice.
- Produced a working demo with no account, API key, or personal data.
- Preserved an exact prior-work versus Codex-work record.
- Passed the private baseline's 41 tests and the new extension's 11 tests.

## What We Learned

The most useful role for an advanced model in personal health is not to sound certain. It is to ask a better question, find the relevant evidence, explain an analysis honestly, and propose the next bounded test. Separating calculations from synthesis makes the system more useful and safer at the same time.

## What's Next

Next steps include user-selected confounders, multiple-comparison controls, interrupted time-series methods, experiment preregistration, local encrypted profiles, source adapters for major wearables and lab formats, clinician-exportable evidence summaries, and replication tracking across completed experiments.

## Testing Instructions

1. Open the live demo. Switch between HRV and Sleep, inspect the calculation dialog, and review the 14-day schedule.
2. Clone the repository.
3. Run `PYTHONPATH=src python3.11 -m liveforever_lab.cli` to regenerate all fictional data, calculations, and the experiment plan.
4. Run `PYTHONPATH=src python3.11 -m unittest discover -s tests -v`.
5. Install the repository as a Codex Skill and invoke `$liveforever-evidence-lab Investigate whether my caffeine timing is associated with next-day recovery.`

No account, API key, paid service, private health record, or real genomic file is required.

## Submission Links

- Public YouTube demo URL
- `/feedback` Session ID from the primary Codex build task
- Public repository: https://github.com/bakulbadwal/liveforever-buildweek
- Live demo: https://bakulbadwal.github.io/liveforever-buildweek/
