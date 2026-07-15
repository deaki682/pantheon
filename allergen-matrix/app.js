'use strict';
var C = window.AllergenCore;
var KEY = 'allergen_matrix_v1';
var state = load() || { name: '', dishes: [{ name: '', allergens: {} }] };
if (/[?&]demo/.test(location.search) && !localStorage.getItem(KEY)) {
  state = { name: 'Corner Bistro', dishes: [
    { name: 'Classic Cheeseburger', allergens: { milk: 'contains', wheat: 'contains', sesame: 'contains', soy: 'may' } },
    { name: 'Pad Thai', allergens: { peanuts: 'contains', eggs: 'contains', fish: 'contains', shellfish: 'may', soy: 'contains' } },
    { name: 'Garden Salad (no dressing)', allergens: {}, confirmedNone: true },
    { name: 'Grilled Salmon', allergens: { fish: 'contains', treenuts: 'may' } }
  ] };
}
var CYCLE = { '': 'contains', 'contains': 'may', 'may': '' };

var rn = document.getElementById('rname');
rn.value = state.name || '';
rn.addEventListener('input', function () { state.name = rn.value; });

function render() {
  var host = document.getElementById('dishes');
  host.innerHTML = '';
  state.dishes.forEach(function (d, i) {
    d.allergens = d.allergens || {};
    var el = document.createElement('div');
    el.className = 'dish';
    var toggles = C.ALLERGENS.map(function (a) {
      var st = d.allergens[a.key] || '';
      var sym = st === 'contains' ? '● ' : st === 'may' ? '○ ' : '';
      return '<button data-s="' + st + '" onclick="cyc(' + i + ',\'' + a.key + '\')">' + sym + a.label + '</button>';
    }).join('');
    el.innerHTML =
      '<div class="top"><input type="text" placeholder="Item name" value="' + esc(d.name) + '" oninput="nm(' + i + ',this.value)">' +
      '<button class="x" title="Remove" onclick="del(' + i + ')">✕</button></div>' +
      '<div class="tog">' + toggles + '</div>' +
      '<label class="none"><input type="checkbox" ' + (d.confirmedNone ? 'checked' : '') + ' onchange="cn(' + i + ',this.checked)"> Confirmed: no major allergens</label>';
    host.appendChild(el);
  });
  validate();
}
window.cyc = function (i, key) { var a = state.dishes[i].allergens; a[key] = CYCLE[a[key] || '']; render(); };
window.nm = function (i, v) { state.dishes[i].name = v; validate(); };
window.cn = function (i, v) { state.dishes[i].confirmedNone = v; validate(); };
window.del = function (i) { state.dishes.splice(i, 1); if (!state.dishes.length) state.dishes.push({ name: '', allergens: {} }); render(); };
window.addDish = function () { state.dishes.push({ name: '', allergens: {} }); render(); };

function validate() {
  var w = C.validate(state.dishes);
  var el = document.getElementById('valid');
  if (!w.length) { el.innerHTML = '<div class="ok">✓ Ready to print.</div>'; return; }
  el.innerHTML = '<div class="warn"><strong>Check these before printing:</strong><ul>' +
    w.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
}

window.printMatrix = function () {
  save();
  var m = C.buildMatrix(state.dishes.filter(function (d) { return d.name && d.name.trim(); }));
  var head = '<tr><th class="n" style="text-align:left">Menu item</th>' +
    m.allergens.map(function (a) { return '<th class="rot">' + esc(a.label) + '</th>'; }).join('') + '</tr>';
  var body = m.rows.map(function (r) {
    return '<tr><td class="n">' + esc(r.name) + '</td>' + r.cells.map(function (c) {
      var cls = c.status === 'contains' ? 'con' : c.status === 'may' ? 'may' : '';
      return '<td class="' + cls + '">' + c.symbol + '</td>';
    }).join('') + '</tr>';
  }).join('');
  document.getElementById('print').innerHTML =
    '<h2>Allergen Information</h2><p class="sub">' + esc(state.name || '') + '</p>' +
    '<table>' + head + body + '</table>' +
    '<p class="legend">' + esc(C.LEGEND) + '</p>' +
    '<p class="note">' + esc(C.STANDARD_NOTE) + '</p>';
  window.print();
};

window.printCards = function () {
  save();
  var rows = state.dishes.filter(function (d) { return d.name && d.name.trim(); }).map(function (d) {
    return '<tr><td class="n" style="text-align:left">' + esc(d.name) + '</td><td style="text-align:left">' + esc(C.dishSummary(d)) + '</td></tr>';
  }).join('');
  document.getElementById('print').innerHTML =
    '<h2>Allergen Information — by item</h2><p class="sub">' + esc(state.name || '') + '</p>' +
    '<table>' + rows + '</table>' +
    '<p class="note">' + esc(C.STANDARD_NOTE) + '</p>';
  window.print();
};

function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
function load() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } }
window.save = save;
window.reset = function () { if (confirm('Clear all menu items?')) { localStorage.removeItem(KEY); location.reload(); } };
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
render();
