// One browser, one boot, every sync assertion. Replaces sync_test +
// meta_test + prefs_test, which each paid for their own launch and their
// own 2.3s splash. Waits on conditions, never on the clock.
const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
let pass = 0, fail = 0;
const ok = (name, cond, detail) => {
  (cond ? pass++ : fail++);
  console.log((cond ? '  ok   ' : '  FAIL ') + name + (detail ? '  ' + detail : ''));
};
(async () => {
  const t0 = Date.now();
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', r => {
    const n = r.request().url().split('/').pop();
    try { r.fulfill({status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ r.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    // this check makes its own references, so skip seeding the four
    // starters - decoding and thumbnailing them was 20 of the 25 seconds
    for (const n of ['starter-guy.jpg','starter-soft.jpg',
                     'starter-wet-c.jpg','starter-freckles-c.jpg'])
      localStorage.setItem('seed|' + n, '1');
  });
  // 'load' waits for every image the page ever fetches; the checks only
  // need the script to be wired up
  await pg.goto('http://localhost:8899/index.html', { waitUntil: 'domcontentloaded' });
  // ready when the app has finished wiring itself up
  await pg.waitForFunction(() => typeof galAdd === 'function' && typeof syncNow === 'function',
                           null, { timeout: 20000 });
  console.log('boot ' + (Date.now()-t0) + 'ms');

  await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
  });
  await pg.waitForFunction(() => !!ACC_USER, null, { timeout: 10000 });

  const R = await pg.evaluate(async () => {
    const out = {};
    const mk = async (w,h,f) => { const c=document.createElement('canvas'); c.width=w; c.height=h;
      const g=c.getContext('2d'); g.fillStyle=f; g.fillRect(0,0,w,h);
      return await new Promise(r=>c.toBlob(r,'image/jpeg',0.9)); };
    const S = globalThis.__FAKE;

    // reference + progress + a capture of the drawing
    const blob = await mk(1200,900,'#777');
    const id = await galAdd({ ts:Date.now(), name:'ref A', thumb:await thumbOf(blob,false), blob });
    localStorage.setItem('time|'+id,'4200'); localStorage.setItem('det|'+id,'fine');
    await capStash(id, { blob: await mk(900,700,'#432'), framed:true, corners:null,
                         rawW:900, rawH:700, adj:{con:12} });
    SYNC_AT=0; await syncNow(true);
    out.uploaded = [...S.objects.keys()].map(k=>k.split('/')[2]).sort().join(',');
    out.byteForByte = (await galAll()).some(r => r.sid &&
      S.objects.get('users/u1/refs/'+r.sid+'.jpg')?.size === r.blob.size);

    // settings
    applyAccent('#4aa3df');
    localStorage.setItem('gridStyle','dots'); localStorage.setItem('gridThk','3');
    PREF_DIRTY = true; SYNC_AT = 0; await syncNow(true);
    out.prefsStored = (S.docs.get('users/u1/prefs/app')||{}).v?.accent;

    // a second device: wipe everything local and pull it all back
    const d = await gdb();
    await new Promise(r=>{ const t=d.transaction('photos','readwrite').objectStore('photos').clear();
                           t.onsuccess=()=>r(); t.onerror=()=>r(); });
    for (const k of Object.keys(localStorage))
      if (/^(time|det|fmt|capk)\|/.test(k)) localStorage.removeItem(k);
    localStorage.setItem('accent','#e8833a'); localStorage.setItem('gridStyle','sq');
    localStorage.setItem('gridThk','1'); loadGridPrefs();
    PREF_SEEN = 0; PREF_DIRTY = false;
    SYNC_AT=0; await syncNow(true);

    const all = await galAll(); const r = all[0]||{};
    out.pulled = all.length;
    out.progress = localStorage.getItem('time|'+r.id);
    out.capture = !!r.cap;
    out.adopted = await capAdopt(r.id, 'CKEY-B');
    const saved = await dbGet('cmp|CKEY-B');
    out.adoptedMeta = saved && saved.framed === true && (saved.adj||{}).con === 12;
    out.accent = getComputedStyle(document.documentElement).getPropertyValue('--acc').trim();
    out.grid = GRID_STYLE + '/' + GRID_THK;

    // repeat syncs must change nothing
    const before = S.objects.size, pAt = (S.docs.get('users/u1/prefs/app')||{}).pAt;
    SYNC_AT=0; await syncNow(true); SYNC_AT=0; await syncNow(true);
    out.stable = (await galAll()).length === all.length && S.objects.size === before
                 && (S.docs.get('users/u1/prefs/app')||{}).pAt === pAt;

    // a sync asked for while one is running must be re-run, not dropped:
    // this is where accent and grid changes were vanishing on a real
    // phone, because an upload was almost always in flight
    SYNC_BUSY = true; SYNC_AGAIN = false;
    await syncNow(true);
    out.queuedWhileBusy = SYNC_AGAIN === true;
    SYNC_BUSY = false;
    PREF_SIG = null; prefsPoll();                   // baseline as it stands
    localStorage.setItem('accent','#ff0000');       // then a real change
    PREF_DIRTY = false; prefsPoll();
    out.noticedChange = PREF_DIRTY === true;
    SYNC_AT = 0; await syncNow(true);
    out.pushedAfterBusy = (S.docs.get('users/u1/prefs/app')||{}).v?.accent === '#ff0000';

    // layers and detail are written from a dozen places; the watcher has
    // to notice them without any of those places knowing it exists
    galActive = (await galAll())[0].id;
    META_SIG_ID = null;
    localStorage.setItem('lay|'+galActive, '{"o":1,"c":{"dk":1,"mid":0}}');
    localStorage.setItem('det|'+galActive, 'hyper');
    SYNC_DIRTY.clear();
    // the watcher's first pass takes the baseline, the second sees change
    const poll = () => { const m = readMeta(galActive);
      for (const k of META_CHURN) delete m[k];
      const sig = JSON.stringify(m);
      if (META_SIG_ID !== galActive){ META_SIG_ID = galActive; META_SIG = sig; return; }
      if (sig !== META_SIG){ META_SIG = sig; syncTouch(galActive); } };
    poll();
    localStorage.setItem('lay|'+galActive, '{"o":1,"c":{"dk":1,"mid":1}}');
    poll();
    out.layersNoticed = SYNC_DIRTY.has(galActive);
    // and the timer alone must NOT trigger one, or it syncs every 3s
    SYNC_DIRTY.clear();
    localStorage.setItem('time|'+galActive, String(Date.now()));
    poll();
    out.timerIsQuiet = !SYNC_DIRTY.has(galActive);
    SYNC_DIRTY.add(galActive); SYNC_AT=0; await syncNow(true);
    out.layersReached = (S.docs.get('users/u1/refs/'+
      (await galAll())[0].sid)||{}).meta?.lay?.indexOf('"mid":1') > 0;

    // a project uploaded before settings travelled must catch up, and a
    // device with no local copy of them must never erase the real ones
    const legacy = (await galAll())[0];
    localStorage.setItem('time|'+legacy.id, '9999');
    SYNC_DIRTY.add(legacy.id); SYNC_AT=0; await syncNow(true);
    out.legacyCaughtUp = (S.docs.get('users/u1/refs/'+legacy.sid)||{}).meta?.time === '9999';
    localStorage.removeItem('time|'+legacy.id);
    localStorage.removeItem('det|'+legacy.id);
    localStorage.removeItem('fmt|'+legacy.id);
    SYNC_DIRTY.add(legacy.id); SYNC_AT=0; await syncNow(true);
    out.emptyDidNotErase = (S.docs.get('users/u1/refs/'+legacy.sid)||{}).meta?.time === '9999';

    // a touch made before the account finished restoring is not lost
    const held = ACC_USER; ACC_USER = null;
    SYNC_DIRTY.clear(); syncTouch(legacy.id);
    out.touchHeld = SYNC_DIRTY.has(legacy.id);
    ACC_USER = held;

    // deleting takes the synced copy with it and does not resurrect
    const gone = (await galAll()).find(x=>x.sid);
    await syncDrop(gone); await galDel(gone.id);
    SYNC_AT=0; await syncNow(true);
    out.deleted = (await galAll()).length === 0;
    return out;
  });

  ok('reference and capture both upload', R.uploaded === 'caps,refs', R.uploaded);
  ok('reference uploads byte for byte',   R.byteForByte);
  ok('settings reach the account',        R.prefsStored === '#4aa3df', R.prefsStored);
  ok('second device pulls the reference', R.pulled === 1);
  ok('project progress crosses',          R.progress === '4200', R.progress);
  ok('comparison photo crosses',          R.capture);
  ok('capture adopts with its framing',   R.adopted && R.adoptedMeta);
  ok('accent colour crosses',             R.accent === '#4aa3df', R.accent);
  ok('grid style and thickness cross',    R.grid === 'dots/3', R.grid);
  ok('repeat syncs change nothing',       R.stable);
  ok('delete does not resurrect',         R.deleted);
  ok('a layer change is noticed',         R.layersNoticed);
  ok('the timer alone stays quiet',       R.timerIsQuiet);
  ok('layers reach the account',          R.layersReached);
  ok('old projects catch up on settings', R.legacyCaughtUp);
  ok('empty settings never erase real ones', R.emptyDidNotErase);
  ok('a touch before sign-in is held',    R.touchHeld);
  ok('a busy sync is queued, not lost',   R.queuedWhileBusy);
  ok('a settings change is noticed',      R.noticedChange);
  ok('and pushed once free',              R.pushedAfterBusy);
  ok('no page errors',                    errs.length === 0, errs[0] || '');

  await br.close();
  console.log((fail ? 'FAILED ' + fail + ' of ' : 'all ') + (pass+fail) +
              ' checks in ' + Math.round((Date.now()-t0)/1000) + 's');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
