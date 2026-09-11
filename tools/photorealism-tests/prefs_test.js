// Settings travel: accent, grid style, unit and the rest sync per-key,
// newest change wins, and an arriving pref repaints in place.
const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const mk = async v => {
    const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
      const n = route.request().url().split('/').pop();
      try { route.fulfill({status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8')}); }
      catch(e){ route.fulfill({status:404, body:''}); }
    });
    const pg = await ctx.newPage();
    pg.on('pageerror', e => { console.log('PAGE ERROR ['+v+']', e.message); process.exitCode=1; });
    await pg.addInitScript(() => {
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
      localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    });
    await pg.goto('http://localhost:8899/index.html');
    await pg.waitForTimeout(2400);
    await pg.evaluate(async () => {
      await fbLoad(); await accWatch();
      globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
      globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
    });
    await pg.waitForTimeout(1200);
    return pg;
  };
  // the two devices share one fake backend only if they share a context;
  // instead run them in one page serially, like sync_test wipes do — but
  // prefs live in localStorage, so a real second context is needed. The
  // fake store is per-page, so device B replays A's doc by hand.
  const A = await mk('A');

  // A: set taste through the app's own setters, then sync
  console.log('1) A sets taste :', await A.evaluate(async () => {
    applyAccent('#5a8fd8');
    gsSet('dots');
    localStorage.setItem('gridCol','#e0524f');
    localStorage.setItem('unit','cm');
    prefPoke();
    SYNC_AT=0; await syncNow(true);
    const d = globalThis.__FAKE.docs.get('users/u1/refs/_prefs');
    return d ? 'doc pv.accent='+d.pv.accent+' gridStyle='+d.pv.gridStyle
             + ' gridCol='+d.pv.gridCol+' unit='+d.pv.unit
             + ' keys='+Object.keys(d.pv).length
           : 'NO DOC';
  }));
  const doc = await A.evaluate(() => globalThis.__FAKE.docs.get('users/u1/refs/_prefs'));

  // B: fresh device, defaults everywhere; the account's taste arrives and paints
  const B = await mk('B');
  console.log('2) B adopts     :', await B.evaluate(async d => {
    globalThis.__FAKE.docs.set('users/u1/refs/_prefs', d);
    SYNC_AT=0; await syncNow(true);
    const acc = getComputedStyle(document.documentElement).getPropertyValue('--acc').trim();
    return 'accent='+localStorage.getItem('accent')+' painted='+acc
      + ' gridStyle='+localStorage.getItem('gridStyle')+' GRID_STYLE='+GRID_STYLE
      + ' gridCol='+localStorage.getItem('gridCol')+' unit='+localStorage.getItem('unit');
  }, doc));

  // B: changes one key; only that key should win going back
  console.log('3) B edits one  :', await B.evaluate(async () => {
    await new Promise(r=>setTimeout(r, 30));    // a newer stamp than the pull's
    applyAccent('#6aa84f');
    prefPoke();
    SYNC_AT=0; await syncNow(true);
    const d = globalThis.__FAKE.docs.get('users/u1/refs/_prefs');
    return 'doc accent='+d.pv.accent+' gridStyle kept='+(d.pv.gridStyle==='dots');
  }));
  const doc2 = await B.evaluate(() => globalThis.__FAKE.docs.get('users/u1/refs/_prefs'));

  // A: pulls B's accent, keeps its own everything else
  console.log('4) A converges  :', await A.evaluate(async d => {
    globalThis.__FAKE.docs.set('users/u1/refs/_prefs', d);
    SYNC_AT=0; await syncNow(true);
    const acc = getComputedStyle(document.documentElement).getPropertyValue('--acc').trim();
    return 'accent='+localStorage.getItem('accent')+' painted='+acc
      + ' gridStyle='+localStorage.getItem('gridStyle');
  }, doc2));

  // A long-used device signing in fresh must ADOPT, not clobber
  const C = await mk('C');
  console.log('5) C no clobber :', await C.evaluate(async d => {
    localStorage.setItem('accent','#d86bb0');   // C's own old habit, pre-sign-in
    localStorage.removeItem('prefSeen'); localStorage.removeItem('prefAt');
    globalThis.__FAKE.docs.set('users/u1/refs/_prefs', d);
    SYNC_AT=0; await syncNow(true);
    const doc = globalThis.__FAKE.docs.get('users/u1/refs/_prefs');
    return 'local accent='+localStorage.getItem('accent')
      + ' (account wins='+(localStorage.getItem('accent')==='#6aa84f')+')'
      + ' doc accent='+doc.pv.accent;
  }, doc2));

  console.log('6) page errors  :', process.exitCode ? 'SOME' : 'none');
  await br.close();
})().catch(e => { console.error(e); process.exit(1); });
