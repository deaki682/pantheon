const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
    const n = route.request().url().split('/').pop();
    try { route.fulfill({status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ route.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2400);
  await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
  });
  await pg.waitForTimeout(1500);

  // device A: a reference, some progress on it, and a capture of the drawing
  console.log('1) device A works:', await pg.evaluate(async () => {
    const mk = async (w,h,fill) => { const c=document.createElement('canvas');
      c.width=w; c.height=h; const g=c.getContext('2d'); g.fillStyle=fill; g.fillRect(0,0,w,h);
      return await new Promise(r=>c.toBlob(r,'image/jpeg',0.9)); };
    const blob = await mk(1200,900,'#777');
    const id = await galAdd({ ts:Date.now(), name:'ref A', thumb:await thumbOf(blob,false), blob });
    localStorage.setItem('time|'+id, '4200');
    localStorage.setItem('det|'+id, 'fine');
    localStorage.setItem('fmt|'+id, '{"w":11,"h":14}');
    // a capture of the drawing, as cmpSaveNow would store it
    const cap = await mk(900,700,'#432');
    await capStash(id, { blob:cap, framed:true, corners:null, rawW:900, rawH:700, adj:{con:12} });
    SYNC_AT=0; await syncNow(true);
    const S=globalThis.__FAKE;
    const doc=[...S.docs.entries()].filter(([k])=>!k.endsWith('/_prefs')).map(([,v])=>v)[0]||{};
    return 'objects=' + S.objects.size + ' [' + [...S.objects.keys()].map(k=>k.split('/')[2]).join(',') + ']'
      + ' meta=' + JSON.stringify(doc.meta||{}) + ' capAt=' + (doc.capAt?'set':'MISSING');
  }));

  // device B: wipe everything local, then sync from scratch
  console.log('2) device B wiped:', await pg.evaluate(async () => {
    const d = await gdb();
    await new Promise(r=>{ const t=d.transaction('photos','readwrite').objectStore('photos').clear(); t.onsuccess=()=>r(); t.onerror=()=>r(); });
    for (const k of Object.keys(localStorage)) if (/^(time|det|fmt|capk)\|/.test(k)) localStorage.removeItem(k);
    return 'local=' + (await galAll()).length;
  }));

  console.log('3) device B pulls:', await pg.evaluate(async () => {
    SYNC_AT=0; await syncNow(true);
    const all = await galAll(); const r = all[0]||{};
    return 'local=' + all.length + ' name="' + r.name + '"'
      + ' time=' + localStorage.getItem('time|'+r.id)
      + ' det=' + localStorage.getItem('det|'+r.id)
      + ' fmt=' + (localStorage.getItem('fmt|'+r.id)?'yes':'no')
      + ' capture=' + (r.cap ? Math.round(r.cap.size/1024)+'KB' : 'MISSING')
      + ' capMeta.framed=' + (r.capMeta||{}).framed;
  }));

  // opening the project must turn the synced capture into its saved compare
  console.log('4) capture adopted:', await pg.evaluate(async () => {
    const r = (await galAll())[0];
    await capAdopt(r.id, 'CKEY-ON-DEVICE-B');
    const saved = await dbGet('cmp|CKEY-ON-DEVICE-B');
    return saved && saved.blob
      ? 'yes, ' + Math.round(saved.blob.size/1024) + 'KB framed=' + saved.framed + ' adj.con=' + (saved.adj||{}).con
      : 'NO (fail)';
  }));

  console.log('5) idempotent   :', await pg.evaluate(async () => {
    SYNC_AT=0; await syncNow(true); SYNC_AT=0; await syncNow(true);
    return 'local=' + (await galAll()).length + ' objects=' + globalThis.__FAKE.objects.size
      + ' state="' + document.getElementById('accState').textContent + '"';
  }));

  // the case that was broken: compare already visited this session, so the
  // key is unchanged, and a newer capture arrives from the other device
  console.log('6) second photo :', await pg.evaluate(async () => {
    const r = (await galAll())[0];
    const c=document.createElement('canvas'); c.width=600; c.height=400;
    c.getContext('2d').fillStyle='#0a0'; c.getContext('2d').fillRect(0,0,600,400);
    const nb = await new Promise(x=>c.toBlob(x,'image/jpeg',0.9));
    // simulate the pull having brought a newer capture down
    r.cap=nb; r.capAt=Date.now()+1000; r.capMeta={framed:false, adj:{con:3}};
    await galPut(r);
    const took = await capAdopt(r.id, 'CKEY-ON-DEVICE-B');   // same key as before
    const saved = await dbGet('cmp|CKEY-ON-DEVICE-B');
    return 'adopted=' + took + ' newBlob=' + (saved && saved.blob && saved.blob.size===nb.size)
      + ' adj.con=' + ((saved||{}).adj||{}).con;
  }));
  console.log('7) no re-adopt  :', await pg.evaluate(async () => {
    const r = (await galAll())[0];
    return 'second call adopts again? ' + (await capAdopt(r.id, 'CKEY-ON-DEVICE-B'));
  }));
  console.log(errs.length ? 'ERRORS ' + errs.slice(0,3).join(' | ') : '8) page errors  : none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
