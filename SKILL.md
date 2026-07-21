---
name: liveforever-evidence-lab
description: Analyze longitudinal wellness data as a privacy-first personal evidence record, quantify uncertainty and data quality, and design a bounded N-of-1 replication plan. Use when the user asks LiveForever to investigate a habit, wearable trend, wellness intervention, lab trend, or genomic hypothesis without making medical claims.
---

# LiveForever Evidence Lab

Turn a personal wellness question into an auditable evidence record and a small replication plan. GPT-5.6 handles question framing, evidence review, explanation, and experiment design. Deterministic Python owns every displayed calculation, interval, quality grade, and derived annotation.

## Workflow

1. Confirm that the request concerns wellness experiment planning rather than diagnosis, treatment, emergencies, medication changes, or interpretation that requires a clinician.
2. Use local files only. Never upload or quote raw genomic data, health exports, lab PDFs, names, dates of birth, credentials, or proprietary records.
3. Identify one exposure, one primary outcome, a lag, and a minimum useful sample. Avoid scanning every possible correlation and presenting the best one without correction.
4. Normalize a daily CSV to the synthetic schema in `examples/maya_daily.csv`.
5. Run the deterministic analysis. For the public demonstration:

```bash
PYTHONPATH=src python3.11 -m liveforever_lab.cli
```

6. Read `demo/analysis.json`. Do not recalculate, round differently, or silently replace any value.
7. Verify scientific context against primary literature. State when a marker, benchmark, or paper is population-dependent, observational, or contested.
8. Explain the result using the format below. Always distinguish observation, inference, and next test.
9. Offer the generated replication plan as a draft for review. Do not recommend changing medication, adding supplements, escalating doses, or delaying professional care.

## Evidence Record Format

Use these headings:

- `Question`
- `Observed signal`
- `Uncertainty`
- `Data quality`
- `Genomic or laboratory context`
- `What this does not establish`
- `Replication plan`
- `Source ledger`

For each numeric claim, preserve the effect, interval, sample counts, lag, and quality warning from `analysis.json`.

## Model Responsibilities

GPT-5.6 may:

- Turn a broad goal into one answerable question.
- Choose which verified sources are relevant to scientific context.
- Explain an effect and confidence interval in plain English.
- Surface confounders, alternative explanations, and missing measurements.
- Adapt the generated plan to practical constraints after the user confirms them.

GPT-5.6 must not:

- Invent a calculation, genotype, laboratory value, source, diagnosis, or causal claim.
- Treat a confidence interval as certainty or a nonsignificant result as proof of no effect.
- Use a single genetic marker to prescribe behavior or treatment.
- Hide low sample size, missingness, imbalance, concurrent changes, or selection bias.
- expose private inputs in output, logs, commits, screenshots, or public demos.

## Claim Language

Prefer:

- `observed association`
- `the interval includes no difference`
- `promising, not proven`
- `hypothesis context only`
- `replicate before acting`

Avoid:

- `caused`
- `proved`
- `your genes mean you should`
- `this treats or prevents`
- `clinically normal` unless quoting an authorized clinical source with proper context

