/* Run: node core.test.js */
'use strict';
var C = require('./core.js');
var pass = 0, fail = 0;
function ok(l, c) { if (c) pass++; else { fail++; console.log('FAIL: ' + l); } }
function eq(l, a, b) { if (a === b) pass++; else { fail++; console.log('FAIL: ' + l + ' got ' + JSON.stringify(a) + ' want ' + JSON.stringify(b)); } }

// the 9 FDA allergens, sesame included
eq('9 allergens', C.ALLERGENS.length, 9);
ok('sesame present (FASTER Act)', C.ALLERGENS.some(function (a) { return a.key === 'sesame'; }));
ok('shellfish present', C.ALLERGENS.some(function (a) { return a.key === 'shellfish'; }));

// symbols
eq('contains symbol', C.symbol('contains'), '●');
eq('may symbol', C.symbol('may'), '○');
eq('none symbol', C.symbol(''), '');

// matrix shape
var dishes = [
  { name: 'Cheeseburger', allergens: { milk: 'contains', wheat: 'contains', sesame: 'contains', treenuts: 'may' } },
  { name: 'Garden Salad', allergens: {}, confirmedNone: true }
];
var m = C.buildMatrix(dishes);
eq('rows', m.rows.length, 2);
eq('cells per row', m.rows[0].cells.length, 9);
var burger = m.rows[0];
eq('milk contains', burger.cells.find(function (c) { return c.key === 'milk'; }).symbol, '●');
eq('treenuts may', burger.cells.find(function (c) { return c.key === 'treenuts'; }).symbol, '○');
eq('fish blank', burger.cells.find(function (c) { return c.key === 'fish'; }).symbol, '');

// per-item summary
eq('summary', C.dishSummary(dishes[0]), 'Contains: Milk, Wheat, Sesame. May contain: Tree nuts.');
eq('summary none', C.dishSummary({ allergens: {} }), 'No major allergens declared.');

// validation
ok('flags empty menu', C.validate([]).length === 1);
ok('flags unnamed item', C.validate([{ allergens: { milk: 'contains' } }]).some(function (w) { return /no name/.test(w); }));
ok('flags no-allergen-unconfirmed', C.validate([{ name: 'Water', allergens: {} }]).some(function (w) { return /confirm/.test(w); }));
ok('confirmedNone suppresses warning', !C.validate([{ name: 'Water', allergens: {}, confirmedNone: true }]).some(function (w) { return /confirm/.test(w); }));

// boring inputs
ok('buildMatrix tolerates empty', C.buildMatrix().rows.length === 0);
ok('legend + note present', C.LEGEND.length > 10 && C.STANDARD_NOTE.indexOf('cross-contact') >= 0);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
