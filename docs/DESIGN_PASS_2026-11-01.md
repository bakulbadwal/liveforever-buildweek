# Portfolio redesign and full-record extension — November 1, 2026

A **post-submission** pass on the public demo. The judged Build Week commit
`6978bcdddb418af799d6023c1d4b1b36c2fcf4a7` and the submitted interface
`demo/index-buildweek.html` are unchanged; the featured analysis is unchanged.

## What changed

### Synthetic data layer (Python computes every number)

- `synthetic.generate_history()` produces one year of fictional nights and
  coaching-log habits (2025-07-21 to 2026-07-20). Its final 84 days reproduce
  `generate_records()` verbatim, so the judged window `examples/maya_daily.csv`
  is byte-identical and the featured result stays `+3.94 ms`, 95% interval
  `+1.13 to +6.42`, 73 paired nights (36 / 37). Four new 0/1 habit columns
  (breathwork, cold exposure, morning light, evening walk) come from a separate
  random stream. `tests/test_record.py::FrozenWindowTests` proves all of it.
- Seven fictional blood draws (2019 to 2026) with the nine PhenoAge inputs
  plus lipids, ApoB, HbA1c, vitamin D and ferritin; `labs.lab_record()` computes
  PhenoAge per draw with the persona's age on the draw date and flags markers
  outside general adult reference ranges. The last draw equals the original
  `SYNTHETIC_LABS`, so the longevity snapshot in `analysis.json` is unchanged.
- `habits.habit_effects()` reuses `analysis.binary_effect` (next-day mean on
  done minus not-done days, moving-block bootstrap interval) and
  `pearson_with_interval`; `input_correlations()` ranks logged inputs by |r|
  and keeps nulls visible; `habit_calendar()` feeds the weekly heatmap;
  `intervention_effects()` compares 28 days after a dated change with the 28
  before using an independent-groups interval and is labelled as the weakest
  evidence on the page. Planted effects are modest; breathwork and the evening
  walk are planted nulls, and the magnesium intervention is a planted null that
  the window comparison "detects", which the page says out loud.
- `benchmarks.py` holds age/sex cohort reference constants with notes.
- `genomics.interpret_panel()` reads a ten-marker curated panel (CYP1A2, COMT,
  MTHFR x2, TCF7L2, FTO, LCT, ALDH2, ACTN3, APOE from rs429358 + rs7412) and
  emits context plus "how LiveForever uses it", never a verdict. The fixture
  `examples/maya_genome.txt` now carries all eleven rsIDs with invented genotypes.
- `record.py` assembles `demo/record.json`; the CLI writes it alongside
  `analysis.json`, `examples/maya_history.csv`, `examples/maya_labs_history.json`
  and `examples/maya_supplements.csv`.

Regenerate everything:

```bash
PYTHONPATH=src python3 -m liveforever_lab.cli
```

### Interface

`demo/index.html`, `demo/portfolio.css`, `demo/portfolio.js` were rewritten as
one scrolling narrative; `demo/genome.js` is new.

Sections, in order: masthead and definition with byline; biological-age dial
with the seven-year trend; a scope line of what is connected; "One record,
five layers" (time coverage of bloodwork, supplements, nights, habits, genome);
biological age across seven draws with a selectable draw and every marker
against its range; habits (weekly heatmap, done-vs-not effects with intervals
and an outcome toggle, three interventions with the generator's truth printed
beside each result, supplement spans, cohort comparison); the featured
caffeine experiment (question, headline number, three-outcome effect plot,
nightly timeline with HRV/Sleep toggle and keyboard-reachable nights, the
fourteen-day pre-registered retest with decision rule); the genome as an
interactive three.js double helix (r128, pinned on cdnjs, lazy-loaded) whose
lit base pairs are the panel markers, with a 2D fallback for reduced motion or
no WebGL and a keyboard-reachable list; how it works (code computes / the
model explains, quality grade, method and provenance, privacy); colophon.

Visual system: deep night-blue ground, warm ivory ink, hairline rules,
Spectral for headlines and lead numbers, Albert Sans with tabular figures for
data. One accent (amber) means one thing everywhere: the condition under test
(caffeine stopped, habit done, after a change). Slate is always the comparison.
No red or green. Filled markers mean the 95% interval excludes zero; hollow
markers mean nothing was detected.

Also new: Open Graph and Twitter meta, `demo/og.png` (1200 x 630, rendered from
`demo/share.html` with headless Chrome), `demo/favicon.svg`,
`demo/apple-touch-icon.png`. Legacy hashes `#experiment` and `#data` still land
on the matching sections; `#overview` lands at the top.

Removed from the previous portfolio version: the dark sidebar, the persona
avatar header, pill badges, KPI tiles with traffic-light colours, tracked
uppercase micro-labels, the 01/02/03/04 step cards and the system font stack.

## Verification

- `uv run --with pytest pytest -q`: 36 passed (22 existing + 14 new).
- `node --test tests/chart-math.test.cjs`: 6 passed.
- `git diff` on `demo/analysis.json`, `examples/maya_daily.csv` and
  `examples/maya_labs.json` after regeneration: empty.
- Browser pane at 375 x 812: `document.documentElement.scrollWidth <= innerWidth`
  true; no element extends past the viewport.
- Impeccable mechanical detector over the four demo files: no findings.
- The three.js scene was verified in the desktop app's browser pane (WebGL);
  headless Chrome with `--disable-gpu` renders the 2D fallback, which is the
  intended behaviour without WebGL.

## Known limits

- The dataviz palette validator flags the amber accent as lighter than its
  categorical band and the slate comparison as near-grey. Both are deliberate:
  slate is the neutral baseline, amber is the single lit condition, and the
  CVD separation (ΔE 19) and contrast checks pass; identity is also carried by
  filled-versus-hollow markers and labels.
- Habit effects are estimated over the full year while the featured caffeine
  result is estimated on the fixed 84-day window; caffeine is therefore
  excluded from the habit panel so one question never shows two numbers.
- Intervention windows are time-confounded by construction and are labelled
  as such.
