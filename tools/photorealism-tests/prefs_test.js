const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
async function device(br, tag) {
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
    const n = route.request().url().split('/').pop();
    try { route.fulfill({status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ route.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  pg.on('pageerror', e => console.log('  PAGEERROR(' + tag + ') ' + e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2300);
  await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE = globalThis.__FAKE || {};
    globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
  });
  await pg.waitForTimeout(1200);
  return pg;
}
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  // one browser context = one "device"; the fake backend is per-page, so
  // this test moves the document between them by hand
  const A = await device(br, 'A');

  console.log('1) A changes look:', await A.evaluate(async () => {
    applyAccent('#4aa3df');                       // blue accent
    localStorage.setItem('gridStyle','dots');
    localStorage.setItem('gridThk','3');
    localStorage.setItem('gridSub','2');
    localStorage.setItem('uiScale','l'); UI_SCALE='l'; a11yApply();
    PREF_DIRTY = true;
    SYNC_AT = 0; await syncNow(true);
    const d = globalThis.__FAKE.docs.get('users/u1/prefs/app');
    return d ? 'stored accent=' + d.v.accent + ' grid=' + d.v.gridStyle
             + ' thk=' + d.v.gridThk + ' scale=' + d.v.uiScale + ' pAt=' + (d.pAt?'set':'MISSING')
             : 'NOTHING STORED (fail)';
  }));
  const doc = await A.evaluate(() => globalThis.__FAKE.docs.get('users/u1/prefs/app'));

  // device B: a fresh page with default settings
  const B = await device(br, 'B');
  console.log('2) B before     :', await B.evaluate(() => 'accent=' + localStorage.getItem('accent')
    + ' grid=' + GRID_STYLE + ' thk=' + GRID_THK + ' sub=' + GRID_SUB
    + ' scale=' + UI_SCALE + ' uiL=' + document.documentElement.classList.contains('uiL')));

  console.log('3) B pulls them :', await B.evaluate(async (d) => {
    globalThis.__FAKE.docs.set('users/u1/prefs/app', d);
    PREF_SEEN = 0; PREF_DIRTY = false;
    SYNC_AT = 0; await syncNow(true);
    return 'accent=' + getComputedStyle(document.documentElement).getPropertyValue('--acc').trim()
      + ' grid=' + GRID_STYLE + ' thk=' + GRID_THK + ' sub=' + GRID_SUB
      + ' scale=' + UI_SCALE + ' uiL=' + document.documentElement.classList.contains('uiL');
  }, doc));

  console.log('4) B does not    echo it back:', await B.evaluate(async () => {
    const before = globalThis.__FAKE.docs.get('users/u1/prefs/app').pAt;
    SYNC_AT = 0; await syncNow(true);
    return globalThis.__FAKE.docs.get('users/u1/prefs/app').pAt === before ? 'correct, no ping-pong' : 'REWROTE IT (fail)';
  }));

  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
