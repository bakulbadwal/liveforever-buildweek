(function () {
  'use strict';

  var state = {
    payload: null,
    metric: 'hrv_ms',
    view: 'overview'
  };

  var metricMeta = {
    hrv_ms: {
      tab: 'HRV',
      axis: 'HRV (ms)',
      unit: 'ms',
      digits: 1,
      padding: 3
    },
    sleep_hours: {
      tab: 'Sleep',
      axis: 'Sleep (hours)',
      unit: 'h',
      digits: 2,
      padding: 0.25
    }
  };

  function fmt(value, digits) {
    var precision = digits == null ? 2 : digits;
    return Number(value).toFixed(precision);
  }

  function signed(value, digits) {
    return (value >= 0 ? '+' : '') + fmt(value, digits);
  }

  function shortDate(value) {
    return new Date(value + 'T12:00:00').toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  }

  function dayLabel(value) {
    return new Date(value + 'T12:00:00').toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  }

  function sourceRow(label, value, description) {
    return [
      '<div class="source-row">',
      '<span>', label, '</span>',
      '<div><strong>', value, '</strong><p>', description, '</p></div>',
      '</div>'
    ].join('');
  }

  function render(payload) {
    state.payload = payload;

    var a = payload.analysis;
    var p = payload.plan;
    var primary = a.primary_effect;
    var sleep = a.secondary_effects.find(function (item) {
      return item.outcome === 'sleep_hours';
    });
    var rhr = a.secondary_effects.find(function (item) {
      return item.outcome === 'resting_hr';
    });

    var schedule = p.schedule.map(function (day) {
      var conditionClass = day.condition.indexOf('Cutoff') === 0 ? 'cutoff' : 'usual';
      return [
        '<div class="day ', conditionClass, '">',
        '<strong>', dayLabel(day.date), '</strong>',
        '<span>', day.condition, '</span>',
        '</div>'
      ].join('');
    }).join('');

    var controls = p.controls.map(function (item) {
      return [
        '<div class="control">',
        '<div class="check" aria-hidden="true">&#10003;</div>',
        '<div>', item, '</div>',
        '</div>'
      ].join('');
    }).join('');

    var stopConditions = p.stop_conditions.map(function (item) {
      return '<li>' + item + '</li>';
    }).join('');

    var warnings = a.quality.warnings.map(function (item) {
      return '<div class="warning">' + item + '</div>';
    }).join('');

    var calculations = a.calculation_provenance.map(function (item) {
      return '<div>' + item + '</div>';
    }).join('');

    document.getElementById('app').innerHTML = [
      '<section class="view" id="view-overview" data-view-panel="overview">',
        '<div class="page-intro">',
          '<p class="kicker">Maya&#39;s current question</p>',
          '<h1>', a.question, '</h1>',
          '<p>Compare one daily habit with the following night&#39;s recovery, then turn the signal into a controlled retest.</p>',
        '</div>',

        '<div class="result-band">',
          '<div class="primary-result">',
            '<div class="label">Observed HRV difference</div>',
            '<div class="result-value">', signed(primary.effect), ' ms</div>',
            '<p class="result-copy">Higher next-day HRV when caffeine stopped by 2 PM.</p>',
            '<div class="result-meta">',
              '<span class="claim-pill">Association only</span>',
              '<span>95% interval ', signed(primary.ci_low), ' to ', signed(primary.ci_high), '</span>',
            '</div>',
          '</div>',
          '<div class="supporting-metrics">',
            '<div class="support-metric">',
              '<div class="label">Sleep duration</div>',
              '<strong>', signed(sleep.effect), ' h</strong>',
              '<p>Difference between cutoff and usual-timing nights.</p>',
            '</div>',
            '<div class="support-metric">',
              '<div class="label">Resting HR</div>',
              '<strong>', signed(rhr.effect), ' bpm</strong>',
              '<p>Lower values followed cutoff days in this dataset.</p>',
            '</div>',
            '<div class="support-metric">',
              '<div class="label">Paired nights</div>',
              '<strong>', a.quality.paired_days, '</strong>',
              '<p>', a.quality.condition_on_n, ' cutoff and ', a.quality.condition_off_n, ' usual-timing observations.</p>',
            '</div>',
          '</div>',
        '</div>',

        '<section class="journey" aria-labelledby="journey-heading">',
          '<div class="section-bar">',
            '<div><h2 id="journey-heading">How we got here</h2><p>One question, one comparison, one next step.</p></div>',
          '</div>',
          '<div class="journey-grid">',
            '<button class="journey-step" type="button" data-go="overview">',
              '<span class="step-index">01 &middot; Habit</span>',
              '<span class="step-value">Caffeine by 2 PM</span>',
              '<span class="step-note">Compared with usual timing</span>',
            '</button>',
            '<button class="journey-step" type="button" data-go="data">',
              '<span class="step-index">02 &middot; Comparison</span>',
              '<span class="step-value">', a.quality.paired_days, ' paired nights</span>',
              '<span class="step-note">', a.quality.condition_on_n, ' cutoff / ', a.quality.condition_off_n, ' usual</span>',
            '</button>',
            '<button class="journey-step" type="button" data-open-method="true">',
              '<span class="step-index">03 &middot; Signal</span>',
              '<span class="step-value">', signed(primary.effect), ' ms HRV</span>',
              '<span class="step-note">95% interval ', signed(primary.ci_low), ' to ', signed(primary.ci_high), '</span>',
            '</button>',
            '<button class="journey-step" type="button" data-go="experiment">',
              '<span class="step-index">04 &middot; Next test</span>',
              '<span class="step-value">14-day crossover</span>',
              '<span class="step-note">Predefined controls and decision rule</span>',
            '</button>',
          '</div>',
        '</section>',

        '<div class="overview-grid">',
          '<section class="workspace" aria-labelledby="timeline-heading">',
            '<div class="chart-toolbar">',
              '<div><h2 id="timeline-heading">Recovery timeline</h2><p>Nightly recovery by prior-day caffeine timing</p></div>',
              '<div class="segmented" aria-label="Chart metric">',
                '<button class="active" type="button" data-metric="hrv_ms" aria-pressed="true">HRV</button>',
                '<button type="button" data-metric="sleep_hours" aria-pressed="false">Sleep</button>',
              '</div>',
            '</div>',
            '<div class="chart-wrap">',
              '<svg id="chart" viewBox="0 0 760 250" role="img" aria-labelledby="chart-title chart-description"></svg>',
              '<div class="chart-tooltip" id="chart-tooltip" role="status" hidden></div>',
            '</div>',
            '<div class="legend">',
              '<span><i style="background:var(--green)"></i>Cutoff by 2 PM</span>',
              '<span><i style="background:var(--coral)"></i>Usual timing</span>',
              '<span><i style="background:#63788c"></i>Prior timing unrecorded</span>',
              '<span><i style="background:#87959a"></i>7-day mean</span>',
            '</div>',
          '</section>',

          '<aside class="reading-panel">',
            '<h2>What this means</h2>',
            '<p>Cutoff days were associated with higher HRV and longer sleep. The next useful step is to repeat the comparison under a balanced schedule.</p>',
            '<div class="reading-facts">',
              '<div class="reading-fact"><span>Coverage</span><strong>', Math.round(a.quality.coverage * 100), '% of calendar days</strong></div>',
              '<div class="reading-fact"><span>Balance</span><strong>', a.quality.condition_on_n, ' vs ', a.quality.condition_off_n, ' nights</strong></div>',
              '<div class="reading-fact"><span>Data grade</span><strong>', a.quality.grade, ' &middot; ', a.quality.score, '/100</strong></div>',
            '</div>',
            '<div class="actions">',
              '<button class="button primary" type="button" data-go="experiment">View 14-day retest</button>',
              '<button class="button" type="button" data-open-method="true">Inspect method</button>',
            '</div>',
          '</aside>',
        '</div>',
      '</section>',

      '<section class="view" id="view-experiment" data-view-panel="experiment" hidden>',
        '<div class="page-intro">',
          '<p class="kicker">14-day retest</p>',
          '<h1>Retest the signal under a balanced schedule.</h1>',
          '<p>Alternate cutoff and usual-timing days while keeping the major inputs steady.</p>',
        '</div>',
        '<div class="experiment-layout">',
          '<section class="schedule-panel" aria-labelledby="schedule-heading">',
            '<div class="schedule-head">',
              '<div><h2 id="schedule-heading">', p.title, '</h2><p>', p.design, '</p></div>',
              '<div class="schedule-key">',
                '<span><i style="background:var(--green)"></i>Cutoff</span>',
                '<span><i style="background:var(--coral)"></i>Usual</span>',
              '</div>',
            '</div>',
            '<div class="schedule">', schedule, '</div>',
          '</section>',
          '<aside class="controls-panel">',
            '<h2>Predefined controls</h2>',
            controls,
            '<div class="decision"><strong>Decision rule</strong>', p.decision_rule, '</div>',
            '<details class="pause-details">',
              '<summary>When to pause</summary>',
              '<ul>', stopConditions, '</ul>',
            '</details>',
          '</aside>',
        '</div>',
      '</section>',

      '<section class="view" id="view-data" data-view-panel="data" hidden>',
        '<div class="page-intro">',
          '<p class="kicker">Data and methods</p>',
          '<h1>Know what is behind the number.</h1>',
          '<p>Inspect completeness, context, and calculation details without crowding the primary result.</p>',
        '</div>',

        '<div class="quality-strip" aria-label="Data quality summary">',
          '<div class="quality-stat"><div class="label">Evidence grade</div><strong>', a.quality.grade, '</strong><p>', a.quality.score, ' out of 100</p></div>',
          '<div class="quality-stat"><div class="label">Calendar coverage</div><strong>', Math.round(a.quality.coverage * 100), '%</strong><p>', a.dataset.recorded_days, ' fictional recorded days</p></div>',
          '<div class="quality-stat"><div class="label">Cutoff nights</div><strong>', a.quality.condition_on_n, '</strong><p>Paired with next-day outcomes</p></div>',
          '<div class="quality-stat"><div class="label">Usual nights</div><strong>', a.quality.condition_off_n, '</strong><p>Paired with next-day outcomes</p></div>',
        '</div>',

        '<div class="data-layout">',
          '<section class="quality-panel">',
            '<h2>Connected data</h2>',
            '<p class="panel-lede">Four evidence layers support the question; none determines the answer alone.</p>',
            '<div class="source-list">',
              sourceRow('Wearables', a.dataset.recorded_days + ' daily records', 'HRV, sleep duration, resting heart rate, and missingness.'),
              sourceRow('Habit log', a.quality.paired_days + ' paired nights', 'Caffeine timing, total dose, training load, meditation, and alcohol.'),
              sourceRow('Laboratory', a.longevity_snapshot.completeness, 'Synthetic inputs for the published PhenoAge calculation.'),
              sourceRow('Genomics', '1 synthetic marker', 'Caffeine-metabolism context used to prioritize the question.'),
            '</div>',
            '<div class="warning-list">', warnings, '</div>',
          '</section>',

          '<aside class="context-panel">',
            '<h2>Personal context</h2>',
            '<p class="panel-lede">Context helps choose what to test. The observed data still owns the result.</p>',
            '<div class="context-item">',
              '<div class="context-value">', a.genomics_context.gene, '<br>', a.genomics_context.synthetic_genotype, '</div>',
              '<div class="context-copy"><strong>Caffeine metabolism context</strong><p>', a.genomics_context.annotation, ' One synthetic marker is used to prioritize the question, not determine the result.</p></div>',
            '</div>',
            '<div class="context-item">',
              '<div class="context-value">', fmt(a.longevity_snapshot.phenoage, 1), '<br>yrs</div>',
              '<div class="context-copy"><strong>PhenoAge snapshot</strong><p>Chronological age ', fmt(a.longevity_snapshot.chronological_age, 0), '; difference ', signed(a.longevity_snapshot.difference_years, 1), ' years. Calculated from ', a.longevity_snapshot.completeness.toLowerCase(), '.</p></div>',
            '</div>',
          '</aside>',

          '<section class="method-panel">',
            '<h2>Calculation method</h2>',
            '<p class="panel-lede">Deterministic Python produces every displayed value. The LiveForever Codex Skill uses GPT-5.6 to explain the result and adapt the retest without changing the calculations.</p>',
            '<details class="method-details" id="method-details">',
              '<summary>Show calculation and provenance</summary>',
              '<div class="method-content">',
                '<div class="formula-list">', calculations, '</div>',
                '<p><strong>Primary estimate:</strong> ', signed(primary.effect), ' ms, 95% interval ', signed(primary.ci_low), ' to ', signed(primary.ci_high), ', from ', primary.n_on, ' cutoff and ', primary.n_off, ' usual-timing paired nights.</p>',
                '<p>', a.claim_boundary, '</p>',
              '</div>',
            '</details>',
          '</section>',
        '</div>',

        '<div class="privacy-band">',
          '<div><strong>Privacy by design</strong><p>Every record in this public demo is synthetic. No login, external health service, API key, or personal health data is used.</p></div>',
          '<a class="button" href="https://github.com/bakulbadwal/liveforever-buildweek" target="_blank" rel="noreferrer">View source</a>',
        '</div>',
      '</section>'
    ].join('');

    bindControls();
    drawChart(a.timeline, state.metric);

    var initialView = window.location.hash.replace('#', '');
    setView(['overview', 'experiment', 'data'].indexOf(initialView) >= 0 ? initialView : 'overview', false);
  }

  function bindControls() {
    document.querySelectorAll('[data-metric]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.metric = button.dataset.metric;
        document.querySelectorAll('[data-metric]').forEach(function (item) {
          var active = item === button;
          item.classList.toggle('active', active);
          item.setAttribute('aria-pressed', String(active));
        });
        drawChart(state.payload.analysis.timeline, state.metric);
      });
    });

    document.querySelectorAll('[data-go]').forEach(function (button) {
      button.addEventListener('click', function () {
        navigate(button.dataset.go);
      });
    });

    document.querySelectorAll('[data-open-method]').forEach(function (button) {
      button.addEventListener('click', function () {
        navigate('data');
        var method = document.getElementById('method-details');
        method.open = true;
        method.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  }

  function navigate(view) {
    if (window.location.hash !== '#' + view) {
      window.history.pushState({ view: view }, '', '#' + view);
    }
    setView(view, true);
  }

  function setView(view, focusHeading) {
    state.view = view;

    document.querySelectorAll('[data-view-panel]').forEach(function (panel) {
      var active = panel.dataset.viewPanel === view;
      panel.classList.toggle('active', active);
      panel.hidden = !active;
    });

    document.querySelectorAll('[data-view]').forEach(function (button) {
      var active = button.dataset.view === view;
      button.classList.toggle('active', active);
      button.setAttribute('aria-current', active ? 'page' : 'false');
    });

    if (focusHeading) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function drawChart(timeline, metric) {
    var svg = document.getElementById('chart');
    if (!svg) {
      return;
    }

    var meta = metricMeta[metric];
    var values = timeline.map(function (point) { return point[metric]; });
    var valid = values.filter(function (value) { return value != null; });
    var min = Math.min.apply(null, valid) - meta.padding;
    var max = Math.max.apply(null, valid) + meta.padding;
    var left = 48;
    var right = 742;
    var top = 22;
    var bottom = 208;
    var x = function (index) {
      return left + (right - left) * window.LiveForeverChart.calendarFraction(timeline, index);
    };
    var y = function (value) {
      return bottom - (value - min) / (max - min) * (bottom - top);
    };

    var averages = values.map(function (_, index) {
      return window.LiveForeverChart.rollingMean(timeline, index, metric, 7);
    });

    var pathParts = [];
    var started = false;
    averages.forEach(function (value, index) {
      if (value == null) {
        started = false;
        return;
      }
      pathParts.push((started ? 'L' : 'M') + x(index).toFixed(1) + ',' + y(value).toFixed(1));
      started = true;
    });

    var grid = [0, 0.25, 0.5, 0.75, 1].map(function (fraction) {
      var value = max - (max - min) * fraction;
      var yy = top + (bottom - top) * fraction;
      var label = metric === 'hrv_ms' ? value.toFixed(0) : value.toFixed(1);
      return [
        '<line x1="', left, '" y1="', yy, '" x2="', right, '" y2="', yy, '" stroke="#d6dfdc"/>',
        '<text x="', left - 9, '" y="', yy + 4, '" text-anchor="end" fill="#627176" font-size="10">', label, '</text>'
      ].join('');
    }).join('');

    var dots = timeline.map(function (point, index) {
      if (point[metric] == null) {
        return '';
      }
      var condition = window.LiveForeverChart.condition(point);
      return [
        '<circle class="chart-point" tabindex="0" data-index="', index, '" ',
        'cx="', x(index), '" cy="', y(point[metric]), '" r="4.5" ',
        'fill="', condition === 'cutoff' ? '#14745f' : condition === 'usual' ? '#c45b49' : '#63788c', '" ',
        'stroke="#ffffff" stroke-width="1.5">',
        '<title>', shortDate(point.date), ': ', fmt(point[metric], meta.digits), ' ', meta.unit, '</title>',
        '</circle>'
      ].join('');
    }).join('');

    var dateIndexes = [0, Math.floor((timeline.length - 1) / 2), timeline.length - 1];
    var dates = dateIndexes.map(function (index) {
      return [
        '<text x="', x(index), '" y="234" text-anchor="middle" fill="#627176" font-size="10">',
        shortDate(timeline[index].date),
        '</text>'
      ].join('');
    }).join('');

    svg.innerHTML = [
      '<title id="chart-title">Recovery timeline</title>',
      '<desc id="chart-description">', meta.axis, ' by prior-day caffeine timing. Use Tab to inspect individual points.</desc>',
      grid,
      '<path d="', pathParts.join(' '), '" fill="none" stroke="#87959a" stroke-width="2.5"/>',
      dots,
      dates,
      '<text x="', left, '" y="13" fill="#627176" font-size="10">', meta.axis, '</text>'
    ].join('');

    bindChartTooltips(timeline, metric);
  }

  function bindChartTooltips(timeline, metric) {
    var tooltip = document.getElementById('chart-tooltip');
    var wrapper = tooltip.parentElement;
    var meta = metricMeta[metric];

    function show(event) {
      var circle = event.currentTarget;
      var point = timeline[Number(circle.dataset.index)];
      var circleRect = circle.getBoundingClientRect();
      var wrapperRect = wrapper.getBoundingClientRect();
      var prior = window.LiveForeverChart.condition(point);
      var condition = prior === 'cutoff' ? 'Prior day: cutoff by 2 PM' : prior === 'usual' ? 'Prior day: usual timing' : 'Prior-day timing unrecorded';

      tooltip.innerHTML = [
        '<strong>', shortDate(point.date), '</strong><br>',
        fmt(point[metric], meta.digits), ' ', meta.unit, '<br>',
        condition
      ].join('');
      tooltip.hidden = false;

      var desiredLeft = circleRect.left - wrapperRect.left + circleRect.width + 10;
      var desiredTop = circleRect.top - wrapperRect.top - 16;
      tooltip.style.left = Math.min(Math.max(8, desiredLeft), wrapperRect.width - tooltip.offsetWidth - 8) + 'px';
      tooltip.style.top = Math.min(Math.max(8, desiredTop), wrapperRect.height - tooltip.offsetHeight - 8) + 'px';
    }

    function hide() {
      tooltip.hidden = true;
    }

    document.querySelectorAll('.chart-point').forEach(function (circle) {
      circle.addEventListener('pointerenter', show);
      circle.addEventListener('pointermove', show);
      circle.addEventListener('focus', show);
      circle.addEventListener('pointerleave', hide);
      circle.addEventListener('blur', hide);
    });
  }

  document.querySelectorAll('[data-view]').forEach(function (button) {
    button.addEventListener('click', function () {
      navigate(button.dataset.view);
    });
  });

  window.addEventListener('popstate', function () {
    var view = window.location.hash.replace('#', '') || 'overview';
    if (['overview', 'experiment', 'data'].indexOf(view) >= 0) {
      setView(view, false);
    }
  });

  fetch('analysis.json')
    .then(function (response) {
      if (!response.ok) {
        throw new Error('Could not load analysis (' + response.status + ')');
      }
      return response.json();
    })
    .then(render)
    .catch(function (error) {
      document.getElementById('app').innerHTML = [
        '<div class="error-state">',
        '<strong>Demo data could not load.</strong>',
        error.message,
        '<br><br>Serve the demo folder over HTTP rather than opening the file directly.',
        '</div>'
      ].join('');
    });
})();
