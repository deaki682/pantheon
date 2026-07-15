'use strict';
var C = window.FuneralCore;
var KEY = 'funeral_price_list_v1';
var state = load() || { home: {}, items: {}, altc: '', caskets: [], containers: [] };
if (/[?&]demo/.test(location.search) && !localStorage.getItem(KEY)) {
  state = {
    home: { name: 'Riverside Funeral Home', phone: '(555) 240-1180', address: '412 Elm Street, Springfield', license: 'FD-40921', date: 'January 1, 2026' },
    items: {
      basic_services: { price: 2495 }, embalming: { price: 895 }, other_prep: { price: 350 },
      facilities_viewing: { price: 550 }, facilities_ceremony: { price: 695 }, facilities_memorial: { price: 495 },
      facilities_graveside: { price: 395 }, hearse: { price: 375 }, limousine: { price: 325 },
      forwarding: { price: 1995 }, receiving: { price: 1795 }, direct_cremation: { price: 1795 },
      immediate_burial: { price: 2195 }, caskets: { note: 'Priced individually — see Casket Price List' },
      outer_containers: { note: 'Priced individually — see Outer Burial Container Price List' }
    },
    altc: 'fiberboard, unfinished wood, pressed wood',
    caskets: [{ name: '20-Gauge Steel, Blue', description: 'Non-gasketed, crepe interior', price: 1895 }, { name: 'Solid Oak', description: 'Satin finish, velvet interior', price: 3495 }],
    containers: [{ name: 'Concrete Grave Liner', description: 'Meets standard cemetery requirement', price: 895 }, { name: 'Sealed Burial Vault', description: 'Reinforced concrete', price: 1695 }]
  };
}

// ---- build the GPL item inputs ----
var gplEl = document.getElementById('gpl');
C.GPL_CATEGORIES.forEach(function (cat) {
  var it = state.items[cat.key] || {};
  var row = document.createElement('div');
  row.className = 'row';
  row.innerHTML =
    '<div><label>' + (cat.required ? '• ' : '') + cat.label + '</label>' +
    '<input type="text" placeholder="note (optional)" data-k="' + cat.key + '" data-f="note" value="' + esc(it.note || '') + '"></div>' +
    '<div><label>Price</label><input type="number" step="0.01" data-k="' + cat.key + '" data-f="price" value="' + (it.price != null ? it.price : '') + '"></div>';
  gplEl.appendChild(row);
});
document.getElementById('altc').value = state.altc || '';

// ---- home fields ----
['name', 'phone', 'address', 'license', 'date'].forEach(function (f) {
  var el = document.getElementById('h_' + f);
  el.value = state.home[f] || '';
  el.addEventListener('input', function () { state.home[f] = el.value; validate(); });
});
document.getElementById('altc').addEventListener('input', function (e) { state.altc = e.target.value; });

// ---- delegated input handling for GPL + dynamic rows ----
document.addEventListener('input', function (e) {
  var t = e.target;
  if (t.dataset.k) {
    state.items[t.dataset.k] = state.items[t.dataset.k] || {};
    state.items[t.dataset.k][t.dataset.f] = t.value;
    validate();
  }
});

// ---- dynamic casket / container rows ----
function renderRows(kind) {
  var host = document.getElementById(kind);
  host.innerHTML = '';
  (state[kind] || []).forEach(function (r, i) {
    var div = document.createElement('div');
    div.className = 'dyn-row';
    div.innerHTML =
      '<input type="text" placeholder="Name" value="' + esc(r.name || '') + '" oninput="upd(\'' + kind + '\',' + i + ',\'name\',this.value)">' +
      '<input type="text" placeholder="Description" value="' + esc(r.description || '') + '" oninput="upd(\'' + kind + '\',' + i + ',\'description\',this.value)">' +
      '<input type="number" step="0.01" placeholder="Price" value="' + (r.price != null ? r.price : '') + '" oninput="upd(\'' + kind + '\',' + i + ',\'price\',this.value)">' +
      '<button class="x" onclick="delRow(\'' + kind + '\',' + i + ')">✕</button>';
    host.appendChild(div);
  });
}
window.addRow = function (kind) { state[kind] = state[kind] || []; state[kind].push({}); renderRows(kind); };
window.delRow = function (kind, i) { state[kind].splice(i, 1); renderRows(kind); };
window.upd = function (kind, i, f, v) { state[kind][i][f] = v; };
renderRows('caskets'); renderRows('containers');

// ---- validation ----
function validate() {
  var w = C.validateGPL(state.items);
  var el = document.getElementById('valid');
  if (!w.length) { el.innerHTML = '<div class="ok">✓ All required Funeral Rule items are present.</div>'; return; }
  el.innerHTML = '<div class="warn"><strong>' + w.length + ' required item(s) still needed:</strong><ul>' +
    w.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
}
validate();

// ---- printing ----
function docFoot(home) {
  return '<div class="foot">' + esc(home.name || '') +
    (home.address ? ' · ' + esc(home.address) : '') +
    (home.phone ? ' · ' + esc(home.phone) : '') +
    (home.license ? ' · Lic. ' + esc(home.license) : '') +
    '<br>Prices effective ' + esc(home.date || '[date]') +
    '. These prices are subject to change without notice.</div>';
}
window.printDoc = function (which) {
  save();
  var home = state.home, html = '';
  if (which === 'gpl') {
    var g = C.buildGPL(home, state.items, { alternativeContainers: state.altc, effectiveDate: home.date });
    html = '<h2>General Price List</h2><p class="sub">' + esc(home.name || '') + '</p>';
    html += '<div class="d">' + esc(g.itemizationNotice) + '</div>';
    html += '<table>';
    g.lines.forEach(function (l) {
      html += '<tr><td>' + esc(l.label) + (l.note ? '<br><small>' + esc(l.note) + '</small>' : '') +
        (l.disclosure ? '<div class="d">' + esc(l.disclosure) + '</div>' : '') +
        '</td><td class="p">' + (l.price || (l.note ? '' : '$______')) + '</td></tr>';
    });
    html += '</table>';
    html += '<div class="d">' + esc(g.alternativeContainerDisclosure) + '</div>';
  } else if (which === 'cpl') {
    html = renderList('Casket Price List', home, state.caskets, C.DISCLOSURES.casketList);
  } else if (which === 'obcpl') {
    html = renderList('Outer Burial Container Price List', home, state.containers, C.DISCLOSURES.outerContainerList);
  }
  html += docFoot(home);
  var p = document.getElementById('print');
  p.innerHTML = html;
  window.print();
};
function renderList(title, home, rows, disclosure) {
  var out = '<h2>' + esc(title) + '</h2><p class="sub">' + esc(home.name || '') + '</p>';
  out += '<div class="d">' + esc(disclosure) + '</div><table>';
  (rows || []).forEach(function (r) {
    out += '<tr><td>' + esc(r.name || '') + (r.description ? '<br><small>' + esc(r.description) + '</small>' : '') +
      '</td><td class="p">' + (r.price != null && r.price !== '' ? C.money(r.price) : '$______') + '</td></tr>';
  });
  if (!(rows || []).length) out += '<tr><td colspan="2"><small>No items entered.</small></td></tr>';
  out += '</table>';
  return out;
}

// ---- persistence ----
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
function load() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } }
window.save = save;
window.reset = function () { if (confirm('Clear all entered data?')) { localStorage.removeItem(KEY); location.reload(); } };
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
