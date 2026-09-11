// Regression matrix for Photorealism: viewports x button sizes, every screen,
// menus, rotation sequences. Reports page errors, overlapping visible chrome,
// off-screen controls, and unexpected layout facts. Usage: node regress.js [quick]
const { chromium } = require('playwright-core');
const OUT = '/tmp/claude-0/-home-user-pantheon/43db5575-695c-5ade-801f-30bed7c1325e/scratchpad/reg/';
require('fs').mkdirSync(OUT, { recursive: true });
const QUICK = process.argv.includes('quick');

const VIEWS = [
  { tag: 'phoneP', w: 390, h: 844 },
  { tag: 'phoneL', w: 844, h: 390 },
  { tag: 'tabL',   w: 1280, h: 800 },
  { tag: 'tabP',   w: 800, h: 1280 },
  { tag: 'foldL',  w: 841, h: 701 },
];
const SCALES = QUICK ? [null] : [null, 'l'];

// chrome elements whose visible boxes must never overlap each other
const CHROME = ['backBtn','setBtn','expBtn','hudToggle','detBtn','gridBtn','underBtn','compareBtn'];
const MENUS = ['hud','detMenu','gridMenu','underMenu'];

function inter(a, b) {
  const x = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const y = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  return x * y;
}

async function boxes(pg, ids) {
  return pg.evaluate((ids) => {
    const o = {};
    for (const id of ids) {
      const el = document.getElementById(id); if (!el) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      o[id] = { x: r.x, y: r.y, w: r.width, h: r.height };
    }
    return { b: o, vw: innerWidth, vh: innerHeight };
  }, ids);
}

function checkLayout(tag, { b, vw, vh }, issues, allowPairs = []) {
  const ids = Object.keys(b);
  for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
    const a = ids[i], c = ids[j];
    if (allowPairs.some(p => p.includes(a) && p.includes(c))) continue;
    const ov = inter(b[a], b[c]);
    if (ov > 4) issues.push(`${tag}: ${a} overlaps ${c} (${Math.round(ov)}px²)`);
  }
  for (const id of ids) {
    const r = b[id];
    if (r.x < -1 || r.y < -1 || r.x + r.w > vw + 1 || r.y + r.h > vh + 1)
      issues.push(`${tag}: ${id} off-screen (${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.w)}x${Math.round(r.h)} in ${vw}x${vh})`);
  }
}

async function waitReady(pg) {
  try {
    // returns the instant the grid is ready instead of on a 2s tick
    await pg.waitForFunction(
      () => { try { return !!GRID_READY } catch (e) { return false } },
      null, { timeout: 90000 });
    return true;
  } catch (e) {}
  for (let i = 0; i < 5; i++) {
    await pg.waitForTimeout(2000);
    if (await pg.evaluate(() => { try { return !!GRID_READY } catch (e) { return false } })) return true;
  }
  return false;
}

async function run(br, v, scale, report) {
  const tag = `${v.tag}${scale ? '+' + scale.toUpperCase() : ''}`;
  const issues = [];
  const ctx = await br.newContext({ viewport: { width: v.w, height: v.h }, reducedMotion: 'no-preference',
    deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const pg = await ctx.newPage();
  await pg.addInitScript((sc) => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    localStorage.setItem('lang','en');
    if (sc) localStorage.setItem('uiScale', sc);
  }, scale);
  pg.on('pageerror', e => issues.push(`${tag}: PAGEERROR ${e.message}`));
  pg.on('console', m => { if (m.type() === 'error' && !/ERR_CONNECTION|Failed to load resource|net::/.test(m.text())) issues.push(`${tag}: CONSOLE ${m.text().slice(0, 160)}`); });
  try {
    // 'load' waits for every image the page ever fetches - 20+ seconds
    // per config, ten configs. Wait for the gallery to actually exist.
    await pg.goto('http://localhost:8899/index.html', { waitUntil: 'domcontentloaded' });
    await pg.waitForFunction(
      () => document.querySelectorAll('#gallery .gitem, #galleryC .gitem').length > 0,
      null, { timeout: 30000 });
    // home: scrollable when content overflows
    const home = await pg.evaluate(() => { const s = document.getElementById('scrUpload');
      return { sh: s.scrollHeight, ch: s.clientHeight, ov: getComputedStyle(s).overflowY }; });
    if (home.sh > home.ch + 2 && home.ov !== 'auto' && home.ov !== 'scroll') issues.push(`${tag}: home overflows (${home.sh}>${home.ch}) but is not scrollable`);
    await pg.screenshot({ path: `${OUT}${tag}-home.png` });
    // format screen
    await pg.locator('.gitem').first().click(); await pg.waitForTimeout(1200);
    await pg.screenshot({ path: `${OUT}${tag}-format.png` });
    const fg = await boxes(pg, ['fmtGo','backBtn','gmDesign2']);
    checkLayout(tag + '/format', fg, issues);
    await pg.locator('#fmtGo').click();
    if (!await waitReady(pg)) { issues.push(`${tag}: drawing screen never became ready`); await ctx.close(); report.push({ tag, issues }); return; }
    await pg.waitForTimeout(800);
    await pg.screenshot({ path: `${OUT}${tag}-draw.png` });
    checkLayout(tag + '/draw', await boxes(pg, CHROME), issues);
    // grid fully covers viewport after open (edge bug)
    const cov = await pg.evaluate(() => { const c = document.getElementById('gridCv'), v = document.getElementById('viewport');
      const r = v.getBoundingClientRect(); return { cw: c.width, ch: c.height, vw: Math.round(r.width * devicePixelRatio), vh: Math.round(r.height * devicePixelRatio) }; });
    if (Math.abs(cov.cw - cov.vw) > 2 || Math.abs(cov.ch - cov.vh) > 2) issues.push(`${tag}: grid canvas ${cov.cw}x${cov.ch} != viewport ${cov.vw}x${cov.vh}`);
    // layer menu
    await pg.locator('#hudToggle').click(); await pg.waitForTimeout(500);
    await pg.screenshot({ path: `${OUT}${tag}-layers.png` });
    checkLayout(tag + '/layers', await boxes(pg, CHROME.concat(['hud'])), issues);
    await pg.locator('#hudToggle').click(); await pg.waitForTimeout(300);
    // detail menu
    await pg.locator('#detBtn').click(); await pg.waitForTimeout(500);
    checkLayout(tag + '/detail', await boxes(pg, CHROME.concat(['detMenu'])), issues);
    await pg.locator('#detBtn').click(); await pg.waitForTimeout(300);
    // grid menu + grid style window
    await pg.locator('#gridBtn').click(); await pg.waitForTimeout(500);
    await pg.screenshot({ path: `${OUT}${tag}-gridmenu.png` });
    checkLayout(tag + '/gridmenu', await boxes(pg, CHROME.concat(['gridMenu'])), issues);
    await pg.locator('#gmDesign').click(); await pg.waitForTimeout(800);
    await pg.screenshot({ path: `${OUT}${tag}-gsd.png` });
    const gsd = await pg.evaluate(() => { const p = document.getElementById('gsdPanel'), r = p.getBoundingClientRect();
      const d = document.getElementById('gsdDone').getBoundingClientRect();
      return { pw: r.width, ph: r.height, vh: innerHeight, vw: innerWidth, doneIn: d.bottom <= innerHeight + 1 && d.right <= innerWidth + 1, scroll: p.scrollHeight > p.clientHeight + 2 }; });
    if (!gsd.doneIn) issues.push(`${tag}: Grid Style Done button off-screen`);
    if (gsd.scroll && gsd.vw > gsd.vh) issues.push(`${tag}: Grid Style panel scrolls in landscape (${gsd.ph}px)`);
    await pg.locator('#gsdStyleBox').click(); await pg.waitForTimeout(300);
    const pop = await pg.evaluate(() => { const r = document.getElementById('gsdStyles').getBoundingClientRect();
      return r.top >= -1 && r.bottom <= innerHeight + 1; });
    if (!pop) issues.push(`${tag}: Grid Style style-pop clips the viewport`);
    await pg.locator('#gsdStyleBox').click(); await pg.waitForTimeout(200);
    await pg.locator('#gsdDone').click(); await pg.waitForTimeout(400);
    // gear -> accessibility
    await pg.locator('#setBtn').click(); await pg.waitForTimeout(500);
    const gear = await pg.evaluate(() => { const g = document.getElementById('gearPanel'); const r = g.getBoundingClientRect();
      return { open: !!g.offsetParent, fits: r.height <= innerHeight + 1, scroll: g.scrollHeight > g.clientHeight + 2 }; });
    if (!gear.open) issues.push(`${tag}: gear panel did not open`);
    else if (!gear.fits && !gear.scroll) issues.push(`${tag}: gear panel taller than screen and not scrollable`);
    await pg.locator('#a11yBtn').click().catch(() => {}); await pg.waitForTimeout(500);
    const a11y = await pg.evaluate(() => { const p = document.getElementById('a11yPanel'); if (!p || !p.offsetParent) return null;
      const pr = p.getBoundingClientRect(); const bad = [...p.querySelectorAll('button')].filter(b => { const r = b.getBoundingClientRect(); return r.right > pr.right + 1 || r.left < pr.left - 1; });
      return { bad: bad.map(b => b.textContent.trim()) }; });
    if (a11y && a11y.bad.length) issues.push(`${tag}: accessibility buttons cut off by panel: ${a11y.bad.join(', ')}`);
    await pg.screenshot({ path: `${OUT}${tag}-a11y.png` });
    await pg.locator('#a11yDone').click().catch(() => {}); await pg.waitForTimeout(300);
    await pg.keyboard.press('Escape').catch(() => {});
    await pg.evaluate(() => { for (const id of ['a11yModal','gearModal']) { const m = document.getElementById(id); if (m) m.style.display = 'none'; } });
    // rotation sequence on the drawing screen: must end centred and covered
    const rot = v.w > v.h ? [{ w: v.h, h: v.w }, { w: v.w, h: v.h }] : [{ w: v.h, h: v.w }, { w: v.w, h: v.h }];
    for (const s of rot) { await pg.setViewportSize({ width: s.w, height: s.h }); await pg.waitForTimeout(900); }
    const after = await pg.evaluate(() => { const v = document.getElementById('viewport').getBoundingClientRect();
      const w = document.getElementById('refImg').getBoundingClientRect();
      const c = document.getElementById('gridCv');
      return { cx: Math.round(w.x + w.width / 2 - (v.x + v.width / 2)), cy: Math.round(w.y + w.height / 2 - (v.y + v.height / 2)),
        fitsW: w.width <= v.width + 2, fitsH: w.height <= v.height + 2,
        cov: Math.abs(c.width - Math.round(v.width * devicePixelRatio)) <= 2 && Math.abs(c.height - Math.round(v.height * devicePixelRatio)) <= 2 }; });
    if ((after.fitsW && Math.abs(after.cx) > 3) || (after.fitsH && Math.abs(after.cy) > 3)) issues.push(`${tag}: paper off-centre after double rotation (dx ${after.cx}, dy ${after.cy})`);
    if (!after.cov) issues.push(`${tag}: grid canvas not covering viewport after rotation`);
    checkLayout(tag + '/after-rotation', await boxes(pg, CHROME), issues);
    await pg.screenshot({ path: `${OUT}${tag}-rotated.png` });
    // compare screen
    await pg.locator('#compareBtn').click().catch(() => {}); await pg.waitForTimeout(900);
    const cmp = await pg.evaluate(() => { const s = document.getElementById('scrCompare'); if (!s.classList.contains('on')) return null;
      const btns = [...document.querySelectorAll('#cmpRow button, #lvBtn')].filter(b => b.offsetParent).map(b => { const r = b.getBoundingClientRect(); return { id: b.id, h: Math.round(r.height) }; });
      const sl = document.getElementById('alphaSl'); let slc = null;
      if (sl && sl.offsetParent) { const r = sl.getBoundingClientRect(); const pr = sl.parentElement.getBoundingClientRect(); slc = Math.round((r.x + r.width / 2) - (pr.x + pr.width / 2)); }
      return { btns, slc }; });
    if (cmp) {
      const hs = cmp.btns.map(b => b.h); const spread = Math.max(...hs) - Math.min(...hs);
      if (spread > 4) issues.push(`${tag}: compare toolbar button heights differ by ${spread}px (${cmp.btns.map(b => b.id + ':' + b.h).join(' ')})`);
      if (cmp.slc !== null && Math.abs(cmp.slc) > 3) issues.push(`${tag}: compare transparency slider off-centre by ${cmp.slc}px`);
      await pg.screenshot({ path: `${OUT}${tag}-compare.png` });
    }
  } catch (e) { issues.push(`${tag}: HARNESS ${String(e.message || e).split('\n')[0].slice(0, 140)}`); }
  await ctx.close();
  report.push({ tag, issues });
}

(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const report = [];
  for (const v of VIEWS) for (const sc of SCALES) await run(br, v, sc, report);
  await br.close();
  let total = 0;
  for (const r of report) { total += r.issues.length; console.log(`== ${r.tag}: ${r.issues.length ? '' : 'OK'}`); for (const i of r.issues) console.log('   ' + i); }
  console.log(`TOTAL ISSUES: ${total}`);
  require('fs').writeFileSync(OUT + 'report.json', JSON.stringify(report, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
