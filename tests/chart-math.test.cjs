const { test } = require('node:test');
const assert = require('node:assert/strict');
const chart = require('../demo/chart-math.js');

test('seven-day mean excludes an old observation across a recording gap', () => {
  const rows = [{ date: '2026-01-01', hrv_ms: 10 }, { date: '2026-01-09', hrv_ms: 90 }];
  assert.equal(chart.rollingMean(rows, 1, 'hrv_ms'), 90);
});

test('seven-day mean includes six days ago, excludes seven days ago and preserves zero', () => {
  const rows = [
    { date: '2026-01-01', hrv_ms: 1000 },
    { date: '2026-01-02', hrv_ms: 0 },
    { date: '2026-01-05', hrv_ms: null },
    { date: '2026-01-08', hrv_ms: 20 },
  ];
  assert.equal(chart.rollingMean(rows, 3, 'hrv_ms'), 10);
});

test('missing values do not become zero-valued observations', () => {
  assert.equal(chart.rollingMean([{ date: '2026-01-08', hrv_ms: null }], 0, 'hrv_ms'), null);
});

test('color represents prior-day exposure even when same-day exposure differs', () => {
  assert.equal(chart.condition({ caffeine_cutoff_2pm: 1, prior_day_caffeine_cutoff_2pm: 0 }), 'usual');
  assert.equal(chart.condition({ caffeine_cutoff_2pm: 0, prior_day_caffeine_cutoff_2pm: 1 }), 'cutoff');
});

test('missing prior calendar day is unknown, never silently usual or cutoff', () => {
  assert.equal(chart.condition({ caffeine_cutoff_2pm: 1, prior_day_caffeine_cutoff_2pm: null }), 'unknown');
  assert.equal(chart.condition({ caffeine_cutoff_2pm: 0 }), 'unknown');
});

test('time axis leaves proportional space for unrecorded days', () => {
  const rows = [{ date: '2026-01-01' }, { date: '2026-01-03' }, { date: '2026-01-09' }];
  assert.equal(chart.calendarFraction(rows, 1), 0.25);
  assert.equal(chart.calendarFraction(rows, 2), 1);
  assert.equal(chart.calendarFraction(rows.slice(0, 1), 0), 0);
});
