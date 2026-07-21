# Build Week Provenance

## Private Baseline

Before this public submission, a private LiveForever repository was built with Claude/Fable. Its baseline included a local metrics store, wearable and Apple Health ingestion, daily habit and intervention logs, longitudinal laboratory tracking, PhenoAge, a curated genomic parser, trend reporting, a private dashboard, and synthetic-data tests.

That prior work is not presented as Codex work. The private repository remains private because it contains personal health, medication, laboratory, and wearable records. None of that data, its reports, its profile, or its credentials was copied into this submission.

## Codex And GPT-5.6 Extension

The Build Week extension was created in a separate repository with Codex and GPT-5.6. New core functionality includes:

- A public, standalone, privacy-safe personal evidence lab.
- A deterministic lagged N-of-1 comparison engine.
- Effect sizes with 95% uncertainty intervals.
- Fisher-transformed intervals for Pearson correlations.
- Minimum-sample, missingness, balance, paired-outcome, and confounding checks.
- A transparent evidence-quality score and grade.
- Explicit association-versus-causation claim boundaries.
- A synthetic wearable, habit, laboratory, and genomic dataset.
- A cautious genetics-to-hypothesis workflow rather than genotype-as-advice.
- A balanced 14-day replication planner with controls, stop conditions, and a decision rule.
- A Codex Agent Skill that makes GPT-5.6 the source-review, explanation, and planning layer.
- An interactive responsive evidence dashboard generated from the deterministic output contract.
- Eleven new automated tests covering the Build Week functionality.

## Collaboration With Codex

Codex inspected the private baseline without modifying it, verified that its 41 tests passed, reviewed Build Week requirements and competing product overlap, helped select the extension, designed the model-versus-code responsibility boundary, implemented the evidence engine, generated and tested the fictional fixtures, built the interactive demo, researched primary scientific context, validated the Skill, and prepared the submission package.

The human product decisions were to:

- Submit LiveForever as the only project.
- Preserve the richer original product direction despite overlap with other health applications.
- Make uncertainty and experiment design the Build Week differentiator.
- Keep all personal health and genomic information out of the public build.
- Use genetics to prioritize questions, never to dictate medical or wellness advice.

