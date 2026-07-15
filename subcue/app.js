'use strict';
var C = window.SubcueCore;
var L = window.SubcueLicense;
var LIC_KEY = 'subcue_license_v1';
var MAX_PREVIEW = 300;

var file = null;          // the loaded File object (kept for re-read on encoding change)
var orig = null;          // { format, cues } as loaded
var cues = [];            // current working cues
var outFormat = 'srt';    // export format
var pro = false;

// ---- Pro / license --------------------------------------------------------
(function initPro() {
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(LIC_KEY)); } catch (e) {}
  if (saved && saved.key && L) {
    L.verify(saved.key).then(function (r) {
      if (r.valid) { pro = true; applyPro(); }
      else { try { localStorage.removeItem(LIC_KEY); } catch (e) {} }
    });
  }
})();
function applyPro() {
  document.body.classList.toggle('is-pro', pro);
  var b = document.getElementById('proBadge'); if (b) b.textContent = pro ? '★ Pro' : '';
  var u = document.getElementById('unlockBtn'); if (u) u.style.display = pro ? 'none' : '';
}
function requirePro() { if (pro) return true; openUnlock(); return false; }

// ---- file loading ---------------------------------------------------------
var drop = document.getElementById('drop');
var fileInput = document.getElementById('file');
drop.addEventListener('click', function () { fileInput.click(); });
fileInput.addEventListener('change', function () { if (fileInput.files[0]) loadFile(fileInput.files[0]); });
['dragenter', 'dragover'].forEach(function (ev) {
  drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('hot'); });
});
['dragleave', 'drop'].forEach(function (ev) {
  drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('hot'); });
});
drop.addEventListener('drop', function (e) {
  var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) loadFile(f);
});
document.getElementById('enc').addEventListener('change', function () { if (file) loadFile(file); });

function loadFile(f) {
  file = f;
  var enc = document.getElementById('enc').value;
  var rd = new FileReader();
  rd.onload = function () {
    var text = String(rd.result || '');
    orig = C.parse(text);
    cues = orig.cues.map(function (c) { return { start: c.start, end: c.end, text: c.text, id: c.id, settings: c.settings }; });
    outFormat = orig.format || 'srt';
    setFmtButtons();
    if (!cues.length) {
      status('No cues found. Is this a subtitle file? Try a different encoding.');
    }
    showAll();
    rescan();
    renderPreview();
    renderFileInfo();
    status(cues.length + ' cues loaded from ' + f.name + '.');
  };
  rd.onerror = function () { status('Could not read that file.'); };
  try { rd.readAsText(f, enc); } catch (e) { rd.readAsText(f); }
}

function showAll() {
  ['issuesCard', 'opsCard', 'prevCard'].forEach(function (id) { document.getElementById(id).style.display = ''; });
  document.getElementById('dlBtn').disabled = false;
  document.getElementById('rescanBtn').disabled = false;
}

function renderFileInfo() {
  var el = document.getElementById('fileinfo');
  el.style.display = '';
  var s = C.stats(cues);
  el.innerHTML =
    '<span class="pill">' + esc(file ? file.name : '') + '</span>' +
    '<span class="pill fmt">detected: ' + esc((orig && orig.format ? orig.format : '?').toUpperCase()) + '</span>' +
    '<span class="pill">' + cues.length + ' cues</span>' +
    '<span class="pill">' + fmtDur(s.duration) + '</span>';
}
function fmtDur(ms) {
  if (!ms) return '0:00';
  var t = Math.round(ms / 1000), h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
  return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0');
}

// ---- issues ---------------------------------------------------------------
function rescan() {
  if (!orig) return;
  var issues = C.analyze(cues);
  var sum = document.getElementById('issuesSummary');
  var list = document.getElementById('ilist');
  if (!issues.length) {
    sum.innerHTML = '<span class="none">✓ No timing or formatting problems found.</span>';
    list.innerHTML = '';
    return;
  }
  var byType = {};
  issues.forEach(function (x) { byType[x.type] = (byType[x.type] || 0) + 1; });
  sum.innerHTML = '<b>' + issues.length + ' issue' + (issues.length > 1 ? 's' : '') + ':</b> ' +
    Object.keys(byType).map(function (t) { return byType[t] + ' ' + t; }).join(' · ');
  list.innerHTML = issues.slice(0, 400).map(function (x) {
    return '<div class="it"><span class="badge ' + x.type + '">' + x.type + '</span><span>' + esc(x.msg) + '</span></div>';
  }).join('');
}

// ---- preview --------------------------------------------------------------
function renderPreview() {
  var body = document.getElementById('prevBody');
  var shown = cues.slice(0, MAX_PREVIEW);
  body.innerHTML = shown.map(function (c, i) {
    return '<tr><td class="t">' + (i + 1) + '</td><td class="t">' + C.formatTime(c.start, ',') +
      '</td><td class="t">' + C.formatTime(c.end, ',') + '</td><td class="txt">' + esc(c.text || '') + '</td></tr>';
  }).join('');
  document.getElementById('prevNote').textContent =
    cues.length > MAX_PREVIEW ? ('Showing first ' + MAX_PREVIEW + ' of ' + cues.length + ' cues (all are exported).') : (cues.length + ' cues.');
}

// ---- format selector ------------------------------------------------------
var fmtSeg = document.getElementById('fmtSeg');
fmtSeg.addEventListener('click', function (e) {
  var btn = e.target.closest('button'); if (!btn) return;
  outFormat = btn.getAttribute('data-f'); setFmtButtons();
});
function setFmtButtons() {
  Array.prototype.forEach.call(fmtSeg.querySelectorAll('button'), function (b) {
    b.classList.toggle('on', b.getAttribute('data-f') === outFormat);
  });
}

// ---- FPS presets ----------------------------------------------------------
(function () {
  var sel = document.getElementById('fps');
  C.FPS_PRESETS.forEach(function (p, i) {
    var o = document.createElement('option'); o.value = i; o.textContent = p.label; sel.appendChild(o);
  });
})();

// ---- operations (free) ----------------------------------------------------
function apply(newCues, msg) { cues = newCues; renderPreview(); rescan(); renderFileInfo(); status(msg); }
function needFile() { if (!orig) { status('Load a file first.'); return false; } return true; }

window.doShift = function () {
  if (!needFile()) return;
  var v = parseFloat(document.getElementById('shiftVal').value) || 0;
  var unit = parseFloat(document.getElementById('shiftUnit').value) || 1;
  var ms = Math.round(v * unit);
  apply(C.shift(cues, ms), 'Shifted all cues by ' + (ms >= 0 ? '+' : '') + ms + ' ms.');
};
window.doSort = function () { if (needFile()) apply(C.sort(cues), 'Sorted cues by start time.'); };
window.doRemoveEmpty = function () {
  if (!needFile()) return;
  var n = cues.length; var out = C.removeEmpty(cues);
  apply(out, 'Removed ' + (n - out.length) + ' empty cue(s).');
};

// ---- operations (Pro) -----------------------------------------------------
function parseFlexTime(s) {
  s = String(s || '').trim(); if (!s) return null;
  if (s.indexOf(':') >= 0) return C.parseTime(s);
  var f = parseFloat(s.replace(',', '.')); return isNaN(f) ? null : Math.round(f * 1000);
}
window.doSync = function () {
  if (!needFile() || !requirePro()) return;
  var aOld = parseFlexTime(document.getElementById('a_old').value);
  var aNew = parseFlexTime(document.getElementById('a_new').value);
  var bOld = parseFlexTime(document.getElementById('b_old').value);
  var bNew = parseFlexTime(document.getElementById('b_new').value);
  if (aOld == null || aNew == null || bOld == null || bNew == null) { status('Enter all four sync times (e.g. 00:01:00,000 or 60).'); return; }
  if (aOld === bOld) { status('Point A and B must be at different original times.'); return; }
  apply(C.syncByAnchors(cues, aOld, aNew, bOld, bNew), 'Re-synced to the two anchor points.');
};
window.doFps = function () {
  if (!needFile() || !requirePro()) return;
  var p = C.FPS_PRESETS[parseInt(document.getElementById('fps').value, 10) || 0];
  apply(C.scale(cues, p.from / p.to, 0), 'Converted timing ' + p.label + '.');
};
window.doAutofix = function () {
  if (!needFile() || !requirePro()) return;
  var out = C.sort(cues);
  out = C.fixDurations(out, { minMs: 700 });
  out = C.fixOverlaps(out, 40);
  apply(out, 'Auto-fixed: sorted, min duration 700 ms, overlaps resolved with a 40 ms gap.');
};
window.doStrip = function () {
  if (!needFile() || !requirePro()) return;
  apply(C.stripTags(cues), 'Stripped formatting tags.');
};
window.resetFile = function () {
  if (!orig) return;
  cues = orig.cues.map(function (c) { return { start: c.start, end: c.end, text: c.text, id: c.id, settings: c.settings }; });
  renderPreview(); rescan(); renderFileInfo(); status('Reset to the loaded file.');
};

// ---- download -------------------------------------------------------------
window.doDownload = function () {
  if (!needFile()) return;
  var text = C.serialize(cues, outFormat, { keepIds: true, keepSettings: true });
  var base = (file ? file.name : 'subtitles').replace(/\.[^.]+$/, '');
  var name = base + '.' + outFormat;
  var mime = outFormat === 'vtt' ? 'text/vtt' : 'text/plain';
  var blob = new Blob([text], { type: mime + ';charset=utf-8' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click();
  setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 100);
  status('Downloaded ' + name + '.');
};

// ---- unlock ---------------------------------------------------------------
window.openUnlock = function () { document.getElementById('unlockModal').style.display = 'flex'; document.getElementById('licInput').focus(); };
window.closeUnlock = function () { document.getElementById('unlockModal').style.display = 'none'; document.getElementById('licMsg').textContent = ''; };
window.doUnlock = function () {
  var raw = document.getElementById('licInput').value;
  var msg = document.getElementById('licMsg'); msg.className = 'lic-msg'; msg.textContent = 'Checking…';
  if (!L) { msg.textContent = 'Verifier not loaded.'; return; }
  L.verify(raw).then(function (r) {
    if (r.valid) {
      try { localStorage.setItem(LIC_KEY, JSON.stringify({ key: raw.trim(), serial: r.serial })); } catch (e) {}
      pro = true; applyPro();
      msg.className = 'lic-msg ok'; msg.textContent = '✓ Pro unlocked. Thank you!';
      setTimeout(closeUnlock, 900);
    } else {
      msg.className = 'lic-msg err';
      msg.textContent = '✗ ' + (r.reason || 'That key did not verify.') + ' Check for a copy/paste slip.';
    }
  });
};

// ---- util -----------------------------------------------------------------
function status(s) { document.getElementById('statusline').textContent = s; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }

setFmtButtons();
applyPro();

// ---- demo (for screenshots / try-before-load): ?demo loads a messy sample ----
if (/[?&]demo/.test(location.search)) {
  var sample =
    '1\n00:00:01,000 --> 00:00:02,000\n<i>Previously...</i>\n\n' +
    '2\n00:00:02,500 --> 00:00:02,700\nWait — this reads far too fast for two hundred milliseconds of screen time here.\n\n' +
    '3\n00:00:04,000 --> 00:00:08,000\nThe deal was simple.\n\n' +
    '4\n00:00:07,500 --> 00:00:10,000\n{\\an8}We never agreed to that.\n\n' +
    '5\n00:00:12,000 --> 00:00:12,300\nGo.\n';
  orig = C.parse(sample);
  cues = orig.cues.map(function (c) { return { start: c.start, end: c.end, text: c.text, id: c.id, settings: c.settings }; });
  outFormat = orig.format; setFmtButtons();
  file = { name: 'episode-04.srt' };
  if (/[?&]fixed/.test(location.search)) {
    // Run the same pipeline the Pro "Auto-fix" + "Strip tags" buttons use — proves it end to end.
    var out = C.sort(cues);
    out = C.fixDurations(out, { minMs: 700 });
    out = C.fixOverlaps(out, 40);
    cues = C.stripTags(out);
  }
  showAll(); rescan(); renderPreview(); renderFileInfo();
  status(cues.length + ' cues loaded from episode-04.srt.');
}
