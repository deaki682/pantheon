'use strict';
var C = window.AllergenCore;
var L = window.AllergenLicense;
var KEY = 'allergen_matrix_v1';
var LIC_KEY = 'allergen_matrix_license_v1';
var MENUS_KEY = 'allergen_matrix_menus_v1';

var state = load() || { name: '', dishes: [{ name: '', allergens: {} }], brand: {} };
if (!state.brand) state.brand = {};
if (/[?&]demo/.test(location.search) && !localStorage.getItem(KEY)) {
  state = { name: 'Corner Bistro', brand: {}, dishes: [
    { name: 'Classic Cheeseburger', allergens: { milk: 'contains', wheat: 'contains', sesame: 'contains', soy: 'may' } },
    { name: 'Pad Thai', allergens: { peanuts: 'contains', eggs: 'contains', fish: 'contains', shellfish: 'may', soy: 'contains' } },
    { name: 'Garden Salad (no dressing)', allergens: {}, confirmedNone: true },
    { name: 'Grilled Salmon', allergens: { fish: 'contains', treenuts: 'may' } }
  ] };
}
var CYCLE = { '': 'contains', 'contains': 'may', 'may': '' };

// ---- Pro / license state --------------------------------------------------
var pro = false;
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
  var badge = document.getElementById('proBadge');
  if (badge) badge.textContent = pro ? '★ Pro unlocked' : '';
  var btn = document.getElementById('unlockBtn');
  if (btn) btn.style.display = pro ? 'none' : '';
  renderBrand();
  renderMenus();
}

// ---- restaurant name ------------------------------------------------------
var rn = document.getElementById('rname');
rn.value = state.name || '';
rn.addEventListener('input', function () { state.name = rn.value; });

// ---- dishes ---------------------------------------------------------------
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

// ---- branding (Pro) -------------------------------------------------------
function renderBrand() {
  var foot = document.getElementById('brandFoot');
  if (foot) foot.value = (state.brand && state.brand.footer) || '';
  var logoPrev = document.getElementById('logoPrev');
  if (logoPrev) {
    if (state.brand && state.brand.logo) { logoPrev.src = state.brand.logo; logoPrev.style.display = ''; }
    else logoPrev.style.display = 'none';
  }
}
window.setFooter = function (v) { state.brand.footer = v; };
window.clearLogo = function () { state.brand.logo = ''; renderBrand(); };
window.onLogo = function (input) {
  var f = input.files && input.files[0];
  if (!f) return;
  if (f.size > 512 * 1024) { alert('Please use a logo under 512 KB.'); return; }
  var rd = new FileReader();
  rd.onload = function () { state.brand.logo = rd.result; renderBrand(); };
  rd.readAsDataURL(f);
};

function brandHeaderHtml() {
  if (!pro || !state.brand) return '';
  var logo = state.brand.logo ? '<img class="blogo" src="' + state.brand.logo + '" alt="">' : '';
  return logo;
}
function brandFooterHtml() {
  if (!pro || !state.brand || !state.brand.footer) return '';
  return '<p class="brandfoot">' + esc(state.brand.footer) + '</p>';
}

// ---- saved menus (Pro) ----------------------------------------------------
function loadMenus() { try { return JSON.parse(localStorage.getItem(MENUS_KEY)) || {}; } catch (e) { return {}; } }
function saveMenus(m) { try { localStorage.setItem(MENUS_KEY, JSON.stringify(m)); } catch (e) {} }

function renderMenus() {
  var host = document.getElementById('menuList');
  if (!host) return;
  var menus = loadMenus();
  var ids = Object.keys(menus);
  if (!ids.length) { host.innerHTML = '<small>No saved menus yet. Save the current menu to reuse it later.</small>'; return; }
  host.innerHTML = ids.map(function (id) {
    var m = menus[id];
    return '<div class="menu-row"><span class="mnm">' + esc(m.name || '(unnamed)') + '</span>' +
      '<span class="mdate">' + esc(m.savedAt || '') + '</span>' +
      '<button class="sec sm" onclick="loadMenu(\'' + id + '\')">Load</button>' +
      '<button class="x" title="Delete" onclick="delMenu(\'' + id + '\')">✕</button></div>';
  }).join('');
}
window.saveMenuAs = function () {
  if (!requirePro()) return;
  var nm = prompt('Save this menu as:', state.name || 'My menu');
  if (nm == null) return;
  var menus = loadMenus();
  var id = 'm' + (Date.now ? Date.now() : (new Date()).getTime());
  var d = new Date();
  var stamp = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  menus[id] = { name: nm, savedAt: stamp, data: JSON.parse(JSON.stringify(state)) };
  saveMenus(menus);
  renderMenus();
};
window.loadMenu = function (id) {
  var menus = loadMenus();
  var m = menus[id];
  if (!m) return;
  state = JSON.parse(JSON.stringify(m.data));
  if (!state.brand) state.brand = {};
  rn.value = state.name || '';
  save(); render(); renderBrand();
};
window.delMenu = function (id) {
  var menus = loadMenus();
  delete menus[id];
  saveMenus(menus);
  renderMenus();
};

// ---- printing -------------------------------------------------------------
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
    brandHeaderHtml() +
    '<h2>Allergen Information</h2><p class="sub">' + esc(state.name || '') + '</p>' +
    '<table>' + head + body + '</table>' +
    '<p class="legend">' + esc(C.LEGEND) + '</p>' +
    '<p class="note">' + esc(C.STANDARD_NOTE) + '</p>' +
    brandFooterHtml();
  window.print();
};

window.printCards = function () {
  if (!requirePro()) return;
  save();
  var rows = state.dishes.filter(function (d) { return d.name && d.name.trim(); }).map(function (d) {
    return '<div class="card-item"><div class="ci-name">' + esc(d.name) + '</div>' +
      '<div class="ci-sum">' + esc(C.dishSummary(d)) + '</div></div>';
  }).join('');
  document.getElementById('print').innerHTML =
    brandHeaderHtml() +
    '<h2>Allergen Information — by item</h2><p class="sub">' + esc(state.name || '') + '</p>' +
    '<div class="cards">' + rows + '</div>' +
    '<p class="note">' + esc(C.STANDARD_NOTE) + '</p>' +
    brandFooterHtml();
  window.print();
};

// ---- unlock flow ----------------------------------------------------------
function requirePro() {
  if (pro) return true;
  openUnlock();
  return false;
}
window.openUnlock = function () { document.getElementById('unlockModal').style.display = 'flex'; document.getElementById('licInput').focus(); };
window.closeUnlock = function () { document.getElementById('unlockModal').style.display = 'none'; document.getElementById('licMsg').textContent = ''; };
window.doUnlock = function () {
  var raw = document.getElementById('licInput').value;
  var msg = document.getElementById('licMsg');
  msg.className = 'lic-msg';
  msg.textContent = 'Checking…';
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

// ---- persistence ----------------------------------------------------------
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
function load() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } }
window.save = save;
window.reset = function () { if (confirm('Clear all menu items? (Saved menus and your Pro unlock are kept.)')) { localStorage.removeItem(KEY); location.reload(); } };
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }

render();
applyPro();
