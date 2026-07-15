/*
 * Extension Sentinel — core logic
 * -------------------------------
 * Pure, dependency-free. Runs in the extension popup and under Node (tests).
 *
 * Scores each installed extension by the risk its permissions carry, and diffs against
 * the last snapshot to catch the thing that actually bites users: a trusted extension
 * that quietly GAINS scary permissions after an ownership change / update ("turned evil").
 * 100% local — it only reads what chrome.management already exposes; nothing leaves the machine.
 */
(function (root) {
  'use strict';

  // permission -> { weight, why }
  var RISK = {
    debugger:            { w: 6, why: 'Can inspect and control other pages via the debugger — very powerful.' },
    proxy:               { w: 5, why: 'Can route all your traffic through a proxy.' },
    webRequest:          { w: 4, why: 'Can observe your network requests.' },
    webRequestBlocking:  { w: 5, why: 'Can intercept and modify your network requests.' },
    nativeMessaging:     { w: 4, why: 'Can talk to programs installed on your computer.' },
    management:          { w: 4, why: 'Can enable/disable or uninstall your other extensions.' },
    cookies:             { w: 3, why: 'Can read and write your cookies (including login sessions).' },
    history:             { w: 3, why: 'Can read your browsing history.' },
    clipboardRead:       { w: 3, why: 'Can read your clipboard.' },
    declarativeNetRequestFeedback: { w: 3, why: 'Can see which requests its network rules matched.' },
    scripting:           { w: 2, why: 'Can inject scripts into pages.' },
    declarativeNetRequest: { w: 2, why: 'Can block or modify requests by rule.' },
    downloads:           { w: 2, why: 'Can manage your downloads.' },
    tabs:                { w: 2, why: 'Can read the URL/title of your tabs.' },
    bookmarks:           { w: 1, why: 'Can read/change bookmarks.' },
    geolocation:         { w: 2, why: 'Can access your location.' },
    privacy:             { w: 2, why: 'Can change your browser privacy settings.' }
  };

  var BROAD_HOSTS = ['<all_urls>', '*://*/*', 'http://*/*', 'https://*/*', 'file:///*'];

  function isBroadHost(h) {
    if (!h) return false;
    if (BROAD_HOSTS.indexOf(h) >= 0) return true;
    // e.g. "https://*/*" already covered; also treat "*://*/..." wildcards as broad
    return /^[a-z*]+:\/\/\*\//i.test(h);
  }

  function levelFor(score) { return score >= 6 ? 'high' : score >= 3 ? 'medium' : 'low'; }

  // ext: { permissions:[], hostPermissions:[] (or hostPermissions folded in) }
  function scoreExtension(ext) {
    ext = ext || {};
    var perms = ext.permissions || [];
    var hosts = ext.hostPermissions || [];
    var reasons = [], score = 0;

    var broad = hosts.filter(isBroadHost);
    if (broad.length) { score += 5; reasons.push({ w: 5, text: 'Can read and change data on ALL websites (' + broad.join(', ') + ').' }); }
    else if (hosts.length > 8) { score += 2; reasons.push({ w: 2, text: 'Has access to many specific sites (' + hosts.length + ').' }); }

    perms.forEach(function (p) {
      var r = RISK[p];
      if (r) { score += r.w; reasons.push({ w: r.w, text: r.why }); }
    });

    reasons.sort(function (a, b) { return b.w - a.w; });
    return { score: score, level: levelFor(score), reasons: reasons };
  }

  // Minimal record we persist between checks.
  function snapshot(exts) {
    return (exts || []).map(function (e) {
      return {
        id: e.id, name: e.name, version: e.version,
        permissions: (e.permissions || []).slice().sort(),
        hostPermissions: (e.hostPermissions || []).slice().sort()
      };
    });
  }

  function toMap(snap) {
    var m = {};
    (snap || []).forEach(function (s) { m[s.id] = s; });
    return m;
  }

  function diffMinus(a, b) { // items in a not in b
    var set = {}; (b || []).forEach(function (x) { set[x] = 1; });
    return (a || []).filter(function (x) { return !set[x]; });
  }

  // Compare last snapshot to current: new installs + permission creep on updates.
  function diffSnapshots(prev, curr) {
    var pm = toMap(prev), cm = toMap(curr);
    var added = [], removed = [], creep = [];
    curr.forEach(function (c) {
      var p = pm[c.id];
      if (!p) { added.push({ id: c.id, name: c.name }); return; }
      var newPerms = diffMinus(c.permissions, p.permissions);
      var newHosts = diffMinus(c.hostPermissions, p.hostPermissions);
      if (newPerms.length || newHosts.length) {
        creep.push({ id: c.id, name: c.name, version: c.version, newPermissions: newPerms, newHosts: newHosts });
      }
    });
    (prev || []).forEach(function (p) { if (!cm[p.id]) removed.push({ id: p.id, name: p.name }); });
    return { added: added, removed: removed, creep: creep };
  }

  var api = {
    RISK: RISK, isBroadHost: isBroadHost, levelFor: levelFor,
    scoreExtension: scoreExtension, snapshot: snapshot, diffSnapshots: diffSnapshots
  };
  root.SentinelCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
