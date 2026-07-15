// app.js — the only file that touches the DOM. Loaded as a plain <script> after
// strip.js / exif.js / zip.js, so it uses the shared global `MS`. It wires
// drag-drop to the pure core, renders one card per file, and handles the boring
// failure cases: empty files, non-images, unsupported formats, damaged files,
// and files that were already clean.
(function () {
  'use strict';
  const { stripBytes, detectFormat, SUPPORTED, readMetadataSummary, verifyClean, makeZip } = MS;

  const $ = (id) => document.getElementById(id);
  const dropZone = $('drop');
  const fileInput = $('file');
  const resultsEl = $('results');
  const barEl = $('bar');
  const summaryEl = $('summary');
  const tpl = $('card-tpl');

  const results = [];        // { name, data:Uint8Array|null }
  const objectUrls = [];     // thumbnail URLs to revoke on Clear

  const MIME = { jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' };
  function humanSize(n) {
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
    return (n / 1024 / 1024).toFixed(2) + ' MB';
  }
  function trackUrl(blob) { const u = URL.createObjectURL(blob); objectUrls.push(u); return u; }
  function downloadBlob(blob, name) {
    const u = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = u; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(u), 4000);
  }

  // ---- card scaffolding ----
  function makeCard(name) {
    const node = tpl.content.firstElementChild.cloneNode(true);
    const fn = node.querySelector('.fname');
    fn.textContent = name; fn.title = name;
    resultsEl.appendChild(node);
    return {
      root: node,
      img: node.querySelector('.thumb img'),
      thumb: node.querySelector('.thumb'),
      badge: node.querySelector('.badge'),
      sizes: node.querySelector('.sizes'),
      lead: node.querySelector('.lead'),
      findings: node.querySelector('.findings'),
      actions: node.querySelector('.cardactions'),
      download: node.querySelector('.download'),
    };
  }
  const setBadge = (card, text, kind) => { card.badge.textContent = text; card.badge.className = 'badge ' + kind; };
  const setLead = (card, text, cls) => { card.lead.textContent = text; card.lead.className = 'lead' + (cls ? ' ' + cls : ''); };
  const noImage = (card) => { card.thumb.classList.add('noimg'); card.img.remove(); };
  function setThumb(card, bytes, fmt) {
    card.img.src = trackUrl(new Blob([bytes], { type: MIME[fmt] || 'application/octet-stream' }));
    card.img.onerror = () => noImage(card);
  }
  function renderFindings(card, findings) {
    card.findings.innerHTML = '';
    for (const f of findings) {
      const row = document.createElement('div');
      row.className = 'finding ' + (f.severity || 'low');
      const k = document.createElement('span'); k.className = 'k'; k.textContent = f.label;
      const v = document.createElement('span'); v.className = 'v'; v.textContent = f.value;
      row.append(k, v); card.findings.appendChild(row);
    }
  }
  function renderMessage(card, text, cls) {
    card.findings.innerHTML = '';
    const p = document.createElement('p'); p.className = cls; p.textContent = text;
    card.findings.appendChild(p);
  }
  const wireDownload = (card, name, bytes, fmt) =>
    card.download.addEventListener('click', () => downloadBlob(new Blob([bytes], { type: MIME[fmt] || 'application/octet-stream' }), name));
  const noDownload = (card) => card.actions.remove();

  // ---- canvas fallback: only for a recognised format too malformed to parse
  // losslessly. Re-rasterising discards every metadata block by construction, at
  // the cost of a re-encode. Always surfaced to the user. ----
  async function canvasReencode(bytes, fmt) {
    const bmp = await createImageBitmap(new Blob([bytes], { type: MIME[fmt] }));
    const canvas = document.createElement('canvas');
    canvas.width = bmp.width; canvas.height = bmp.height;
    canvas.getContext('2d').drawImage(bmp, 0, 0);
    if (bmp.close) bmp.close();
    const out = await new Promise((res, rej) =>
      canvas.toBlob((blob) => (blob ? res(blob) : rej(new Error('encode failed'))), MIME[fmt], 0.95));
    return new Uint8Array(await out.arrayBuffer());
  }

  // Prefer the reader's rich findings (GPS coords, camera…); if it surfaced
  // nothing but the stripper still removed segments (e.g. an unknown APPn, a
  // trailer, stale WebP flags), show those so the report is never falsely empty.
  const REMOVED_SEV = { exif: 'high', xmp: 'high', iptc: 'med', thumbnail: 'high', trailer: 'med', comment: 'low', text: 'low', flags: 'low', other: 'low' };
  function reportFrom(summary, removed) {
    if (summary.findings.length) return summary.findings;
    return (removed || []).map((x) => ({ label: x.label, value: x.bytes ? humanSize(x.bytes) + ' removed' : 'removed', severity: REMOVED_SEV[x.kind] || 'low' }));
  }

  // ---- process one file end to end ----
  async function processOne(file) {
    const myGen = generation;
    const card = makeCard(file.name);
    let bytes;
    try {
      bytes = new Uint8Array(await file.arrayBuffer());
    } catch {
      setBadge(card, 'Error', 'danger'); noImage(card); noDownload(card);
      renderMessage(card, 'Could not read this file.', 'errline'); return;
    }
    if (myGen !== generation) { card.root.remove(); return; }   // list was cleared while reading this file
    if (bytes.length === 0) {
      setBadge(card, 'Skipped', 'neutral'); noImage(card); noDownload(card);
      renderMessage(card, 'This file is empty (0 bytes).', 'errline'); return;
    }

    const fmt = detectFormat(bytes);
    const summary = readMetadataSummary(bytes);

    try {
      const r = stripBytes(bytes);
      const v = verifyClean(r.output);
      setThumb(card, r.output, fmt);
      card.sizes.textContent = `${fmt.toUpperCase()} · ${humanSize(bytes.length)} → ${humanSize(r.output.length)}`;

      if (!r.changed && !summary.hasAny && r.output.length === bytes.length) {
        setBadge(card, 'Already safe', 'neutral');
        setLead(card, '', '');
        renderMessage(card, 'Good news — this photo had no hidden data to begin with. It’s safe to share as-is.', 'nometa');
      } else if (v.clean) {
        setBadge(card, '✓ Untraceable', 'ok');
        setLead(card, 'This photo was exposing — now erased:', 'danger');
        renderFindings(card, reportFrom(summary, r.removed));
      } else {
        setBadge(card, 'Cleaned — needs a check', 'warn');
        setLead(card, 'This photo was exposing — now erased:', 'danger');
        renderFindings(card, reportFrom(summary, r.removed));
        const p = document.createElement('p'); p.className = 'errline';
        p.textContent = 'A double-check still detected ' + v.remaining.join(', ') + '. Please report this file.';
        card.findings.appendChild(p);
      }
      wireDownload(card, file.name, r.output, fmt);
      results.push({ name: file.name, data: r.output });
      return;
    } catch (e) {
      if (e.code === 'UNSUPPORTED_FORMAT' || e.code === 'NOT_AN_IMAGE') {
        setBadge(card, 'Skipped', 'neutral'); noImage(card); noDownload(card);
        renderMessage(card, e.message, 'errline'); return;
      }
      if (SUPPORTED.includes(fmt)) {   // recognised format but malformed → safe fallback
        try {
          const out = await canvasReencode(bytes, fmt);
          if (myGen !== generation) { card.root.remove(); return; }
          const v = verifyClean(out);
          setThumb(card, out, fmt);
          card.sizes.textContent = `${fmt.toUpperCase()} · ${humanSize(bytes.length)} → ${humanSize(out.length)} (re-encoded)`;
          setBadge(card, v.clean ? '✓ Untraceable (rebuilt)' : 'Rebuilt — needs a check', 'warn');
          setLead(card, 'This photo was exposing — now erased:', 'danger');
          renderFindings(card, reportFrom(summary, []));
          const note = document.createElement('p'); note.className = 'errline';
          note.textContent = 'This file was damaged, so it was safely rebuilt from scratch instead of edited. The picture may be very slightly recompressed.';
          card.findings.appendChild(note);
          wireDownload(card, file.name, out, fmt);
          results.push({ name: file.name, data: out });
          return;
        } catch {
          setBadge(card, 'Error', 'danger'); noImage(card); noDownload(card);
          renderMessage(card, 'This file looks damaged and could not be processed safely.', 'errline'); return;
        }
      }
      setBadge(card, 'Error', 'danger'); noImage(card); noDownload(card);
      renderMessage(card, e.message || 'Could not process this file.', 'errline');
    }
  }

  // ---- batch orchestration ----
  // Files dropped while a batch is still running are queued, not dropped.
  // `generation` bumps on Clear so an in-flight file abandons instead of
  // repopulating a just-cleared list.
  let busy = false;
  let generation = 0;
  const queue = [];
  async function handleFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    for (const f of files) queue.push(f);   // not `push(...files)` — a 100k-file drop would overflow the call stack
    if (busy) return;
    busy = true;
    try { while (queue.length) await processOne(queue.shift()); }
    finally { busy = false; updateBar(); }   // always reset, even if a file threw unexpectedly
  }
  function updateBar() {
    const ok = results.filter((r) => r.data).length;
    const total = resultsEl.children.length;
    const skipped = total - ok;
    if (total === 0) { barEl.hidden = true; return; }
    barEl.hidden = false;
    summaryEl.textContent = `${ok} cleaned` + (skipped ? ` · ${skipped} skipped` : '');
    $('zip').disabled = ok === 0;
  }
  function uniqueNames(items) {
    const used = new Set();
    return items.map(({ name, data }) => {
      let n = name;
      if (used.has(n)) {
        const dot = name.lastIndexOf('.');
        const base = dot > 0 ? name.slice(0, dot) : name;
        const ext = dot > 0 ? name.slice(dot) : '';
        let c = 1;
        do { n = `${base}-${c}${ext}`; c++; } while (used.has(n));
      }
      used.add(n);
      return { name: n, data };
    });
  }
  function downloadZip() {
    const files = uniqueNames(results.filter((r) => r.data));
    if (!files.length) return;
    downloadBlob(new Blob([makeZip(files)], { type: 'application/zip' }), 'untraceable-photos.zip');
  }
  function clearAll() {
    generation++;            // tell any in-flight processOne to abandon its file
    queue.length = 0;        // and drop anything still queued
    for (const u of objectUrls) URL.revokeObjectURL(u);
    objectUrls.length = 0;
    results.length = 0;
    resultsEl.innerHTML = '';
    barEl.hidden = true;
  }

  // ---- events ----
  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); } });
  $('pick').addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
  fileInput.addEventListener('change', () => { handleFiles(fileInput.files); fileInput.value = ''; });

  ['dragenter', 'dragover'].forEach((ev) => dropZone.addEventListener(ev, (e) => { e.preventDefault(); dropZone.classList.add('drag'); }));
  ['dragleave', 'dragend'].forEach((ev) => dropZone.addEventListener(ev, () => dropZone.classList.remove('drag')));
  dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('drag'); handleFiles(e.dataTransfer.files); });
  window.addEventListener('dragover', (e) => e.preventDefault());   // don't navigate away on a stray drop
  window.addEventListener('drop', (e) => e.preventDefault());

  $('zip').addEventListener('click', downloadZip);
  $('clear').addEventListener('click', clearAll);
})();
