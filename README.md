# LiveForever

LiveForever is a privacy-first personal evidence lab. It combines longitudinal wearable data, habit logs, laboratory trends, and cautious genomic context to answer one practical question at a time: **what appears to affect my recovery, how certain is that signal, and how can I test it more carefully?**

**[Open the fictional interactive demo](https://bakulbadwal.github.io/liveforever-buildweek/)**

The public Build Week project contains no personal health information. Every visible record, lab value, genomic marker, and outcome belongs to the fictional demo persona Maya Chen.

## What Makes It Different

- **One owned evidence layer:** wearables, daily inputs, labs, and genomic context meet in one longitudinal record.
- **Calculations outside the model:** Python owns effect sizes, 95% intervals, lags, sample counts, missingness, condition balance, correlations, PhenoAge, and quality grades.
- **GPT-5.6 inside a contract:** the model frames questions, reviews primary sources, explains results, identifies blind spots, and adapts experiment plans without altering calculated values.
- **Genetics as a hypothesis, not a verdict:** a synthetic CYP1A2 marker informs which caffeine question may be worth testing but never determines a recommendation.
- **Null-result honesty:** insufficient samples and intervals that include zero are shown as inconclusive.
- **Local-first privacy:** raw health and genomic data stay outside the public repository and outside model output.

## Demonstration

The fictional demo asks whether stopping caffeine by 2 PM is associated with better next-day recovery. It analyzes 84 calendar days and reports:

- `+3.94 ms` next-day HRV, 95% interval `+1.13 to +6.42`
- `+0.30 h` sleep duration, 95% interval `+0.05 to +0.56`
- `-1.38 bpm` resting heart rate, 95% interval `-2.26 to -0.45`
- `73` paired nights with balanced conditions
- `95%` calendar coverage and a `B` evidence-quality grade
- A deterministic, balanced 14-day replication schedule

These are deliberately generated signals in synthetic data, not human findings.

## Architecture

```text
wearables + habits + labs + local genomic marker
                       |
                       v
         deterministic Python analysis
  effects | intervals | quality | PhenoAge | provenance
                       |
                       v
               analysis.json contract
                       |
                       v
             Codex + GPT-5.6 skill
 framing | source review | explanation | experiment planning
                       |
                       v
          auditable personal evidence record
```

## Run It

Requires Python 3.11 or newer and no runtime dependencies.

```bash
PYTHONPATH=src python3.11 -m liveforever_lab.cli
python3.11 -m http.server 8765 --directory demo
```

Open `http://localhost:8765`.

Run the tests:

```bash
PYTHONPATH=src python3.11 -m unittest discover -s tests -v
```

Install as a Codex Skill by placing this repository in the Codex skills directory, then invoke:

```text
$liveforever-evidence-lab Investigate whether my caffeine timing is associated with next-day recovery.
```

## What Code Calculates

`src/liveforever_lab/analysis.py` calculates lagged group comparisons, deterministic seven-day moving-block bootstrap intervals, Pearson correlations with Fisher intervals, recent-versus-baseline trends, sample counts, calendar coverage, group balance, paired-outcome coverage, confounding warnings, and the evidence-quality grade.

`src/liveforever_lab/phenoage.py` implements the published PhenoAge equation when all required inputs exist. `src/liveforever_lab/genomics.py` parses the explicitly synthetic marker fixture and emits a bounded hypothesis annotation. `src/liveforever_lab/planner.py` creates the balanced 14-day schedule, controls, stop conditions, and decision rule.

The complete method and claim boundaries are documented in [docs/TECHNICAL_METHOD.md](docs/TECHNICAL_METHOD.md).

## Scientific Context

- PhenoAge combines chronological age with nine routine clinical biomarkers; the implementation follows the published coefficients and remains an educational summary, not a clinical age or mortality prediction: [Levine et al. method discussed in PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13015750/).
- CYP1A2 `rs762551` has been studied in caffeine metabolism, but functional effects vary with context and population. LiveForever therefore uses it only to generate a hypothesis worth testing: [systematic review](https://pubmed.ncbi.nlm.nih.gov/29282363/), [population-dependence meta-analysis](https://pubmed.ncbi.nlm.nih.gov/27173183/).

## Privacy And Safety

- Real databases, profiles, exports, lab PDFs, genomic files, API tokens, reports, and intervention histories are excluded by design.
- The checked-in genome and laboratory fixtures are visibly marked synthetic.
- The product supports wellness experiment planning, not diagnosis or treatment.
- Medication and supplement changes are outside the generated plan.
- Severe or concerning symptoms are a stop condition and require appropriate professional care.

## Build Week

The original private LiveForever baseline and the new Codex/GPT-5.6 extension are separated in [docs/BUILD_WEEK_PROVENANCE.md](docs/BUILD_WEEK_PROVENANCE.md). Submission copy, recording script, and deadline checklist are in [docs/DEVPOST_SUBMISSION.md](docs/DEVPOST_SUBMISSION.md), [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md), and [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md).

## License

MIT
