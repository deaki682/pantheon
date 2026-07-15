/* Minimal dependency-free tests. Run: node test/engine.test.js */
'use strict';
var engine = require('../engine.js');
var fix = engine.fixText;
var CH = String.fromCharCode;

var NNBSP = CH(0x202F), NBSP = CH(0x00A0);
var GO = CH(0x00AB), GC = CH(0x00BB), RSQUO = CH(0x2019);
var ELL = CH(0x2026), EM = CH(0x2014), EURO = CH(0x20AC);

var pass = 0, fail = 0;
function eq(label, got, want) {
  if (got === want) { pass++; return; }
  fail++;
  console.log('FAIL: ' + label);
  console.log('  got : ' + JSON.stringify(got) + '  ' + codes(got));
  console.log('  want: ' + JSON.stringify(want) + '  ' + codes(want));
}
function ok(label, cond) { if (cond) { pass++; } else { fail++; console.log('FAIL: ' + label); } }
function codes(s) { return '[' + s.split('').map(function (c) { return c.charCodeAt(0).toString(16); }).join(' ') + ']'; }

// --- core spacing ---
eq('narrow before !', fix('Bonjour!'), 'Bonjour' + NNBSP + '!');
eq('narrow before ?', fix('Ca va?'), 'Ca va' + NNBSP + '?');
eq('narrow before ;', fix('un ; deux'), 'un' + NNBSP + '; deux');
eq('full NBSP before :', fix('Note: ici'), 'Note' + NBSP + ': ici');
eq('collapse existing space before !', fix('Bonjour !'), 'Bonjour' + NNBSP + '!');
eq('compat mode uses NBSP before !', fix('Bonjour!', { mode: 'compat' }), 'Bonjour' + NBSP + '!');

// --- guillemets ---
eq('straight quotes to guillemets', fix('"Bonjour"'), GO + NNBSP + 'Bonjour' + NNBSP + GC);
eq('repair loose guillemets', fix('« mot »'), GO + NNBSP + 'mot' + NNBSP + GC);

// --- apostrophe / dashes ---
eq('apostrophe elision', fix("l'eau"), 'l' + RSQUO + 'eau');
eq('ellipsis', fix('attends...'), 'attends' + ELL);
eq('leave four dots', fix('attends....'), 'attends....');
eq('double hyphen to em dash', fix('a--b'), 'a' + EM + 'b');
eq('keep single hyphen', fix('arc-en-ciel'), 'arc-en-ciel');

// --- symbols ---
eq('percent', fix('20%'), '20' + NBSP + '%');
eq('euro', fix('12,50€'), '12,50' + NBSP + EURO);
eq('time h', fix('14h30'), '14' + NBSP + 'h' + NBSP + '30');

// --- safety: masking ---
ok('URL untouched', fix('voir http://a.com/b?x=1&y=2 ok').indexOf('http://a.com/b?x=1&y=2') >= 0);
ok('email untouched', fix('ecris a jean@site.fr merci').indexOf('jean@site.fr') >= 0);
ok('time colon untouched', fix('rendez-vous 12:30 pile').indexOf('12:30') >= 0);
ok('ratio untouched', fix('format 16:9 large').indexOf('16:9') >= 0);
ok('emoticon untouched', fix('cool :) vraiment').indexOf(':)') >= 0);
ok('prime/feet untouched', fix('il fait 6\'2" de haut').indexOf('6\'2"') >= 0);
eq('year not grouped', fix('en 2024 et page 1234'), 'en 2024 et page 1234');
ok('decimals kept both forms', fix('3,14 puis 3.14').indexOf('3,14') >= 0 && fix('3,14 puis 3.14').indexOf('3.14') >= 0);

// --- no over-eager spacing ---
ok('no space before leading ?', fix('? oui').charCodeAt(0) === '?'.charCodeAt(0));

// --- idempotency (the headline promise) ---
var samples = [
  'Il dit : "Bonjour !" puis partit... a 14h30 ; c\'etait l\'ete.',
  'Voir http://x.fr?a=1 et 12:30 et 20% -- vraiment ?',
  fix('Il dit : "Bonjour !"'),
  '"Deja" fait :)',
  'Rien a corriger.'
];
samples.forEach(function (s, i) {
  var once = fix(s);
  var twice = fix(once);
  eq('idempotent #' + i, twice, once);
});

// --- toggles ---
eq('spacing off leaves punctuation', fix('Bonjour!', { spacing: false, quotes: false, symbols: false, dashes: false }), 'Bonjour!');
eq('quotes off leaves straight quote', fix('"x"', { quotes: false, spacing: false }), '"x"');

// --- boring inputs ---
eq('empty string', fix(''), '');
ok('non-string returns input', fix(null) === null);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
