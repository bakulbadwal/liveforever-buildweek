# Evidence integrity revision — September 5, 2026

This is a **post-submission improvement** on the current portfolio version. The judged Build Week commit `6978bcdddb418af799d6023c1d4b1b36c2fcf4a7` remains in history; no submitted artifact is rewritten.

## Changes and rationale

- **Validate daily evidence before calculating.** CSV loading accepts a UTF-8 BOM and preserves blank observations. It rejects duplicate/empty headers, uneven rows, non-finite numbers, duplicate dates, and non-canonical calendar dates with clear errors. Direct Python callers receive the same validation.
- **Order-independent results.** Analysis sorts a copied input by date before selecting the evidence window and timeline. Shuffling the same records now produces an identical result without mutating the caller's data. Previously the displayed date range and timeline depended on input order.
- **No artificial precision for singleton groups.** A one-observation condition may show a descriptive mean difference, but its uncertainty interval is unavailable. Previously the fallback could output an exact zero-width interval from two individual observations.
- **Date-correct chart.** The analysis supplies `prior_day_caffeine_cutoff_2pm` by exact calendar-day lookup, including evidence outside the truncated chart window. Chart colors and tooltips use that value. Missing prior days appear as unknown rather than usual timing.
- **A real seven-calendar-day mean and time axis.** A pure browser/Node module computes the rolling mean by dates and spaces chart points by elapsed time. Missing days no longer masquerade as equally spaced observations or stretch the averaging window.
- **Strict JSON output.** The CLI refuses to serialize NaN or Infinity.
- **Accurate method labels.** Independent review caught a surviving “seven-day” bootstrap description. The displayed provenance now says seven consecutive available pairs and discloses the short-series and singleton exceptions; the estimator is unchanged.

## Files

- `src/liveforever_lab/analysis.py`: validation, deterministic ordering, singleton handling, lagged timeline metadata.
- `src/liveforever_lab/cli.py`: strict JSON serialization.
- `demo/chart-math.js`: dependency-free calendar-aware chart functions.
- `demo/portfolio.js`, `demo/index.html`: actual UI uses those functions and identifies unknown timing.
- `demo/analysis.json`: regenerated synthetic contract with prior-day timing metadata.
- `tests/test_data_integrity.py`, `tests/chart-math.test.cjs`: regression tests for real input and chart failure cases.
- `README.md`: post-submission behavior and verification commands.

## Verification

- Baseline: 11 Python tests passed.
- New input-integrity tests reproduced failures in the original implementation.
- Final Python suite: 22 tests passed.
- Browser chart math: 6 Node tests passed; the module is the one used by the live page.
- Compared generated demo against baseline: primary and secondary effects, quality, dose response, trends, and experiment plan are unchanged. The primary estimate remains +3.94 ms across 73 paired nights.
- Browser check: HRV/Sleep toggle, navigation, unknown timing display, and absence of console errors; full notes in the portfolio report.

## Remaining limits

The bootstrap still resamples consecutive observed pairs rather than a complete calendar grid; a missing-date gap can be spanned by a block. This revision does not claim to change that estimator or establish causality. The static demo still presents the single fictional persona and is not a general-purpose health-data upload service. Empty datasets now raise a clear error from the analysis API.
