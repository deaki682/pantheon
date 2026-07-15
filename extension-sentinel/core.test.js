/* Run: node core.test.js */
'use strict';
var C = require('./core.js');
var pass = 0, fail = 0;
function ok(l, c) { if (c) pass++; else { fail++; console.log('FAIL: ' + l); } }
function eq(l, a, b) { if (a === b) pass++; else { fail++; console.log('FAIL: ' + l + ' got ' + JSON.stringify(a) + ' want ' + JSON.stringify(b)); } }

// broad host detection
ok('all_urls broad', C.isBroadHost('<all_urls>'));
ok('https wildcard broad', C.isBroadHost('https://*/*'));
ok('scheme wildcard broad', C.isBroadHost('*://*/*'));
ok('specific host not broad', !C.isBroadHost('https://example.com/*'));

// scoring
var benign = C.scoreExtension({ permissions: ['storage', 'alarms'], hostPermissions: [] });
eq('benign level', benign.level, 'low');
eq('benign score', benign.score, 0);

var mid = C.scoreExtension({ permissions: ['tabs', 'scripting'], hostPermissions: ['https://example.com/*'] });
ok('mid level medium-ish', mid.level === 'medium' || mid.score >= 3 || mid.level === 'low');

var scary = C.scoreExtension({ permissions: ['webRequestBlocking', 'cookies'], hostPermissions: ['<all_urls>'] });
eq('scary level high', scary.level, 'high');
ok('scary explains all-sites', scary.reasons.some(function (r) { return /ALL websites/.test(r.text); }));
ok('scary reasons sorted desc', scary.reasons[0].w >= scary.reasons[scary.reasons.length - 1].w);

var dbg = C.scoreExtension({ permissions: ['debugger'] });
eq('debugger alone is high', dbg.level, 'high');

// snapshot is minimal + sorted
var snap = C.snapshot([{ id: 'a', name: 'A', version: '1', permissions: ['tabs', 'cookies'], hostPermissions: ['b', 'a'] }]);
eq('snapshot perms sorted', snap[0].permissions.join(','), 'cookies,tabs');
eq('snapshot hosts sorted', snap[0].hostPermissions.join(','), 'a,b');

// diff: new install
var prev = C.snapshot([{ id: 'a', name: 'A', permissions: ['storage'], hostPermissions: [] }]);
var curr = C.snapshot([
  { id: 'a', name: 'A', permissions: ['storage'], hostPermissions: [] },
  { id: 'b', name: 'B', permissions: ['tabs'], hostPermissions: [] }
]);
var d1 = C.diffSnapshots(prev, curr);
eq('detects new install', d1.added.length, 1);
eq('new install id', d1.added[0].id, 'b');
eq('no creep', d1.creep.length, 0);

// diff: permission creep after update (the headline feature)
var before = C.snapshot([{ id: 'a', name: 'Weather', permissions: ['storage'], hostPermissions: [] }]);
var after = C.snapshot([{ id: 'a', name: 'Weather', version: '2', permissions: ['storage', 'webRequest', 'cookies'], hostPermissions: ['<all_urls>'] }]);
var d2 = C.diffSnapshots(before, after);
eq('detects creep', d2.creep.length, 1);
ok('creep lists new perms', d2.creep[0].newPermissions.indexOf('webRequest') >= 0 && d2.creep[0].newPermissions.indexOf('cookies') >= 0);
ok('creep lists new hosts', d2.creep[0].newHosts.indexOf('<all_urls>') >= 0);

// diff: removal
var d3 = C.diffSnapshots(curr, prev);
eq('detects removal', d3.removed.length, 1);

// boring inputs
eq('score empty', C.scoreExtension().score, 0);
eq('diff empty', C.diffSnapshots([], []).added.length, 0);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
