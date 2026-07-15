/* Run: node core.test.js */
'use strict';
var C = require('./core.js');
var pass = 0, fail = 0;
function ok(label, cond) { if (cond) pass++; else { fail++; console.log('FAIL: ' + label); } }
function eq(label, a, b) { if (a === b) pass++; else { fail++; console.log('FAIL: ' + label + '  got ' + JSON.stringify(a) + '  want ' + JSON.stringify(b)); } }

// money formatting
eq('money basic', C.money(1234.5), '$1,234.50');
eq('money zero', C.money(0), '$0.00');
eq('money bad', C.money('x'), '');

// disclosures present and non-empty
['itemization', 'basicServicesFee', 'embalming', 'alternativeContainer', 'casketList'].forEach(function (k) {
  ok('disclosure ' + k + ' present', typeof C.DISCLOSURES[k] === 'string' && C.DISCLOSURES[k].length > 40);
});

// GPL builds every category and carries the itemization notice
var gpl = C.buildGPL(
  { name: 'Test Home', address: '1 Main St', phone: '555' },
  { basic_services: { price: 2500 }, embalming: { price: 895 }, caskets: { note: 'See casket price list' } },
  { alternativeContainers: 'fiberboard, unfinished wood', effectiveDate: '2026-01-01' }
);
eq('GPL has all categories', gpl.lines.length, C.GPL_CATEGORIES.length);
ok('GPL itemization notice present', gpl.itemizationNotice.indexOf('only the items you desire') >= 0);
ok('GPL basic services priced', gpl.lines.find(function (l) { return l.key === 'basic_services'; }).price === '$2,500.00');
ok('GPL alt-container disclosure names containers', gpl.alternativeContainerDisclosure.indexOf('fiberboard') >= 0);
ok('GPL basic_services carries fee disclosure', gpl.lines.find(function (l) { return l.key === 'basic_services'; }).disclosure.indexOf('basic services and overhead') >= 0);

// validation flags missing required items
var warnings = C.validateGPL({ basic_services: { price: 2500 } });
ok('validation flags missing required items', warnings.length > 5);
ok('validation names embalming', warnings.some(function (w) { return w.indexOf('Embalming') >= 0; }));
var noWarnIfNote = C.validateGPL({ caskets: { note: 'priced individually' } });
ok('a note satisfies a required item', !noWarnIfNote.some(function (w) { return w.indexOf('Caskets') >= 0; }));

// casket price list
var cpl = C.buildPriceList('Casket Price List', { name: 'Test Home' }, [
  { name: 'Oak', description: 'Solid oak', price: 3200 },
  { name: 'Cloth-covered', description: 'Fiberboard', price: 795 }
]);
eq('CPL rows', cpl.rows.length, 2);
eq('CPL price formatted', cpl.rows[0].price, '$3,200.00');

// statement totals
var stmt = C.buildStatement({ name: 'Test Home' }, [
  { label: 'Basic services', price: 2500 },
  { label: 'Embalming', price: 895 },
  { label: 'Hearse', price: 350 }
], { decedent: 'John Doe', date: '2026-07-15' });
eq('statement total', stmt.total, '$3,745.00');
eq('statement raw total', stmt.totalRaw, 3745);
ok('statement legal-requirements note present', stmt.legalRequirementsNote.indexOf('required by law') >= 0);

// empty / boring inputs
ok('buildGPL tolerates empty', C.buildGPL().lines.length === C.GPL_CATEGORIES.length);
ok('buildStatement tolerates empty', C.buildStatement().totalRaw === 0);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
