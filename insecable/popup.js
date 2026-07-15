'use strict';

var input = document.getElementById('in');
var output = document.getElementById('out');
var fixBtn = document.getElementById('fix');
var copyBtn = document.getElementById('copy');
var modeLabel = document.getElementById('mode');
var settings = null;

chrome.storage.sync.get('settings', function (d) {
  settings = (d && d.settings) || null;
  var compat = settings && settings.mode === 'compat';
  modeLabel.textContent = 'Mode : ' + (compat ? 'compatibilite (U+00A0)' : 'fine (U+202F)');
});

function doFix() {
  output.value = InsecableEngine.fixText(input.value, settings || undefined);
  copyBtn.disabled = output.value.length === 0;
}

fixBtn.addEventListener('click', doFix);
input.addEventListener('input', doFix); // live preview — the 10-second demo

copyBtn.addEventListener('click', function () {
  navigator.clipboard.writeText(output.value).then(function () {
    copyBtn.textContent = 'Copie';
    setTimeout(function () { copyBtn.textContent = 'Copier'; }, 1200);
  }).catch(function () {});
});

document.getElementById('opts').addEventListener('click', function (e) {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});
