(function (root) {
  'use strict';

  function dayNumber(value) {
    return Date.parse(value + 'T00:00:00Z') / 86400000;
  }

  function rollingMean(timeline, index, metric, windowDays) {
    var end = dayNumber(timeline[index].date);
    var start = end - (windowDays == null ? 7 : windowDays) + 1;
    var values = timeline.slice(0, index + 1).filter(function (point) {
      var day = dayNumber(point.date);
      return day >= start && day <= end && Number.isFinite(point[metric]);
    }).map(function (point) { return point[metric]; });
    return values.length ? values.reduce(function (sum, value) { return sum + value; }, 0) / values.length : null;
  }

  function condition(point) {
    var prior = point.prior_day_caffeine_cutoff_2pm;
    if (!Number.isFinite(prior)) return 'unknown';
    return prior >= 0.5 ? 'cutoff' : 'usual';
  }

  function calendarFraction(timeline, index) {
    var first = dayNumber(timeline[0].date);
    var span = dayNumber(timeline[timeline.length - 1].date) - first;
    return span > 0 ? (dayNumber(timeline[index].date) - first) / span : 0;
  }

  var api = { rollingMean: rollingMean, condition: condition, calendarFraction: calendarFraction };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LiveForeverChart = api;
}(typeof window === 'object' ? window : this));
