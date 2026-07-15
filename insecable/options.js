'use strict';

var DEFAULT = { mode: 'narrow', quotes: true, spacing: true, symbols: true, dashes: true };
var KEYS = ['quotes', 'spacing', 'symbols', 'dashes'];

function load() {
  chrome.storage.sync.get('settings', function (d) {
    var s = Object.assign({}, DEFAULT, (d && d.settings) || {});
    var radio = document.querySelector('input[name=mode][value="' + s.mode + '"]');
    if (radio) radio.checked = true;
    KEYS.forEach(function (k) { document.getElementById(k).checked = !!s[k]; });
  });
}

function save() {
  var checked = document.querySelector('input[name=mode]:checked');
  var s = { mode: checked ? checked.value : 'narrow' };
  KEYS.forEach(function (k) { s[k] = document.getElementById(k).checked; });
  chrome.storage.sync.set({ settings: s }, function () {
    var st = document.getElementById('status');
    st.textContent = 'Enregistre';
    setTimeout(function () { st.textContent = ''; }, 1000);
  });
}

document.addEventListener('DOMContentLoaded', function () {
  load();
  document.querySelectorAll('input').forEach(function (el) {
    el.addEventListener('change', save);
  });
});
