'use strict';
var C = window.SentinelCore;
var SNAP_KEY = 'sentinel_snapshot_v1';

function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }

function fail(msg) {
  document.getElementById('list').innerHTML = '<div class="empty">' + esc(msg) + '</div>';
}

if (!(typeof chrome !== 'undefined' && chrome.management && chrome.management.getAll)) {
  fail('This page must run as an installed extension (chrome.management unavailable here).');
} else {
  chrome.management.getAll(function (all) {
    var exts = (all || []).filter(function (e) {
      return e.type === 'extension' && e.id !== chrome.runtime.id;
    });
    // normalize + score
    var scored = exts.map(function (e) {
      var s = C.scoreExtension({ permissions: e.permissions, hostPermissions: e.hostPermissions });
      return { e: e, s: s };
    }).sort(function (a, b) { return b.s.score - a.s.score; });

    renderChanges(exts);
    renderList(scored);
    document.getElementById('foot').textContent =
      exts.length + ' extensions checked · ' +
      scored.filter(function (x) { return x.s.level === 'high'; }).length + ' high-risk. ' +
      'Re-open after any update to catch new permissions.';
  });
}

function renderChanges(exts) {
  var curr = C.snapshot(exts.map(function (e) {
    return { id: e.id, name: e.name, version: e.version, permissions: e.permissions, hostPermissions: e.hostPermissions };
  }));
  chrome.storage.local.get(SNAP_KEY, function (data) {
    var prev = data && data[SNAP_KEY];
    if (prev) {
      var d = C.diffSnapshots(prev, curr);
      var html = '';
      if (d.creep.length) {
        html += '<div class="alert"><h2>⚠ Gained permissions since your last check</h2>' +
          d.creep.map(function (c) {
            var extra = (c.newPermissions.concat(c.newHosts)).join(', ');
            return '<div class="item"><b>' + esc(c.name) + '</b> now also wants: ' + esc(extra) + '</div>';
          }).join('') + '</div>';
      }
      if (d.added.length) {
        html += '<div class="alert"><h2>New since last check</h2>' +
          d.added.map(function (a) { return '<div class="item">' + esc(a.name) + '</div>'; }).join('') + '</div>';
      }
      document.getElementById('alerts').innerHTML = html;
    }
    // save the fresh snapshot for next time
    var obj = {}; obj[SNAP_KEY] = curr;
    chrome.storage.local.set(obj);
  });
}

function renderList(scored) {
  var list = document.getElementById('list');
  list.innerHTML = '';
  scored.forEach(function (x) {
    var li = document.createElement('li');
    li.className = 'ext';
    var reasons = x.s.reasons.length
      ? '<ul class="why">' + x.s.reasons.map(function (r) { return '<li>' + esc(r.text) + '</li>'; }).join('') + '</ul>'
      : '<div class="why">Only benign permissions. Low risk.</div>';
    li.innerHTML =
      '<div class="row"><span class="badge ' + x.s.level + '">' + x.s.level + '</span>' +
      '<span class="nm">' + esc(x.e.name) + '</span>' +
      (x.e.enabled ? '' : '<span class="badge low">off</span>') + '</div>' +
      '<div class="why-wrap" style="display:none">' + reasons + '</div>';
    var wrap = li.querySelector('.why-wrap');
    li.querySelector('.row').addEventListener('click', function () {
      wrap.style.display = wrap.style.display === 'none' ? 'block' : 'none';
    });
    // high-risk expanded by default
    if (x.s.level === 'high') wrap.style.display = 'block';
    list.appendChild(li);
  });
}
