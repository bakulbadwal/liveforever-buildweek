# Case Study — LiveForever
### A product-thinking write-up (not a README). To run it, see [README](./README.md) or the [live demo](https://bakulbadwal.github.io/liveforever-buildweek/); this is the *why*.

A privacy-first personal evidence lab that turns a longitudinal health history into one testable wellness question, an uncertainty-aware evidence record, and a bounded next experiment.

> Honest framing up front: the public Build Week project uses one fictional persona and deliberately generated signals. It is a privacy-safe extension of a richer private prototype, not a clinical product and not a claim that synthetic results generalize to real people. The product reasoning — how to divide responsibility among code, an AI model, and the user — is the point.

---

## The problem — data abundance, interpretation scarcity

People who track their health can accumulate years of wearables, habits, bloodwork, interventions, and genomic context. The resulting experience is still fragmented: one app charts sleep, another stores labs, a spreadsheet records supplements, and a general-purpose AI can summarize everything but may sound more certain than the evidence allows.

The unmet job is not another dashboard. It is: **help me turn my own history into one answerable question, show me how uncertain the result is, and help me decide what to test next without pretending to diagnose or prove causality.**

## Who it is for

The primary user is a serious self-tracker who has enough longitudinal data to notice patterns but not a reliable way to distinguish a real personal signal from noise, missingness, imbalance, or concurrent changes.

It is deliberately *not* positioned as a clinician, medical-device workflow, or universal recommendation engine. A user should leave with a better experiment and a more honest view of their own evidence — not an AI prescription.

## The sharpest decision: do not build an “AI health coach”

The obvious product would be a chat window that absorbs health data and gives personalized advice. I rejected that framing because it gives the model responsibility for the two things it is least suited to own here: **numerical truth and medical authority.** A fluent answer can hide an improvised calculation, a missing-data problem, or a causal leap.

LiveForever instead separates the system into responsibilities:

- **Deterministic code** calculates effects, intervals, lags, sample counts, missingness, quality grades, PhenoAge, and the initial experiment schedule.
- **GPT-5.6 through the Codex Skill** frames the question, reviews scientific context, explains the fixed analysis, surfaces alternative hypotheses, and adapts the plan to practical constraints.
- **The user** chooses the question, reviews tradeoffs, and decides whether the evidence is useful enough to replicate or ignore.

The model can be articulate *about* the evidence without becoming authoritative *over* the evidence. That boundary is the applied-AI product decision at the center of the project.

## The core product insight: uncertainty is part of the interface

Most products hide uncertainty in a methodology page or a footer disclaimer. LiveForever puts it in the main workflow: confidence intervals sit beside effects, low samples generate visible warnings, missing nights stay missing, genetics is labeled hypothesis context, and the headline says “promising, not proven.”

The four-step **Evidence Chain** makes the reasoning inspectable:

`context → habit → observed signal → next test`

That sequence prevents a plausible biological story from being mistaken for proof. The CYP1A2 marker can make caffeine timing an interesting question; only the longitudinal record can show whether the pattern appears in this fictional person; neither establishes causation.

## Key product decisions & tradeoffs

| Decision | Why | Tradeoff accepted |
|---|---|---|
| **One question at a time over an everything-dashboard** | Predefining one exposure, outcome, and lag reduces correlation fishing and gives the user a decision-shaped result. | Less breadth on screen. Correct — more charts would create activity without clarity. |
| **Deterministic calculations over model-generated statistics** | Effects, intervals, warnings, and grades must be reproducible and testable. | Less conversational flexibility. Trust is more valuable than improvisation in a health context. |
| **A replication plan over a recommendation** | An observational result should produce a better next test, not a confident instruction. | The product may feel less decisive. That restraint is intentional. |
| **One coherent fictional persona over anonymized personal records** | Longitudinal health and genomic data can remain identifying even after obvious fields are removed. Synthetic data demonstrates the complete workflow without creating that exposure. | It cannot prove real-world efficacy. The public artifact proves product and engineering judgment, not clinical validity. |
| **Evidence Chain over a generic chat-first interface** | Users need to inspect how context became a claim and what happens next. | Less open-ended than chat. The constrained path is the product. |
| **Static hosted demo plus an Agent Skill over a new backend** | Judges and users can test the product with no account, key, database, or privacy risk; GPT-5.6 operates through the included Skill. | No multi-user persistence or live model call in the browser. Those are future needs, not current ones. |

## How I would measure success

**North-star:** the share of started questions that reach a documented, evidence-aware decision — *replicate, stop, or remain inconclusive* — rather than merely generating another chart.

**Supporting product metrics:** time from question to interpretable evidence record; experiment-plan acceptance and completion; percentage of records with sufficient samples and outcome coverage; repeat use for a second pre-specified question; and user comprehension of what the result does *not* establish.

**AI quality and safety metrics:** numerical fidelity to the immutable analysis contract; source-verification accuracy; rate of unsupported causal or medical claims; and whether model-proposed adaptations preserve controls, stop conditions, and medication/supplement boundaries. The target for altered numbers or invented clinical claims is zero.

## Roadmap

1. **Local connectors, not cloud ingestion by default** — normalize Oura, Apple Health, laboratory, and habit exports on-device while preserving the same analysis contract.
2. **Experiment registry and adherence** — pre-register the exposure, outcome, lag, controls, and decision rule; then distinguish planned analysis from exploratory follow-up.
3. **Longitudinal decision journal** — retain what was tested, what remained inconclusive, and which behaviors were adopted, rejected, or scheduled for replication.
4. **Model eval harness** — test GPT-5.6 explanations against fixed evidence records for numerical fidelity, causal language, source quality, and safety-boundary adherence.
5. **Clinician-shareable export** — a concise evidence record a user can bring to an appropriate professional, without presenting the product itself as medical advice.

## Honest limitations

The public result is synthetic; the observed analysis remains non-causal; one marker cannot establish a metabolism phenotype; PhenoAge is an educational summary rather than a diagnosis; and the current product has no longitudinal user study demonstrating that people complete better experiments or make better decisions.

The hosted demo also does not solve production health-data governance, account security, consent, deletion, or clinical escalation. Avoiding a backend is correct for this public prototype, but a real multi-user product would need those systems before accepting anyone’s data.

## Why this write-up exists

LiveForever is the clearest example in my portfolio of an applied-AI product decision: deciding what the model should do, what deterministic software must do, and where the human must remain in control. The interesting work is not adding AI to a health dashboard. It is designing a system where AI contributes high-context reasoning without hiding uncertainty or acquiring authority it should not have.

If you are reading this as an AI product-management hiring signal, that is the intent: problem selection, privacy judgment, model-boundary design, measurable quality, honest limitations, and a working product rather than a concept deck.

---

*Tech: Python 3.11 evidence engine, deterministic moving-block bootstrap and Fisher intervals, Codex Agent Skill with GPT-5.6, vanilla HTML/CSS/JS, synthetic fixtures, GitHub Pages. Built for OpenAI Build Week 2026 and part of a broader portfolio at [github.com/bakulbadwal](https://github.com/bakulbadwal).*
