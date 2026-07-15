/* node core.test.js — Subcue engine tests. Quality is the whole thesis, so this is thorough. */
'use strict';
var C = require('./core.js');
var pass = 0, fail = 0;
function ok(cond, msg) { if (cond) pass++; else { fail++; console.error('FAIL: ' + msg); } }
function eq(a, b, msg) { ok(JSON.stringify(a) === JSON.stringify(b), msg + '  (got ' + JSON.stringify(a) + ', want ' + JSON.stringify(b) + ')'); }

// ---- timestamps -----------------------------------------------------------
eq(C.parseTime('00:00:01,000'), 1000, 'SRT comma ms');
eq(C.parseTime('00:00:01.500'), 1500, 'dot ms');
eq(C.parseTime('01:02:03,400'), 3723400, 'full HMS');
eq(C.parseTime('1:02:03.4'), 3723400, '1-digit hour, 1-digit frac -> 400ms');
eq(C.parseTime('02:03.250'), 123250, 'MM:SS.mmm, no hours');
eq(C.parseTime('00:00:05'), 5000, 'no ms');
eq(C.parseTime('nonsense'), null, 'garbage -> null');
eq(C.formatTime(1000, ','), '00:00:01,000', 'format SRT');
eq(C.formatTime(3723400, '.'), '01:02:03.400', 'format VTT dot');
eq(C.formatTime(-50, ','), '00:00:00,000', 'negative clamps to 0');
eq(C.formatTimeSBV(3723400), '1:02:03.400', 'SBV non-padded hour');
// roundtrip
eq(C.formatTime(C.parseTime('01:23:45,678'), ','), '01:23:45,678', 'time roundtrip');

// ---- detection ------------------------------------------------------------
eq(C.detectFormat('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nhi'), 'vtt', 'detect vtt');
eq(C.detectFormat('1\n00:00:01,000 --> 00:00:02,000\nhi'), 'srt', 'detect srt');
eq(C.detectFormat('0:00:01.000,0:00:02.000\nhi'), 'sbv', 'detect sbv');
eq(C.detectFormat('just text'), null, 'detect none');

// ---- SRT parsing ----------------------------------------------------------
var srt = '1\n00:00:01,000 --> 00:00:02,000\nHello\n\n2\n00:00:03,000 --> 00:00:04,500\nWorld\nsecond line\n';
var p = C.parse(srt);
eq(p.format, 'srt', 'parse: format srt');
eq(p.cues.length, 2, 'parse: 2 cues');
eq(p.cues[0], { start: 1000, end: 2000, text: 'Hello', id: '', settings: '' }, 'cue 0');
eq(p.cues[1].text, 'World\nsecond line', 'cue 1 multiline');

// tolerant: BOM + CRLF + missing index + extra blank lines + dot-ms in SRT
var messy = '﻿00:00:01.000 --> 00:00:02.000\r\nNo index here\r\n\r\n\r\n2\r\n00:00:03,000 --> 00:00:04,000\r\nSecond\r\n';
var pm = C.parse(messy, 'srt');
eq(pm.cues.length, 2, 'tolerant: 2 cues from messy input');
eq(pm.cues[0].start, 1000, 'tolerant: BOM+CRLF+dot-ms parsed');
eq(pm.cues[0].text, 'No index here', 'tolerant: index-less cue text');

// ---- VTT parsing ----------------------------------------------------------
var vtt = 'WEBVTT\nKind: captions\nLanguage: en\n\nNOTE this is a note\n\nintro\n00:00:01.000 --> 00:00:02.000 line:80%\nHi there\n\n00:01:02.500 --> 00:01:04.000\nLater\n';
var pv = C.parse(vtt);
eq(pv.format, 'vtt', 'vtt format');
eq(pv.cues.length, 2, 'vtt: header + NOTE skipped, 2 cues');
eq(pv.cues[0].id, 'intro', 'vtt: identifier kept');
eq(pv.cues[0].settings, 'line:80%', 'vtt: cue settings captured');
eq(pv.cues[1].start, 62500, 'vtt: second cue timing');

// ---- SBV parsing ----------------------------------------------------------
var sbv = '0:00:01.000,0:00:02.000\nHello\n\n0:00:03.000,0:00:04.000\nWorld\n';
var ps = C.parse(sbv);
eq(ps.format, 'sbv', 'sbv format');
eq(ps.cues.length, 2, 'sbv: 2 cues');
eq(ps.cues[1].text, 'World', 'sbv: text');

// ---- serialization + roundtrip -------------------------------------------
var cues = C.parse(srt).cues;
ok(C.toSRT(cues).indexOf('00:00:01,000 --> 00:00:02,000') >= 0, 'toSRT timing');
ok(C.toVTT(cues).indexOf('WEBVTT') === 0, 'toVTT header first');
ok(C.toVTT(cues).indexOf('00:00:01.000 --> 00:00:02.000') >= 0, 'toVTT dot timing');
// SRT -> VTT -> SRT preserves timing & text
var back = C.parse(C.toVTT(cues), 'vtt').cues;
eq(back.map(function (c) { return [c.start, c.end, c.text]; }),
   cues.map(function (c) { return [c.start, c.end, c.text]; }), 'SRT->VTT->parse roundtrip');
// renumbering: toSRT always reindexes 1..n
var reidx = C.toSRT([{ start: 0, end: 1000, text: 'a', id: '', settings: '' }, { start: 1000, end: 2000, text: 'b', id: '', settings: '' }]);
ok(/^1\n/.test(reidx) && reidx.indexOf('\n2\n') >= 0, 'toSRT renumbers');

// ---- transforms -----------------------------------------------------------
var t = [{ start: 1000, end: 2000, text: 'a', id: '', settings: '' }, { start: 5000, end: 6000, text: 'b', id: '', settings: '' }];
eq(C.shift(t, 500).map(function (c) { return c.start; }), [1500, 5500], 'shift +500');
eq(C.shift(t, -2000).map(function (c) { return c.start; }), [0, 3000], 'shift negative clamps first to 0');
eq(C.shift(t, 1000, { from: 4000 }).map(function (c) { return c.start; }), [1000, 6000], 'ranged shift only affects >=from');
eq(C.scale(t, 2, 0).map(function (c) { return [c.start, c.end]; }), [[2000, 4000], [10000, 12000]], 'scale x2');

// anchor sync: cue at 1000 should be 2000, cue at 5000 should be 10000
var synced = C.syncByAnchors(t, 1000, 2000, 5000, 10000);
eq(synced[0].start, 2000, 'anchor sync point A');
eq(synced[1].start, 10000, 'anchor sync point B');

// framerate: 25 -> 23.976 slows down (factor 25/23.976 > 1)
var fps = C.scale(t, 25 / 23.976, 0);
ok(fps[0].start > 1000, 'fps convert stretches');

// ---- overlap + duration repair -------------------------------------------
var ov = [{ start: 0, end: 3000, text: 'a', id: '', settings: '' }, { start: 2000, end: 4000, text: 'b', id: '', settings: '' }];
var fixed = C.fixOverlaps(ov, 40);
eq(fixed[0].end, 1960, 'fixOverlaps pulls end back leaving 40ms gap');
ok(fixed[1].start === 2000, 'fixOverlaps leaves next cue start');
var dur = C.fixDurations([{ start: 0, end: 200, text: 'x', id: '', settings: '' }], { minMs: 700 });
eq(dur[0].end, 700, 'fixDurations extends to min');
var durMax = C.fixDurations([{ start: 0, end: 99999, text: 'x', id: '', settings: '' }], { maxMs: 6000 });
eq(durMax[0].end, 6000, 'fixDurations clamps to max');

// ---- cleanup --------------------------------------------------------------
var tagged = [{ start: 0, end: 1000, text: '<i>Hello</i>  {\\an8}there', id: '', settings: '' }];
eq(C.stripTags(tagged)[0].text, 'Hello there', 'stripTags removes html + ass + double space');
eq(C.removeEmpty([{ start: 0, end: 1, text: '  ', id: '', settings: '' }, { start: 1, end: 2, text: 'x', id: '', settings: '' }]).length, 1, 'removeEmpty');

// ---- sort -----------------------------------------------------------------
eq(C.sort([{ start: 5000, end: 6000, text: 'b', id: '', settings: '' }, { start: 1000, end: 2000, text: 'a', id: '', settings: '' }]).map(function (c) { return c.text; }), ['a', 'b'], 'sort by start');

// ---- analyze --------------------------------------------------------------
var bad = [
  { start: 1000, end: 900, text: 'inverted', id: '', settings: '' },
  { start: 2000, end: 2100, text: 'This is a very long single line that clearly exceeds the reading speed limit for its short duration', id: '', settings: '' },
  { start: 3000, end: 5000, text: '', id: '', settings: '' },
  { start: 6000, end: 7000, text: 'ok', id: '', settings: '' },
  { start: 6500, end: 8000, text: 'overlaps prev', id: '', settings: '' }
];
var issues = C.analyze(bad);
function has(type) { return issues.some(function (x) { return x.type === type; }); }
ok(has('nonpositive'), 'analyze: inverted duration');
ok(has('fast'), 'analyze: too-fast cps');
ok(has('long'), 'analyze: long line');
ok(has('empty'), 'analyze: empty cue');
ok(has('overlap'), 'analyze: overlap');
eq(C.analyze([{ start: 0, end: 2000, text: 'clean short line', id: '', settings: '' }]).length, 0, 'analyze: clean cue has no issues');

// ---- stats ----------------------------------------------------------------
eq(C.stats(t), { count: 2, first: 1000, last: 6000, duration: 5000 }, 'stats');

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
