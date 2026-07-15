/*
 * Subcue — subtitle engine (core logic)
 * -------------------------------------
 * Pure, dependency-free. Runs in the browser (<script>) and under Node (tests).
 * Everything works on an internal, format-agnostic cue model so transforms never
 * care whether the file was SRT, VTT, or SBV:
 *
 *   cue = { start: <ms int>, end: <ms int>, text: "<lines\njoined>", id: "", settings: "" }
 *
 * Parses SRT / WebVTT / SBV (tolerant of BOM, CRLF, missing indices, dot-vs-comma
 * milliseconds, hour-less timestamps, NOTE/STYLE/REGION blocks). Serializes back to
 * any of the three. Transforms: shift, scale, 2-point anchor sync, overlap repair,
 * duration clamping, tag stripping, cleanup. analyze() is the linter that powers the
 * "load a broken file, see exactly what's wrong" verification.
 */
(function (root) {
  'use strict';

  // ---- timestamps ---------------------------------------------------------
  function pad(n, w) { n = String(n); while (n.length < w) n = '0' + n; return n; }
  function frac(f) { return f ? parseInt((f + '000').slice(0, 3), 10) : 0; }

  // Accepts "HH:MM:SS,mmm", "HH:MM:SS.mmm", "H:MM:SS.mmm", "MM:SS.mmm", "MM:SS".
  // Returns integer milliseconds, or null if it isn't a timestamp.
  function parseTime(s) {
    if (s == null) return null;
    s = String(s).trim().replace(',', '.');
    var m = s.match(/^(\d+):(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$/);
    if (m) return (((+m[1]) * 60 + (+m[2])) * 60 + (+m[3])) * 1000 + frac(m[4]);
    m = s.match(/^(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$/); // MM:SS(.mmm), no hours
    if (m) return ((+m[1]) * 60 + (+m[2])) * 1000 + frac(m[3]);
    return null;
  }

  // ms -> "HH:MM:SS<sep>mmm". sep is ',' for SRT, '.' for VTT.
  function formatTime(ms, sep) {
    sep = sep || ',';
    ms = Math.round(ms); if (ms < 0) ms = 0;
    var h = Math.floor(ms / 3600000); ms -= h * 3600000;
    var mi = Math.floor(ms / 60000); ms -= mi * 60000;
    var se = Math.floor(ms / 1000); ms -= se * 1000;
    return pad(h, 2) + ':' + pad(mi, 2) + ':' + pad(se, 2) + sep + pad(ms, 3);
  }
  // SBV uses a non-padded hour and a dot: "H:MM:SS.mmm".
  function formatTimeSBV(ms) {
    ms = Math.round(ms); if (ms < 0) ms = 0;
    var h = Math.floor(ms / 3600000); ms -= h * 3600000;
    var mi = Math.floor(ms / 60000); ms -= mi * 60000;
    var se = Math.floor(ms / 1000); ms -= se * 1000;
    return h + ':' + pad(mi, 2) + ':' + pad(se, 2) + '.' + pad(ms, 3);
  }

  // ---- normalization + detection -----------------------------------------
  function normalize(text) {
    return String(text == null ? '' : text)
      .replace(/^\uFEFF/, '')  // strip UTF-8 BOM
      .replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  }

  function detectFormat(text) {
    var t = normalize(text).replace(/^\s+/, '');
    if (/^WEBVTT/.test(t)) return 'vtt';
    // SBV: "H:MM:SS.mmm,H:MM:SS.mmm" on one line, no "-->"
    if (/^\d{1,2}:\d{2}:\d{2}\.\d{1,3},\d{1,2}:\d{2}:\d{2}\.\d{1,3}/m.test(t) && !/-->/.test(t)) return 'sbv';
    if (/-->/.test(t)) return 'srt';
    return null;
  }

  // ---- parsing ------------------------------------------------------------
  function parseCueTiming(line) {
    var idx = line.indexOf('-->');
    if (idx < 0) return null;
    var left = line.slice(0, idx).trim();
    var rightAll = line.slice(idx + 3).trim().split(/\s+/);
    var endStr = rightAll.shift();
    var settings = rightAll.join(' ');
    var start = parseTime(left), end = parseTime(endStr);
    if (start == null || end == null) return null;
    return { start: start, end: end, settings: settings };
  }

  // Shared SRT/VTT block parser. Skips VTT header/NOTE/STYLE/REGION blocks,
  // tolerates optional numeric index (SRT) or cue identifier (VTT).
  function parseBlocks(text) {
    text = normalize(text);
    var cues = [];
    text.split(/\n{2,}/).forEach(function (block) {
      var lines = block.split('\n');
      while (lines.length && lines[0].trim() === '') lines.shift();
      while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
      if (!lines.length) return;
      if (/^WEBVTT/.test(lines[0]) || /^NOTE\b/.test(lines[0]) ||
          /^STYLE\b/.test(lines[0]) || /^REGION\b/.test(lines[0])) return;

      var timing = null, id = '', i = 0;
      if (lines[0].indexOf('-->') >= 0) {
        timing = parseCueTiming(lines[0]); i = 1;
      } else if (lines[1] != null && lines[1].indexOf('-->') >= 0) {
        var first = lines[0].trim();
        if (!/^\d+$/.test(first)) id = first; // keep non-numeric VTT identifiers
        timing = parseCueTiming(lines[1]); i = 2;
      } else {
        return; // no timing line -> not a cue
      }
      if (!timing) return;
      cues.push({ start: timing.start, end: timing.end, text: lines.slice(i).join('\n'), id: id, settings: timing.settings || '' });
    });
    return cues;
  }

  function parseSBV(text) {
    text = normalize(text);
    var cues = [];
    text.split(/\n{2,}/).forEach(function (block) {
      var lines = block.split('\n');
      while (lines.length && lines[0].trim() === '') lines.shift();
      while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
      if (!lines.length) return;
      var parts = lines[0].split(',');
      if (parts.length < 2) return;
      var start = parseTime(parts[0]), end = parseTime(parts[1]);
      if (start == null || end == null) return;
      cues.push({ start: start, end: end, text: lines.slice(1).join('\n'), id: '', settings: '' });
    });
    return cues;
  }

  function parse(text, hint) {
    var fmt = hint || detectFormat(text) || 'srt';
    var cues = (fmt === 'sbv') ? parseSBV(text) : parseBlocks(text);
    return { format: fmt, cues: cues };
  }

  // ---- serialization ------------------------------------------------------
  function toSRT(cues) {
    return cues.map(function (c, i) {
      return (i + 1) + '\n' + formatTime(c.start, ',') + ' --> ' + formatTime(c.end, ',') + '\n' + (c.text || '');
    }).join('\n\n') + '\n';
  }
  function toVTT(cues, opts) {
    opts = opts || {};
    var body = cues.map(function (c) {
      var head = (opts.keepIds && c.id) ? c.id + '\n' : '';
      var settings = (opts.keepSettings && c.settings) ? ' ' + c.settings : '';
      return head + formatTime(c.start, '.') + ' --> ' + formatTime(c.end, '.') + settings + '\n' + (c.text || '');
    }).join('\n\n');
    return 'WEBVTT\n\n' + body + '\n';
  }
  function toSBV(cues) {
    return cues.map(function (c) {
      return formatTimeSBV(c.start) + ',' + formatTimeSBV(c.end) + '\n' + (c.text || '');
    }).join('\n\n') + '\n';
  }
  function serialize(cues, format, opts) {
    if (format === 'vtt') return toVTT(cues, opts);
    if (format === 'sbv') return toSBV(cues);
    return toSRT(cues);
  }

  // ---- helpers ------------------------------------------------------------
  function clone(c) { return { start: c.start, end: c.end, text: c.text, id: c.id, settings: c.settings }; }
  function byStart(a, b) { return a.start - b.start || a.end - b.end; }
  function sort(cues) { return cues.map(clone).sort(byStart); }

  // ---- transforms ---------------------------------------------------------
  // Add a fixed offset (ms, may be negative) to every cue, or only those whose
  // start falls within [range.from, range.to].
  function shift(cues, deltaMs, range) {
    range = range || {};
    return cues.map(function (c) {
      if (range.from != null && c.start < range.from) return clone(c);
      if (range.to != null && c.start > range.to) return clone(c);
      var o = clone(c);
      o.start = Math.max(0, c.start + deltaMs);
      o.end = Math.max(0, c.end + deltaMs);
      return o;
    });
  }

  // Linear remap: t' = round(t*factor + offset). Framerate fixes and stretches.
  function scale(cues, factor, offsetMs) {
    offsetMs = offsetMs || 0;
    return cues.map(function (c) {
      var o = clone(c);
      o.start = Math.max(0, Math.round(c.start * factor + offsetMs));
      o.end = Math.max(0, Math.round(c.end * factor + offsetMs));
      return o;
    });
  }

  // Two-point sync: you know cue-time oldA should land at newA and oldB at newB.
  // Solves the linear map through both points — fixes drift AND offset at once.
  function syncByAnchors(cues, oldA, newA, oldB, newB) {
    if (oldB === oldA) return cues.map(clone);
    var factor = (newB - newA) / (oldB - oldA);
    var offset = newA - factor * oldA;
    return scale(cues, factor, offset);
  }

  // Common framerate conversions (source fps / target fps).
  var FPS_PRESETS = [
    { from: 23.976, to: 25, label: '23.976 → 25 fps' },
    { from: 25, to: 23.976, label: '25 → 23.976 fps' },
    { from: 23.976, to: 24, label: '23.976 → 24 fps' },
    { from: 24, to: 23.976, label: '24 → 23.976 fps' },
    { from: 24, to: 25, label: '24 → 25 fps' },
    { from: 25, to: 24, label: '25 → 24 fps' },
    { from: 29.97, to: 25, label: '29.97 → 25 fps' },
    { from: 25, to: 29.97, label: '25 → 29.97 fps' }
  ];

  // Clamp overlaps: when a cue runs into the next, pull its end back, leaving minGap.
  function fixOverlaps(cues, minGap) {
    minGap = minGap == null ? 0 : minGap;
    var out = sort(cues);
    for (var i = 0; i < out.length - 1; i++) {
      var limit = out[i + 1].start - minGap;
      if (out[i].end > limit) out[i].end = Math.max(out[i].start, limit);
    }
    return out;
  }

  // Enforce min/max on-screen duration.
  function fixDurations(cues, opts) {
    opts = opts || {};
    var minMs = opts.minMs || 0, maxMs = opts.maxMs || Infinity;
    return cues.map(function (c) {
      var o = clone(c), d = c.end - c.start;
      if (d < minMs) o.end = c.start + minMs;
      if (o.end - o.start > maxMs) o.end = o.start + maxMs;
      return o;
    });
  }

  // Strip HTML-ish tags (<i>, <font>), ASS overrides ({\an8}), collapse whitespace.
  function stripTags(cues) {
    return cues.map(function (c) {
      var o = clone(c);
      o.text = (c.text || '')
        .replace(/<\/?[^>]+>/g, '')
        .replace(/\{[^}]*\}/g, '')
        .split('\n').map(function (l) { return l.replace(/[ \t]{2,}/g, ' ').trim(); }).join('\n')
        .replace(/\n{2,}/g, '\n').trim();
      return o;
    });
  }

  function removeEmpty(cues) {
    return cues.filter(function (c) { return (c.text || '').trim() !== ''; }).map(clone);
  }

  // ---- analysis (the linter) ---------------------------------------------
  function cps(c) {
    var len = (c.text || '').replace(/\n/g, '').replace(/<\/?[^>]+>/g, '').length;
    var sec = (c.end - c.start) / 1000;
    return sec > 0 ? len / sec : Infinity;
  }

  function analyze(cues, opts) {
    opts = opts || {};
    var maxCps = opts.maxCps || 21, minMs = opts.minMs || 700,
        maxLineLen = opts.maxLineLen || 42, maxLines = opts.maxLines || 2;
    var issues = [];
    function push(i, type, msg) { issues.push({ i: i, type: type, msg: msg }); }
    cues.forEach(function (c, i) {
      var n = i + 1;
      if (c.end <= c.start) { push(i, 'nonpositive', 'Cue ' + n + ' has zero or negative duration.'); }
      else {
        if (c.end - c.start < minMs) push(i, 'short', 'Cue ' + n + ' is very short (' + (c.end - c.start) + ' ms).');
        if (cps(c) > maxCps) push(i, 'fast', 'Cue ' + n + ' reads too fast (' + Math.round(cps(c)) + ' cps).');
      }
      if (!(c.text || '').trim()) push(i, 'empty', 'Cue ' + n + ' is empty.');
      var lines = (c.text || '').split('\n');
      if (lines.length > maxLines) push(i, 'lines', 'Cue ' + n + ' has ' + lines.length + ' lines.');
      lines.forEach(function (l) {
        if (l.length > maxLineLen) push(i, 'long', 'Cue ' + n + ' has a long line (' + l.length + ' chars).');
      });
    });
    for (var j = 0; j < cues.length - 1; j++) {
      if (cues[j].start > cues[j + 1].start) push(j, 'order', 'Cue ' + (j + 1) + ' starts after cue ' + (j + 2) + '.');
      else if (cues[j].end > cues[j + 1].start) push(j, 'overlap', 'Cue ' + (j + 1) + ' overlaps cue ' + (j + 2) + '.');
    }
    return issues;
  }

  function stats(cues) {
    if (!cues.length) return { count: 0, duration: 0, first: 0, last: 0 };
    var s = sort(cues);
    return { count: cues.length, first: s[0].start, last: s[s.length - 1].end, duration: s[s.length - 1].end - s[0].start };
  }

  var api = {
    parseTime: parseTime, formatTime: formatTime, formatTimeSBV: formatTimeSBV,
    normalize: normalize, detectFormat: detectFormat,
    parse: parse, serialize: serialize, toSRT: toSRT, toVTT: toVTT, toSBV: toSBV,
    sort: sort, shift: shift, scale: scale, syncByAnchors: syncByAnchors, FPS_PRESETS: FPS_PRESETS,
    fixOverlaps: fixOverlaps, fixDurations: fixDurations, stripTags: stripTags, removeEmpty: removeEmpty,
    cps: cps, analyze: analyze, stats: stats
  };
  root.SubcueCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
