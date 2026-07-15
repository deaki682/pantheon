// background.js — the entire service worker. One job: when the toolbar icon is
// clicked, open the tool in a full browser tab (better than a cramped popup for
// dragging in many files). Opening the extension's own page needs no permission.
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: chrome.runtime.getURL('tool.html') });
});
