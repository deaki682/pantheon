/*
 * Insécable — service worker (MV3, ephemeral: no in-memory state).
 * Wires the context-menu item and the keyboard command to an in-page fix.
 * The popup's paste box is the always-works path; this is the convenience path.
 */
'use strict';

var MENU_ID = 'insecable-fix';
var DEFAULT_SETTINGS = { mode: 'narrow', quotes: true, spacing: true, symbols: true, dashes: true };

chrome.runtime.onInstalled.addListener(function () {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: 'Corriger la typographie francaise',
    contexts: ['selection', 'editable']
  });
  chrome.storage.sync.get('settings', function (data) {
    if (!data || !data.settings) chrome.storage.sync.set({ settings: DEFAULT_SETTINGS });
  });
});

chrome.contextMenus.onClicked.addListener(function (info, tab) {
  if (info.menuItemId === MENU_ID && tab && tab.id != null) runFix(tab.id);
});

chrome.commands.onCommand.addListener(function (command) {
  if (command !== 'fix-typography') return;
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (tabs && tabs[0] && tabs[0].id != null) runFix(tabs[0].id);
  });
});

async function runFix(tabId) {
  var settings = DEFAULT_SETTINGS;
  try {
    var data = await chrome.storage.sync.get('settings');
    if (data && data.settings) settings = Object.assign({}, DEFAULT_SETTINGS, data.settings);
  } catch (e) { /* fall back to defaults */ }

  try {
    // 1) load the shared engine into the page's isolated world
    await chrome.scripting.executeScript({ target: { tabId: tabId }, files: ['engine.js'] });
    // 2) run the fix against whatever is focused/selected
    var results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: applyFixInPage,
      args: [settings]
    });
    handleResult(tabId, results && results[0] ? results[0].result : null);
  } catch (e) {
    // Injection is blocked on chrome:// pages, the Web Store, PDF viewer, etc.
    flashBadge('!', '#b91c1c');
  }
}

function handleResult(tabId, r) {
  if (!r) return;
  if (r.ok && r.changed) { flashBadge('OK', '#16a34a'); return; }
  if (r.ok && !r.changed) { flashBadge('=', '#6b7280'); return; }
  // Nothing editable was targeted (e.g. Google Docs canvas). Point to the popup.
  chrome.scripting.executeScript({
    target: { tabId: tabId },
    func: showToastInPage,
    args: ["Insecable : selectionnez du texte dans un champ modifiable, ou collez votre texte dans la fenetre de l'extension."]
  }).catch(function () {});
}

function flashBadge(text, color) {
  try {
    chrome.action.setBadgeText({ text: text });
    chrome.action.setBadgeBackgroundColor({ color: color || '#2563eb' });
    setTimeout(function () { chrome.action.setBadgeText({ text: '' }); }, 1600);
  } catch (e) { /* ignore */ }
}

/* ---- injected into the page (isolated world; must be self-contained) ---- */

function applyFixInPage(settings) {
  var engine = globalThis.InsecableEngine;
  if (!engine) return { ok: false, reason: 'engine' };
  function fix(s) { return engine.fixText(s, settings); }

  var el = document.activeElement;
  var isTextField = el && (el.tagName === 'TEXTAREA' ||
    (el.tagName === 'INPUT' && /^(text|search|url|email|tel|)$/i.test(el.type || 'text')));

  if (isTextField) {
    var val = el.value;
    var start = el.selectionStart, end = el.selectionEnd;
    if (start == null) { start = 0; end = val.length; }
    var hasSel = start !== end;
    var from = hasSel ? start : 0;
    var to = hasSel ? end : val.length;
    var slice = val.slice(from, to);
    var fixed = fix(slice);
    if (fixed === slice) return { ok: true, changed: false };
    el.focus();
    try { el.setSelectionRange(from, to); } catch (e) {}
    var inserted = false;
    try { inserted = document.execCommand('insertText', false, fixed); } catch (e) {}
    if (!inserted) { // execCommand can be a no-op in some engines
      el.value = val.slice(0, from) + fixed + val.slice(to);
      try { el.setSelectionRange(from, from + fixed.length); } catch (e) {}
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return { ok: true, changed: true };
  }

  var sel = window.getSelection ? window.getSelection() : null;
  if (sel && sel.rangeCount > 0 && !sel.isCollapsed) {
    var text = sel.toString();
    var fixed2 = fix(text);
    if (fixed2 === text) return { ok: true, changed: false };
    var okce = false;
    try { okce = document.execCommand('insertText', false, fixed2); } catch (e) {}
    if (!okce) {
      try {
        var range = sel.getRangeAt(0);
        range.deleteContents();
        range.insertNode(document.createTextNode(fixed2));
      } catch (e) { return { ok: false, reason: 'readonly' }; }
    }
    return { ok: true, changed: true };
  }

  return { ok: false, reason: 'no-target' };
}

function showToastInPage(message) {
  try {
    var d = document.createElement('div');
    d.textContent = message;
    d.style.cssText = [
      'position:fixed', 'z-index:2147483647', 'left:50%', 'bottom:24px',
      'transform:translateX(-50%)', 'background:#111827', 'color:#fff',
      'padding:10px 14px', 'border-radius:10px', 'font:13px/1.4 system-ui,sans-serif',
      'box-shadow:0 6px 20px rgba(0,0,0,.3)', 'max-width:80vw'
    ].join(';');
    document.body.appendChild(d);
    setTimeout(function () { d.remove(); }, 4000);
  } catch (e) { /* ignore */ }
}
