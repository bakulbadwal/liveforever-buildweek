/* LiveForever · night atlas
   Every number on the page is read from analysis.json (the featured
   experiment's contract) and record.json (the full synthetic record).
   This file only draws. */
(function () {
  'use strict';

  var state = { analysis: null, plan: null, record: null, draw: null, habitOutcome: 'hrv_ms', nightMetric: 'hrv_ms', width: 0 };

  var OUTCOME = {
    hrv_ms: { label: 'HRV', long: 'Next-day HRV', unit: 'ms', digits: 1, pad: 3, better: 'higher' },
    sleep_hours: { label: 'Sleep', long: 'Sleep duration', unit: 'h', digits: 2, pad: 0.25, better: 'longer' },
    resting_hr: { label: 'Resting HR', long: 'Resting heart rate', unit: 'bpm', digits: 1, pad: 1, better: 'lower' }
  };

  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function fmt(v, d) { return Number(v).toFixed(d == null ? 2 : d); }
  function signed(v, d) { var s = fmt(v, d); return (v > 0 ? '+' : v < 0 ? '−' : '') + s.replace('-', ''); }
  function parse(d) { return new Date(d + 'T12:00:00'); }
  function monthYear(d) { var t = parse(d); return MONTHS[t.getMonth()] + ' ' + t.getFullYear(); }
  function shortDate(d) { var t = parse(d); return MONTHS[t.getMonth()] + ' ' + t.getDate(); }
  function longDate(d) { var t = parse(d); return MONTHS[t.getMonth()] + ' ' + t.getDate() + ', ' + t.getFullYear(); }
  function weekday(d) { return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][parse(d).getDay()]; }
  function dayNum(d) { return Date.parse(d + 'T00:00:00Z') / 86400000; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function width(el) { return Math.max(240, el.clientWidth || el.parentNode.clientWidth || 320); }
  function narrow() { return state.width < 600; }

  /* ---------- shared pieces ---------- */

  function svgOpen(w, h, extra) {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" ' + (extra || '') + '>';
  }

  /* A point estimate with its 95% interval on a shared horizontal scale.
     The interval sits on the upper line; its label is set beneath it, left-aligned
     to the lower bound and clamped inside the plot so it never collides. */
  function intervalRow(w, h, scale, row, opts) {
    opts = opts || {};
    var cy = 16;
    var x0 = scale(0);
    var out = [];
    out.push('<line x1="' + x0 + '" y1="2" x2="' + x0 + '" y2="' + (h - 2) + '" class="axis-line"/>');
    if (row.effect == null) {
      out.push('<text x="' + Math.min(x0 + 8, w - 150) + '" y="' + (cy + 4) + '" class="axis-label">' + esc(row.note || 'not enough paired days') + '</text>');
      return out.join('');
    }
    var x = scale(row.effect);
    var detected = row.ci_low != null && !(row.ci_low <= 0 && 0 <= row.ci_high);
    var stroke = 'var(--slate)';
    if (row.ci_low != null) {
      out.push('<line x1="' + scale(row.ci_low) + '" y1="' + cy + '" x2="' + scale(row.ci_high) + '" y2="' + cy + '" stroke="' + stroke + '" stroke-width="2" stroke-linecap="round"/>');
      out.push('<line x1="' + scale(row.ci_low) + '" y1="' + (cy - 5) + '" x2="' + scale(row.ci_low) + '" y2="' + (cy + 5) + '" stroke="' + stroke + '" stroke-width="1.5"/>');
      out.push('<line x1="' + scale(row.ci_high) + '" y1="' + (cy - 5) + '" x2="' + scale(row.ci_high) + '" y2="' + (cy + 5) + '" stroke="' + stroke + '" stroke-width="1.5"/>');
    }
    if (detected) {
      out.push('<circle cx="' + x + '" cy="' + cy + '" r="5.5" fill="var(--self)" stroke="var(--ground)" stroke-width="2"/>');
    } else {
      out.push('<circle cx="' + x + '" cy="' + cy + '" r="5" fill="var(--ground)" stroke="var(--slate)" stroke-width="2"/>');
    }
    var label = signed(row.effect, opts.digits) + ' ' + opts.unit;
    if (row.ci_low != null) label += ' (' + signed(row.ci_low, opts.digits) + ' to ' + signed(row.ci_high, opts.digits) + ')';
    var reading = row.ci_low == null ? '' : detected ? (opts.detectedWord || 'association') : 'nothing detected';
    var est = label.length * 6.9 + (reading ? reading.length * 6.2 + 10 : 0);
    if (reading && est > w) {
      // no room beside the interval on a narrow plot: hand the reading back to the caller's row label
      if (opts.readingOut) opts.readingOut.text = reading;
      reading = '';
      est = label.length * 6.9;
    }
    var lo = row.ci_low == null ? x : scale(row.ci_low);
    var textX = clamp(lo, 0, Math.max(0, w - est));
    out.push('<text x="' + textX.toFixed(1) + '" y="' + (h - 6) + '" class="value-label">' + esc(label) +
      (reading ? '<tspan class="axis-label" font-style="italic" font-family="Spectral, serif" font-size="12.5" dx="8">' + esc(reading) + '</tspan>' : '') + '</text>');
    return out.join('');
  }

  function linearScale(d0, d1, r0, r1) {
    return function (v) { return r0 + (v - d0) / (d1 - d0) * (r1 - r0); };
  }

  function niceTicks(lo, hi, count) {
    var span = hi - lo;
    var step = Math.pow(10, Math.floor(Math.log10(span / count)));
    var err = span / count / step;
    if (err >= 7.5) step *= 10; else if (err >= 3.5) step *= 5; else if (err >= 1.5) step *= 2;
    var ticks = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) ticks.push(Number(v.toFixed(6)));
    return ticks;
  }

  function axisRow(w, scale, lo, hi, unit, leftPad) {
    var out = [svgOpen(w, 22)];
    niceTicks(lo, hi, narrow() ? 4 : 7).forEach(function (t) {
      var x = scale(t);
      if (x < 0 || x > w) return;
      out.push('<line x1="' + x + '" y1="0" x2="' + x + '" y2="5" class="axis-line"/>');
      out.push('<text x="' + x + '" y="18" text-anchor="middle" class="axis-label">' + (t > 0 ? '+' : '') + t + (t === 0 ? '' : '') + '</text>');
    });
    out.push('<text x="' + w + '" y="18" text-anchor="end" class="axis-label">' + esc(unit) + '</text>');
    out.push('</svg>');
    return out.join('');
  }

  function sharedDomain(rows, pad) {
    var lo = 0, hi = 0;
    rows.forEach(function (r) {
      if (r.effect == null) return;
      lo = Math.min(lo, r.ci_low == null ? r.effect : r.ci_low);
      hi = Math.max(hi, r.ci_high == null ? r.effect : r.ci_high);
    });
    var span = Math.max(hi - lo, pad * 2);
    return [lo - span * 0.08, hi + span * 0.08];
  }

  /* ---------- hero ---------- */

  function renderDial(hero) {
    var size = 300, r = 118, cx = 150, cy = 150, sw = 9;
    var circ = 2 * Math.PI * r;
    var frac = clamp(hero.phenoage / hero.chronological_age_at_draw, 0, 1.2);
    var dash = Math.min(frac, 1) * circ;
    var younger = hero.gap_years < 0;
    // tick marks every year from 0 to chronological age, a quiet instrument scale
    var ticks = [];
    var years = Math.round(hero.chronological_age_at_draw);
    for (var i = 0; i <= years; i++) {
      var a = -Math.PI / 2 + (i / hero.chronological_age_at_draw) * 2 * Math.PI;
      var inner = i % 5 === 0 ? r + 14 : r + 10;
      var outer = r + 18;
      ticks.push('<line x1="' + (cx + Math.cos(a) * inner).toFixed(1) + '" y1="' + (cy + Math.sin(a) * inner).toFixed(1) + '" x2="' + (cx + Math.cos(a) * outer).toFixed(1) + '" y2="' + (cy + Math.sin(a) * outer).toFixed(1) + '" stroke="' + (i % 5 === 0 ? 'var(--ink-3)' : 'var(--rule)') + '" stroke-width="1"/>');
    }
    // marker at the pheno age position
    var pa = -Math.PI / 2 + Math.min(frac, 1) * 2 * Math.PI;
    var mx = cx + Math.cos(pa) * r, my = cy + Math.sin(pa) * r;
    // sparkline of gap over draws, inside the dial
    var trend = hero.trend;
    var tw = 120, th = 34, tx0 = cx - tw / 2, ty0 = cy + 34;
    var gaps = trend.map(function (t) { return t.gap_years; });
    var gmin = Math.min.apply(null, gaps.concat([0])), gmax = Math.max.apply(null, gaps.concat([0]));
    var sx = linearScale(dayNum(trend[0].date), dayNum(trend[trend.length - 1].date), tx0, tx0 + tw);
    var sy = linearScale(gmin, gmax, ty0 + th, ty0);
    var path = trend.map(function (t, i) { return (i ? 'L' : 'M') + sx(dayNum(t.date)).toFixed(1) + ',' + sy(t.gap_years).toFixed(1); }).join(' ');
    var svg = [svgOpen(size, size, 'role="img" aria-label="Biological age ' + fmt(hero.phenoage, 1) + ' against calendar age ' + fmt(hero.chronological_age_at_draw, 1) + '"')];
    svg.push(ticks.join(''));
    svg.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="var(--rule)" stroke-width="' + sw + '"/>');
    svg.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="var(--self)" stroke-width="' + sw + '" stroke-linecap="round" stroke-dasharray="' + dash.toFixed(1) + ' ' + circ.toFixed(1) + '" transform="rotate(-90 ' + cx + ' ' + cy + ')"/>');
    svg.push('<circle cx="' + mx.toFixed(1) + '" cy="' + my.toFixed(1) + '" r="7" fill="var(--ground)" stroke="var(--self)" stroke-width="2.5"/>');
    svg.push('<text x="' + cx + '" y="' + (cy - 36) + '" text-anchor="middle" class="axis-label" font-size="12.5">biological age</text>');
    svg.push('<text x="' + (cx + 14) + '" y="' + (cy - r - 22) + '" class="axis-label" font-size="11">' + fmt(hero.chronological_age_at_draw, 1) + ' calendar</text>');
    svg.push('<text x="' + cx + '" y="' + (cy + 14) + '" text-anchor="middle" font-family="Spectral, serif" font-weight="300" font-size="64" fill="var(--ink)" letter-spacing="-0.02em">' + fmt(hero.phenoage, 1) + '</text>');
    svg.push('<line x1="' + tx0 + '" y1="' + sy(0).toFixed(1) + '" x2="' + (tx0 + tw) + '" y2="' + sy(0).toFixed(1) + '" class="grid-line" stroke-dasharray="2 3"/>');
    svg.push('<path d="' + path + '" fill="none" stroke="var(--ink-2)" stroke-width="1.5" stroke-linejoin="round"/>');
    trend.forEach(function (t, i) {
      svg.push('<circle cx="' + sx(dayNum(t.date)).toFixed(1) + '" cy="' + sy(t.gap_years).toFixed(1) + '" r="' + (i === trend.length - 1 ? 3.5 : 2) + '" fill="' + (i === trend.length - 1 ? 'var(--ink)' : 'var(--ink-2)') + '"/>');
    });
    svg.push('<text x="' + tx0 + '" y="' + (ty0 + th + 14) + '" class="axis-label" font-size="10.5">' + trend[0].date.slice(0, 4) + '</text>');
    svg.push('<text x="' + (tx0 + tw) + '" y="' + (ty0 + th + 14) + '" text-anchor="end" class="axis-label" font-size="10.5">' + trend[trend.length - 1].date.slice(0, 4) + '</text>');
    svg.push('</svg>');
    $('dial-ring').innerHTML = svg.join('');
    $('dial-caption').innerHTML = '<strong>' + fmt(Math.abs(hero.gap_years), 1) + ' years ' + (younger ? 'younger' : 'older') + '</strong> than her calendar age of ' + fmt(hero.chronological_age_at_draw, 1) + ' at the ' + monthYear(hero.draw_date) + ' draw. In ' + hero.first_draw_date.slice(0, 4) + ' the same markers read ' + fmt(Math.abs(hero.first_gap_years), 1) + ' years ' + (hero.first_gap_years < 0 ? 'younger' : 'older') + '.';
  }

  function renderScope(s) {
    var items = [
      '<b>' + s.nights_recorded + '</b> nights of wearable data',
      '<b>' + s.habit_days + '</b> days of habits',
      '<b>' + s.lab_draws + '</b> blood draws over <b>' + s.years_of_labs + '</b> years',
      '<b>' + s.biomarkers_tracked + '</b> biomarkers',
      '<b>' + s.supplements_tracked + '</b> supplements since ' + s.supplement_first.slice(0, 4),
      '<b>' + s.genome_markers + '</b> genome markers'
    ];
    $('scope').innerHTML = items.map(function (t) { return '<span>' + t + '</span>'; }).join('');
  }

  /* ---------- atlas: one record, five layers ---------- */

  function renderAtlas(record) {
    var host = $('atlas');
    var w = width(host);
    var left = narrow() ? 104 : 150, right = 12, top = 26;
    var rowH = narrow() ? 44 : 52, gap = 6;
    var labs = record.labs.draws;
    var supps = record.supplements;
    var start = dayNum(labs[0].date) - 120;
    var end = dayNum(record.scope.last_night) + 20;
    var x = linearScale(start, end, left, w - right);
    var rows = narrow() ? [
      { label: 'Bloodwork', sub: labs.length + ' draws' },
      { label: 'Supplements', sub: supps.length + ' tracked' },
      { label: 'Nights', sub: record.scope.nights_recorded + ' nights' },
      { label: 'Habit log', sub: record.scope.habit_days + ' days' },
      { label: 'Genome', sub: record.scope.genome_markers + ' markers' }
    ] : [
      { label: 'Bloodwork', sub: labs.length + ' draws, ' + record.scope.biomarkers_tracked + ' markers' },
      { label: 'Supplements', sub: supps.length + ' tracked since ' + record.scope.supplement_first.slice(0, 4) },
      { label: 'Wearable nights', sub: record.scope.nights_recorded + ' nights' },
      { label: 'Habit log', sub: record.scope.habit_days + ' days, ' + record.habits.columns.length + ' practices' },
      { label: 'Genome', sub: record.scope.genome_markers + ' markers, one file' }
    ];
    var h = top + rows.length * (rowH + gap) + 26;
    var out = [svgOpen(w, h, 'role="img" aria-label="Time coverage of the five data layers from ' + labs[0].date.slice(0, 4) + ' to ' + record.scope.last_night.slice(0, 4) + '"')];
    // year grid
    var y0 = parse(labs[0].date).getFullYear(), y1 = parse(record.scope.last_night).getFullYear();
    var years = [];
    for (var yr = y0; yr <= y1 + 1; yr++) {
      var xx = x(dayNum(yr + '-01-01'));
      if (xx < left || xx > w - right) continue;
      out.push('<line x1="' + xx.toFixed(1) + '" y1="' + (top - 8) + '" x2="' + xx.toFixed(1) + '" y2="' + (h - 22) + '" class="grid-line"/>');
      years.push({ yr: yr, x: xx });
    }
    // label the first and last visible years always; thin the middle ones so nothing collides
    var labelW = 36, lastEnd = years.length ? years[years.length - 1].x : 0;
    var prevRight = -Infinity;
    years.forEach(function (item, i) {
      var isLast = i === years.length - 1;
      var isFirst = i === 0;
      if (!isFirst && !isLast) {
        if (narrow() && item.yr % 2) return;
        if (item.x + 4 - prevRight < 10 || lastEnd - labelW - (item.x + 4 + labelW) < 10) return;
      }
      var labelX = isLast ? item.x - 4 : item.x + 4;
      out.push('<text x="' + labelX.toFixed(1) + '" y="' + (h - 8) + '" text-anchor="' + (isLast ? 'end' : 'start') + '" class="axis-label">' + item.yr + '</text>');
      if (!isLast) prevRight = labelX + labelW;
    });
    rows.forEach(function (row, i) {
      var y = top + i * (rowH + gap), cy = y + rowH / 2;
      out.push('<line x1="' + left + '" y1="' + (y + rowH) + '" x2="' + (w - right) + '" y2="' + (y + rowH) + '" class="grid-line"/>');
      out.push('<text x="0" y="' + (cy - 2) + '" class="row-label">' + esc(row.label) + '</text>');
      out.push('<text x="0" y="' + (cy + 13) + '" class="atlas-sub">' + esc(row.sub) + '</text>');
      if (i === 0) {
        labs.forEach(function (d) {
          var dx = x(dayNum(d.date));
          out.push('<line x1="' + dx.toFixed(1) + '" y1="' + (cy - 12) + '" x2="' + dx.toFixed(1) + '" y2="' + (cy + 12) + '" stroke="var(--self)" stroke-width="2.5" stroke-linecap="round"/>');
        });
      } else if (i === 1) {
        var lane = (rowH - 10) / supps.length;
        supps.forEach(function (s, k) {
          var ly = y + 5 + k * lane + lane / 2;
          out.push('<line x1="' + x(dayNum(s.first)).toFixed(1) + '" y1="' + ly.toFixed(1) + '" x2="' + x(dayNum(s.last)).toFixed(1) + '" y2="' + ly.toFixed(1) + '" stroke="var(--self)" stroke-opacity="' + (s.current ? 0.9 : 0.45) + '" stroke-width="' + Math.max(1.5, lane - 2) + '" stroke-linecap="round"/>');
        });
      } else if (i === 2) {
        var nights = record.timeline;
        nights.forEach(function (n) {
          if (n.hrv_ms == null) return;
          var nx = x(dayNum(n.date));
          var ny = cy + 12 - (n.hrv_ms - 30) / 40 * 24;
          out.push('<circle cx="' + nx.toFixed(1) + '" cy="' + ny.toFixed(1) + '" r="1.6" fill="var(--self)" fill-opacity="0.9"/>');
        });
      } else if (i === 3) {
        var first = dayNum(record.habits.calendar.first), last = dayNum(record.habits.calendar.last);
        out.push('<rect x="' + x(first).toFixed(1) + '" y="' + (cy - 9) + '" width="' + (x(last) - x(first)).toFixed(1) + '" height="18" rx="2" fill="var(--self)" fill-opacity="0.18"/>');
        // the five practices as thin lanes with their adherence as opacity by week
        var weeks = record.habits.calendar.weeks, cols = record.habits.columns;
        var laneH = 18 / cols.length;
        weeks.forEach(function (wk) {
          cols.forEach(function (c, ci) {
            var done = 0, logged = 0;
            wk.days.forEach(function (d) { if (d.done[c] != null) { logged++; done += d.done[c]; } });
            if (!logged) return;
            var wx = x(dayNum(wk.start)), ww = Math.max(1, x(dayNum(wk.start) + 7) - wx - 0.5);
            out.push('<rect x="' + wx.toFixed(1) + '" y="' + (cy - 9 + ci * laneH).toFixed(1) + '" width="' + ww.toFixed(1) + '" height="' + (laneH - 0.6).toFixed(1) + '" fill="var(--self)" fill-opacity="' + (0.15 + 0.75 * done / logged).toFixed(2) + '"/>');
          });
        });
      } else {
        // the genome does not change: a constant engraved line with its markers evenly spaced
        out.push('<line x1="' + left + '" y1="' + cy + '" x2="' + (w - right) + '" y2="' + cy + '" stroke="var(--self)" stroke-opacity="0.5" stroke-width="1" stroke-dasharray="1 4"/>');
        var n = record.genome.findings.length;
        for (var k = 0; k < n; k++) {
          var gx = left + (k + 0.5) / n * (w - right - left);
          out.push('<circle cx="' + gx.toFixed(1) + '" cy="' + cy + '" r="3" fill="var(--self)"/>');
        }
      }
    });
    out.push('</svg>');
    host.innerHTML = out.join('') + '<p class="fig-note">Horizontal axis is calendar time. Bloodwork is per draw; supplements are logged spans; wearable nights are plotted by HRV; the habit band is shaded by weekly adherence; the genome is one file read once.</p>';
  }

  /* ---------- biological age chart ---------- */

  function renderPheno(record) {
    var host = $('phenochart');
    var labs = record.labs;
    var draws = labs.draws.filter(function (d) { return d.phenoage != null; });
    var w = width(host), h = narrow() ? 260 : 320;
    var left = 40, right = narrow() ? 16 : 24, top = 28, bottom = h - 34;
    var t0 = dayNum(draws[0].date) - 150, t1 = dayNum(draws[draws.length - 1].date) + 150;
    var x = linearScale(t0, t1, left, w - right);
    var ages = [];
    draws.forEach(function (d) { ages.push(d.age, d.phenoage); });
    var ymin = Math.floor(Math.min.apply(null, ages)) - 1, ymax = Math.ceil(Math.max.apply(null, ages)) + 1;
    var y = linearScale(ymin, ymax, bottom, top);
    var out = [svgOpen(w, h, 'role="img" aria-label="PhenoAge against calendar age across ' + draws.length + ' draws"')];
    for (var v = ymin; v <= ymax; v += 2) {
      out.push('<line x1="' + left + '" y1="' + y(v).toFixed(1) + '" x2="' + (w - right) + '" y2="' + y(v).toFixed(1) + '" class="grid-line"/>');
      out.push('<text x="' + (left - 8) + '" y="' + (y(v) + 4).toFixed(1) + '" text-anchor="end" class="axis-label">' + v + '</text>');
    }
    out.push('<text x="' + left + '" y="' + (top - 12) + '" class="axis-label">years</text>');
    // gap area between the two lines
    var area = draws.map(function (d, i) { return (i ? 'L' : 'M') + x(dayNum(d.date)).toFixed(1) + ',' + y(d.phenoage).toFixed(1); }).join(' ')
      + draws.slice().reverse().map(function (d) { return ' L' + x(dayNum(d.date)).toFixed(1) + ',' + y(d.age).toFixed(1); }).join('') + ' Z';
    out.push('<path d="' + area + '" fill="var(--self)" fill-opacity="0.07"/>');
    var ageLine = draws.map(function (d, i) { return (i ? 'L' : 'M') + x(dayNum(d.date)).toFixed(1) + ',' + y(d.age).toFixed(1); }).join(' ');
    var phenoLine = draws.map(function (d, i) { return (i ? 'L' : 'M') + x(dayNum(d.date)).toFixed(1) + ',' + y(d.phenoage).toFixed(1); }).join(' ');
    out.push('<path d="' + ageLine + '" fill="none" stroke="var(--slate)" stroke-width="1.5" stroke-dasharray="4 4"/>');
    out.push('<path d="' + phenoLine + '" fill="none" stroke="var(--self)" stroke-width="2" stroke-linejoin="round"/>');
    draws.forEach(function (d, i) {
      var dx = x(dayNum(d.date)), dy = y(d.phenoage), ay = y(d.age);
      var selected = state.draw === i;
      out.push('<g class="draw-button" role="button" tabindex="0" data-draw="' + i + '" aria-pressed="' + selected + '" aria-label="' + longDate(d.date) + ': biological age ' + fmt(d.phenoage, 1) + ', calendar age ' + fmt(d.age, 1) + '">');
      out.push('<rect class="draw-hit" x="' + (dx - 22) + '" y="' + (Math.min(dy, ay) - 22) + '" width="44" height="' + (Math.abs(dy - ay) + 44) + '" rx="6"/>');
      out.push('<circle cx="' + dx.toFixed(1) + '" cy="' + ay.toFixed(1) + '" r="3" fill="var(--slate)"/>');
      if (selected) out.push('<circle cx="' + dx.toFixed(1) + '" cy="' + dy.toFixed(1) + '" r="12" fill="none" stroke="var(--self)" stroke-width="1.5"/>');
      out.push('<circle class="draw-dot" cx="' + dx.toFixed(1) + '" cy="' + dy.toFixed(1) + '" r="' + (selected ? 6 : 5) + '" fill="var(--self)" stroke="var(--ground)" stroke-width="2"/>');
      if (!narrow() || i === 0 || i === draws.length - 1 || selected) {
        out.push('<text x="' + dx.toFixed(1) + '" y="' + (dy - 12).toFixed(1) + '" text-anchor="middle" class="value-label">' + fmt(d.phenoage, 1) + '</text>');
      }
      out.push('<text x="' + dx.toFixed(1) + '" y="' + (bottom + 20) + '" text-anchor="middle" class="axis-label">' + (narrow() ? "'" + d.date.slice(2, 4) : monthYear(d.date)) + '</text>');
      out.push('</g>');
    });
    var lastD = draws[draws.length - 1];
    out.push('<text x="' + (x(dayNum(lastD.date)) + 10).toFixed(1) + '" y="' + (y(lastD.age) + 4).toFixed(1) + '" class="axis-label" fill="var(--slate)">' + (narrow() ? 'age' : 'calendar age') + '</text>');
    out.push('</svg>');
    host.innerHTML = out.join('') +
      '<div class="legend"><span><i class="self"></i>PhenoAge</span><span><i class="slate"></i>Calendar age</span><span><i class="ringed"></i>Selected draw</span></div>';
    host.querySelectorAll('.draw-button').forEach(function (g) {
      var i = Number(g.dataset.draw);
      g.addEventListener('click', function () { selectDraw(i, true); });
      g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectDraw(i, true); } });
    });
  }

  function selectDraw(i, user) {
    state.draw = i;
    renderPheno(state.record);
    renderDrawPanel(state.record, i);
    if (user) {
      var g = document.querySelector('[data-draw="' + i + '"]');
      if (g) g.focus({ preventScroll: true });
    }
  }

  function rangeBar(value, range, w) {
    var lo = range[0], hi = range[1];
    var span = Math.max(hi - lo, 1e-9);
    var dmin = Math.min(lo - span * 0.35, value - span * 0.1), dmax = Math.max(hi + span * 0.35, value + span * 0.1);
    var x = linearScale(dmin, dmax, 4, w - 4);
    var outside = value < lo || value > hi;
    return svgOpen(w, 22) +
      '<rect x="' + x(lo).toFixed(1) + '" y="7" width="' + (x(hi) - x(lo)).toFixed(1) + '" height="8" rx="1.5" fill="var(--slate)" fill-opacity="0.32"/>' +
      (outside
        ? '<circle cx="' + x(value).toFixed(1) + '" cy="11" r="5" fill="var(--ground)" stroke="var(--self)" stroke-width="2"/>'
        : '<circle cx="' + x(value).toFixed(1) + '" cy="11" r="5" fill="var(--self)"/>') +
      '</svg>';
  }

  function renderDrawPanel(record, i) {
    var draws = record.labs.draws.filter(function (d) { return d.phenoage != null; });
    var d = draws[i];
    var markers = record.labs.markers;
    var host = $('draw-panel');
    var barW = narrow() ? 120 : 150;
    var groups = [['Nine PhenoAge inputs', true], ['Other panels', false]];
    var html = ['<div class="draw-head"><h3>' + longDate(d.date) + ' <span style="color:var(--ink-3)">· age ' + fmt(d.age, 1) + '</span></h3><p>PhenoAge ' + fmt(d.phenoage, 1) + ', ' + fmt(Math.abs(d.gap_years), 1) + ' years ' + (d.gap_years < 0 ? 'younger' : 'older') + ' than calendar age. ' + (d.outside_range.length ? d.outside_range.length + ' of ' + Object.keys(d.values).length + ' markers outside the reference range.' : 'Every marker inside its reference range.') + '</p></div>'];
    html.push('<div class="marker-grid">');
    groups.forEach(function (g) {
      html.push('<div class="marker-group">' + g[0] + '</div>');
      Object.keys(markers).forEach(function (key) {
        var m = markers[key];
        if (!!m.phenoage !== g[1]) return;
        var value = d.values[key];
        if (value == null) return;
        var outside = value < m.range[0] || value > m.range[1];
        html.push('<div class="marker"><div class="name"><b>' + esc(m.label) + '</b> <span>' + value + ' <small>' + esc(m.unit) + '</small></span>' + (outside ? '<span class="flag">outside ' + m.range[0] + '–' + m.range[1] + '</span>' : '<small>' + m.range[0] + '–' + m.range[1] + '</small>') + '</div>' + rangeBar(value, m.range, barW) + '</div>');
      });
    });
    html.push('</div>');
    html.push('<div class="legend"><span><i class="band"></i>Reference range</span><span><i class="self"></i>Inside</span><span><i class="hollow"></i>Outside</span></div>');
    html.push('<p class="fig-note">' + esc(record.labs.boundary) + '</p>');
    host.innerHTML = html.join('');
  }

  /* ---------- habits ---------- */

  function renderHeatmap(record) {
    var cal = record.habits.calendar;
    var host = $('heatmap');
    var cols = record.habits.columns.concat(['caffeine_cutoff_2pm']);
    var weeks = cal.weeks;
    var html = ['<div class="heat-rows" style="--weeks:' + weeks.length + '">'];
    cols.forEach(function (c) {
      var t = cal.totals[c];
      html.push('<div class="heat-row"><div class="name">' + esc(t.label) + '</div><div class="heat-cells">');
      weeks.forEach(function (wk, wi) {
        var done = 0, logged = 0;
        wk.days.forEach(function (d) { if (d.done[c] != null) { logged++; done += d.done[c]; } });
        var v = logged ? done / logged : null;
        var label = t.label + ', week of ' + shortDate(wk.start) + ': ' + (logged ? done + ' of ' + logged + ' logged days' : 'not logged');
        html.push('<button class="heat-cell" type="button" style="--v:' + (v == null ? 0 : v.toFixed(2)) + '" data-v="' + (v == null ? 'none' : v.toFixed(2)) + '" data-label="' + esc(label) + '" aria-label="' + esc(label) + '"></button>');
      });
      html.push('</div><div class="count">' + t.done + '/' + t.logged + '</div></div>');
    });
    html.push('</div>');
    html.push('<div class="heat-axis"><div></div><div><span>' + monthYear(cal.first) + '</span><span>' + monthYear(cal.last) + '</span></div><div></div></div>');
    html.push('<p class="heat-readout" id="heat-readout">Each square is one week, shaded by the share of logged days the practice was done. Tap a square to read it.</p>');
    host.innerHTML = html.join('');
    var readout = $('heat-readout');
    host.querySelectorAll('.heat-cell').forEach(function (b) {
      var show = function () { readout.textContent = b.dataset.label; };
      b.addEventListener('click', show);
      b.addEventListener('focus', show);
      b.addEventListener('mouseenter', show);
    });
  }

  function renderHabitEffects(record) {
    var host = $('habit-effects');
    var o = OUTCOME[state.habitOutcome];
    var rows = record.habits.effects.filter(function (r) { return r.outcome === state.habitOutcome; });
    var w = width(host) - (narrow() ? 112 : 162);
    var dom = sharedDomain(rows, o.pad);
    var scale = linearScale(dom[0], dom[1], 0, w);
    var html = ['<div class="toolbar"><p>Next-day outcome on days the practice was done, minus days it was not. ' + (o.better === 'lower' ? 'Lower is better here.' : 'Higher is better here.') + '</p><div class="toggle" role="group" aria-label="Outcome">'];
    Object.keys(OUTCOME).forEach(function (k) {
      html.push('<button type="button" data-habit-outcome="' + k + '" aria-pressed="' + (k === state.habitOutcome) + '">' + OUTCOME[k].label + '</button>');
    });
    html.push('</div></div><div class="effect-rows">');
    rows.forEach(function (r) {
      var back = {};
      var plot = intervalRow(w, 46, scale, r, { unit: o.unit, digits: 2, readingOut: back });
      html.push('<div class="effect-row"><div class="name">' + esc(r.label) + '<small>' + r.n_on + ' done / ' + r.n_off + ' not' + (back.text ? ' <em>· ' + esc(back.text) + '</em>' : '') + '</small></div>' + svgOpen(w, 46) + plot + '</svg></div>');
    });
    html.push('</div><div class="effect-axis"><div></div>' + axisRow(w, scale, dom[0], dom[1], o.unit) + '</div>');
    var paired = rows.length ? rows[0].n_on + rows[0].n_off : 0;
    var logged = record.habits.calendar.totals[rows[0].habit].logged;
    html.push('<p class="fig-note">Filled: the 95% interval excludes zero (an association, not a cause). Hollow: the interval includes zero, so nothing is detected at this sample size. Counts here are days with a recorded next night (' + paired + ' of the ' + logged + ' logged days for the first row), so they are smaller than the calendar totals above. ' + esc(record.habits.note) + '</p>');
    host.innerHTML = html.join('');
    host.querySelectorAll('[data-habit-outcome]').forEach(function (b) {
      b.addEventListener('click', function () { state.habitOutcome = b.dataset.habitOutcome; renderHabitEffects(record); });
    });
  }

  function renderInterventions(record) {
    var host = $('interventions');
    var w = width(host);
    var innerW = narrow() ? w - 104 : Math.floor(w * 0.58) - 150;
    var html = [];
    record.interventions.forEach(function (iv) {
      html.push('<div class="intervention"><div><h4>' + esc(iv.title) + '</h4><div class="when">' + longDate(iv.date) + ' · ' + esc(iv.category) + '</div><div class="planted"><em>Generator truth:</em> ' + esc(iv.planted) + '</div></div><div class="iv-effects">');
      iv.effects.forEach(function (e) {
        var o = OUTCOME[e.outcome];
        var dom = sharedDomain([e], o.pad);
        var scale = linearScale(dom[0], dom[1], 0, innerW);
        var back = {};
        var plot = intervalRow(innerW, 46, scale, { effect: e.effect, ci_low: e.ci_low, ci_high: e.ci_high, note: 'not enough days on both sides' }, { unit: o.unit, digits: 2, detectedWord: 'change observed', readingOut: back });
        html.push('<div class="iv-effect"><div class="lab">' + esc(o.long) + (back.text ? '<em>' + esc(back.text) + '</em>' : '') + '</div>' + svgOpen(innerW, 46) + plot + '</svg></div>');
      });
      html.push('</div></div>');
    });
    html.push('<p class="fig-note">Window comparisons are time-confounded by construction. The first change is the lesson: the generator planted nothing, yet the HRV window reads as a drop at this sample size. That is why the featured question below uses paired nights and a pre-registered retest instead.</p>');
    host.innerHTML = html.join('');
  }

  function renderSupplements(record) {
    var host = $('supplements');
    var barW = narrow() ? 110 : 140;
    var supps = record.supplements;
    var t0 = dayNum(supps.reduce(function (m, s) { return s.first < m ? s.first : m; }, supps[0].first));
    var t1 = dayNum(record.scope.last_night);
    var x = linearScale(t0, t1, 2, barW - 2);
    var html = [];
    supps.forEach(function (s) {
      html.push('<div class="supp"><div class="name">' + esc(s.label) + '<small>' + s.days + ' days · ' + (s.current ? 'current' : 'stopped ' + monthYear(s.last)) + '</small></div>' + svgOpen(barW, 14) + '<line x1="2" y1="7" x2="' + (barW - 2) + '" y2="7" class="grid-line"/><line x1="' + x(dayNum(s.first)).toFixed(1) + '" y1="7" x2="' + x(dayNum(s.last)).toFixed(1) + '" y2="7" stroke="var(--self)" stroke-opacity="' + (s.current ? 0.95 : 0.5) + '" stroke-width="6" stroke-linecap="round"/></svg></div>');
    });
    html.push('<div class="supp-axis"><span>' + supps.reduce(function (m, s) { return s.first < m ? s.first : m; }, supps[0].first).slice(0, 4) + '</span><span>' + record.scope.last_night.slice(0, 4) + '</span></div>');
    html.push('<p class="fig-note">Mined from the daily log, so each supplement is a column that can be compared against recovery like any habit. Days logged, not doses.</p>');
    host.innerHTML = html.join('');
  }

  function renderBenchmarks(record) {
    var host = $('benchmarks');
    var barW = Math.max(140, width(host) - (narrow() ? 112 : 150));
    var html = [];
    record.benchmarks.forEach(function (b) {
      var lo = Math.min(b.persona_mean, b.reference), hi = Math.max(b.persona_mean, b.reference);
      var span = Math.max(hi - lo, b.reference * 0.06);
      var x = linearScale(lo - span * 1.6, hi + span * 1.6, 8, barW - 8);
      var xr = x(b.reference), xp = x(b.persona_mean);
      var herLabel = fmt(b.persona_mean, b.digits) + ' ' + b.unit;
      var refLabel = 'cohort ' + b.reference;
      html.push('<div class="bench"><div class="name">' + esc(b.label) + '<small>her last ' + b.window_days + ' days, ' + b.n + ' nights</small></div>' + svgOpen(barW, 52) +
        '<line x1="8" y1="30" x2="' + (barW - 8) + '" y2="30" class="grid-line"/>' +
        '<line x1="' + xr.toFixed(1) + '" y1="20" x2="' + xr.toFixed(1) + '" y2="40" stroke="var(--slate)" stroke-width="2"/>' +
        '<text x="' + clamp(xr, 34, barW - 34).toFixed(1) + '" y="50" text-anchor="middle" class="axis-label">' + esc(refLabel) + '</text>' +
        '<circle cx="' + xp.toFixed(1) + '" cy="30" r="6" fill="var(--self)"/>' +
        '<text x="' + clamp(xp, 30, barW - 30).toFixed(1) + '" y="12" text-anchor="middle" class="value-label">' + esc(herLabel) + '</text>' +
        '</svg></div>');
    });
    html.push('<p class="bench-note">Reference values are approximate age-band figures written into the code as constants with a note, for a woman of ' + record.benchmarks[0].age + '; they are not a cited cohort study. Ivory is her mean, slate the reference. HRV is device- and method-dependent; these are context, not targets.</p>');
    host.innerHTML = html.join('');
  }

  /* ---------- featured experiment ---------- */

  function renderFeatured(analysis, plan) {
    var primary = analysis.primary_effect;
    var paired = primary.n_on + primary.n_off;
    $('experiment-h').textContent = analysis.question;
    $('experiment-lede').textContent = 'The question the genome nominated and the record could answer. For ' + analysis.dataset.recorded_days + ' recorded days from ' + longDate(analysis.dataset.start_date) + ' to ' + longDate(analysis.dataset.end_date) + ', each evening’s caffeine timing was paired with the following night’s recovery: ' + paired + ' paired nights, ' + primary.n_on + ' after a 2 PM cutoff and ' + primary.n_off + ' after usual timing.';
    $('headline-number').innerHTML = '<div class="num">' + signed(primary.effect) + '<small>ms HRV</small></div><p class="read">Nights after a 2 PM cutoff averaged <strong>' + signed(primary.effect) + ' ms</strong> higher HRV, 95% interval ' + signed(primary.ci_low) + ' to ' + signed(primary.ci_high) + '. <em>Association only;</em> replicate before acting.</p>';

    var host = $('forest');
    var rows = [primary].concat(analysis.secondary_effects);
    var w = width(host) - (narrow() ? 112 : 182);
    var html = ['<div class="effect-rows">'];
    rows.forEach(function (r) {
      var o = OUTCOME[r.outcome];
      var dom = sharedDomain([r], o.pad);
      var scale = linearScale(dom[0], dom[1], 0, w);
      var back = {};
      var plot = intervalRow(w, 54, scale, r, { unit: o.unit, digits: 2, readingOut: back });
      html.push('<div class="effect-row"><div class="name">' + esc(o.long) + '<small>' + r.n_on + ' cutoff / ' + r.n_off + ' usual nights' + (back.text ? ' <em>· ' + esc(back.text) + '</em>' : '') + '</small></div>' + svgOpen(w, 54) + plot + '</svg></div>');
    });
    html.push('</div><p class="fig-note">Each outcome on its own scale; the vertical line is no difference. Resting heart rate falling after cutoff nights points the same way as the other two.</p>');
    host.innerHTML = html.join('');

    renderNightly(analysis);
    renderPlan(plan, analysis);
  }

  function renderNightly(analysis) {
    var host = $('nightly');
    var metric = state.nightMetric;
    var o = OUTCOME[metric];
    var timeline = analysis.timeline;
    var w = width(host), h = narrow() ? 240 : 300;
    var left = 40, right = 12, top = 22, bottom = h - 36;
    var values = timeline.map(function (p) { return p[metric]; });
    var valid = values.filter(function (v) { return v != null; });
    var min = Math.min.apply(null, valid) - o.pad, max = Math.max.apply(null, valid) + o.pad;
    var x = function (i) { return left + (w - left - right) * window.LiveForeverChart.calendarFraction(timeline, i); };
    var y = linearScale(min, max, bottom, top);
    var averages = values.map(function (_, i) { return window.LiveForeverChart.rollingMean(timeline, i, metric, 7); });
    var path = [], started = false;
    averages.forEach(function (v, i) {
      if (v == null) { started = false; return; }
      path.push((started ? 'L' : 'M') + x(i).toFixed(1) + ',' + y(v).toFixed(1));
      started = true;
    });
    var out = ['<div class="toolbar"><p>Every recorded night in the last eight weeks of the window, coloured by the previous day’s caffeine timing, with a seven-day mean.</p><div class="toggle" role="group" aria-label="Metric">'];
    Object.keys(OUTCOME).slice(0, 2).forEach(function (k) {
      out.push('<button type="button" data-night-metric="' + k + '" aria-pressed="' + (k === metric) + '">' + OUTCOME[k].label + '</button>');
    });
    out.push('</div></div><div class="chart-wrap">');
    out.push(svgOpen(w, h, 'role="img" aria-label="Nightly ' + o.long + ' by prior-day caffeine timing"'));
    niceTicks(min, max, 5).forEach(function (t) {
      if (t < min || t > max) return;
      out.push('<line x1="' + left + '" y1="' + y(t).toFixed(1) + '" x2="' + (w - right) + '" y2="' + y(t).toFixed(1) + '" class="grid-line"/>');
      out.push('<text x="' + (left - 8) + '" y="' + (y(t) + 4).toFixed(1) + '" text-anchor="end" class="axis-label">' + t + '</text>');
    });
    out.push('<text x="' + left + '" y="' + (top - 8) + '" class="axis-label">' + esc(o.unit) + '</text>');
    // month ticks
    var seen = {};
    timeline.forEach(function (p, i) {
      var m = p.date.slice(0, 7);
      if (seen[m]) return;
      seen[m] = true;
      if (i === 0 && parse(p.date).getDate() > 20) return;
      out.push('<text x="' + x(i).toFixed(1) + '" y="' + (bottom + 20) + '" class="axis-label">' + (i === 0 ? shortDate(p.date) : MONTHS[parse(p.date).getMonth()]) + '</text>');
    });
    out.push('<text x="' + (w - right) + '" y="' + (bottom + 20) + '" text-anchor="end" class="axis-label">' + shortDate(timeline[timeline.length - 1].date) + '</text>');
    out.push('<path d="' + path.join(' ') + '" fill="none" stroke="var(--self)" stroke-opacity="0.7" stroke-width="1.5" stroke-linejoin="round"/>');
    timeline.forEach(function (p, i) {
      var v = p[metric];
      if (v == null) return;
      var c = window.LiveForeverChart.condition(p);
      var fill = c === 'cutoff' ? 'var(--accent)' : c === 'usual' ? 'var(--slate)' : 'var(--ground)';
      var stroke = c === 'unknown' ? 'var(--slate)' : 'none';
      var label = weekday(p.date) + ' ' + shortDate(p.date) + ': ' + fmt(v, o.digits) + ' ' + o.unit + ', after ' + (c === 'cutoff' ? 'a 2 PM cutoff' : c === 'usual' ? 'usual timing' : 'an unrecorded day');
      out.push('<g class="night" role="button" tabindex="0" data-i="' + i + '" aria-label="' + esc(label) + '">');
      out.push('<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="12" fill="transparent"/>');
      out.push('<circle class="night-ring" cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="9"/>');
      out.push('<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="' + (narrow() ? 3.5 : 4.5) + '" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1.5"/>');
      out.push('</g>');
    });
    out.push('</svg><div class="chart-tooltip" id="night-tip" role="status" hidden></div></div>');
    out.push('<div class="legend"><span><i class="accent"></i>After a 2 PM cutoff</span><span><i class="slate"></i>After usual timing</span><span><i class="hollow"></i>Previous day unrecorded</span><span><i class="line"></i>7-day mean</span></div>');
    host.innerHTML = out.join('');
    host.querySelectorAll('[data-night-metric]').forEach(function (b) {
      b.addEventListener('click', function () { state.nightMetric = b.dataset.nightMetric; renderNightly(analysis); });
    });
    var tip = $('night-tip');
    var wrap = host.querySelector('.chart-wrap');
    host.querySelectorAll('.night').forEach(function (g) {
      var show = function () {
        var c = g.querySelector('circle:last-child');
        var cx = Number(c.getAttribute('cx')), cy = Number(c.getAttribute('cy'));
        tip.innerHTML = '<b>' + esc(g.getAttribute('aria-label').split(': ')[0]) + '</b><br>' + esc(g.getAttribute('aria-label').split(': ').slice(1).join(': '));
        tip.hidden = false;
        var tw = tip.offsetWidth;
        tip.style.left = clamp(cx - tw / 2, 0, wrap.clientWidth - tw) + 'px';
        tip.style.top = Math.max(0, cy - tip.offsetHeight - 16) + 'px';
      };
      var hide = function () { tip.hidden = true; };
      g.addEventListener('mouseenter', show);
      g.addEventListener('focus', show);
      g.addEventListener('mouseleave', hide);
      g.addEventListener('blur', hide);
      g.addEventListener('click', show);
    });
  }

  function renderPlan(plan, analysis) {
    var host = $('plan');
    var html = ['<div><div class="schedule" aria-label="Fourteen-day schedule">'];
    plan.schedule.forEach(function (d) {
      var cut = d.condition.indexOf('Cutoff') === 0;
      html.push('<div class="day ' + (cut ? 'cutoff' : 'usual') + '" aria-label="' + longDate(d.date) + ': ' + esc(d.condition) + '"><b>' + weekday(d.date) + '</b><b>' + parse(d.date).getDate() + '</b><span>' + (cut ? 'Cutoff' : 'Usual') + '</span></div>');
    });
    html.push('</div><div class="legend"><span><i class="accent"></i>Cutoff by 2 PM</span><span><i class="slate"></i>Usual timing</span></div>');
    html.push('<p class="fig-note">' + esc(plan.design) + ' Seven days of each, in a fixed seeded order, starting ' + longDate(plan.schedule[0].date) + '.</p></div>');
    html.push('<div><h4>Decision rule</h4><p class="rule">' + esc(plan.decision_rule) + '</p><h4>Held constant</h4><ul>' + plan.controls.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul><details><summary>When to pause</summary><ul>' + plan.stop_conditions.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul></details></div>');
    host.innerHTML = html.join('');
  }

  /* ---------- genome ---------- */

  function renderGenome(record) {
    var list = $('helix-list');
    var findings = record.genome.findings;
    list.innerHTML = findings.map(function (f, i) {
      return '<button class="gene" type="button" role="listitem" data-gene="' + i + '" aria-pressed="false"><i aria-hidden="true"></i><span><b>' + esc(f.gene) + '</b><small>' + esc(f.name) + '</small></span><span class="gt">' + esc(f.call) + '</span></button>';
    }).join('');
    list.querySelectorAll('.gene').forEach(function (b) {
      b.addEventListener('click', function () { selectGene(Number(b.dataset.gene), 'list'); });
    });
    if (window.LiveForeverGenome) {
      window.LiveForeverGenome.init($('helix'), findings, function (i) { selectGene(i, 'helix'); });
    }
    selectGene(0, 'init');
  }

  function selectGene(i, source) {
    var record = state.record;
    var f = record.genome.findings[i];
    document.querySelectorAll('.gene').forEach(function (b) { b.setAttribute('aria-pressed', String(Number(b.dataset.gene) === i)); });
    $('finding').innerHTML =
      '<h3>' + esc(f.gene) + ' <span style="color:var(--ink-3)">' + esc(f.name) + '</span><span class="gt">' + esc(f.marker) + ' · ' + esc(f.call) + '</span></h3>' +
      '<div><h4>What this genotype is often studied as</h4><p>' + esc(f.context) + '</p></div>' +
      '<div><h4>How LiveForever uses it</h4><p>' + esc(f.uses) + '</p></div>' +
      '<p class="boundary">' + esc(f.boundary) + '</p>';
    if (window.LiveForeverGenome && source !== 'helix') window.LiveForeverGenome.select(i);
  }

  /* ---------- how it works ---------- */

  function renderMethod(analysis, record) {
    var q = analysis.quality;
    $('quality').innerHTML = '<div class="grade"><b>' + esc(q.grade) + '</b>Evidence-quality grade for the featured question, <span>' + q.score + ' of 100: ' + Math.round(q.coverage * 100) + '% calendar coverage, ' + q.paired_days + ' paired nights, balance ' + q.condition_on_n + ' to ' + q.condition_off_n + '.</span></div><ul>' + q.warnings.map(function (w) { return '<li>' + esc(w) + '</li>'; }).join('') + '<li>The grade is deterministic. The model cannot raise it or suppress a warning.</li></ul>';
    $('method-body').innerHTML = '<ol>' + analysis.calculation_provenance.concat(record.provenance).map(function (p) { return '<li>' + esc(p) + '</li>'; }).join('') + '</ol><p>' + esc(analysis.claim_boundary) + '</p><p>Regenerate everything with <code>PYTHONPATH=src python3 -m liveforever_lab.cli</code>; the judged interface is preserved at <a href="index-buildweek.html">index-buildweek.html</a> and commit 6978bcd.</p>';
  }

  /* ---------- orchestration ---------- */

  function renderAll() {
    state.width = document.documentElement.clientWidth;
    var r = state.record, a = state.analysis;
    renderDial(r.hero);
    renderScope(r.scope);
    renderAtlas(r);
    if (state.draw == null) state.draw = r.hero.trend.length - 1;
    renderPheno(r);
    renderDrawPanel(r, state.draw);
    renderHeatmap(r);
    renderHabitEffects(r);
    renderInterventions(r);
    renderSupplements(r);
    renderBenchmarks(r);
    renderFeatured(a, state.plan);
    renderMethod(a, r);
  }

  var LEGACY = { overview: 'top', experiment: 'experiment', data: 'data' };

  function landOnHash() {
    var hash = window.location.hash.replace('#', '');
    if (!hash) return;
    var target = document.getElementById(LEGACY[hash] || hash);
    if (target) target.scrollIntoView({ block: 'start' });
  }

  Promise.all([
    fetch('analysis.json').then(function (r) { return r.json(); }),
    fetch('record.json').then(function (r) { return r.json(); })
  ]).then(function (payloads) {
    state.analysis = payloads[0].analysis;
    state.plan = payloads[0].plan;
    state.record = payloads[1];
    renderAll();
    renderGenome(state.record);
    landOnHash();
    var last = state.width, timer;
    window.addEventListener('resize', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        if (document.documentElement.clientWidth !== last) { last = document.documentElement.clientWidth; renderAll(); }
      }, 160);
    });
    window.addEventListener('hashchange', landOnHash);
  }).catch(function (err) {
    $('record').insertAdjacentHTML('afterbegin', '<p class="chapter-lede" role="alert">The synthetic record could not be loaded (' + esc(err.message) + '). The JSON files are generated by the Python CLI; see the repository README.</p>');
  });
}());
