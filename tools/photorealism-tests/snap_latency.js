const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', r => {
    const n=r.request().url().split('/').pop();
    try{ r.fulfill({status:200, contentType:'text/javascript', body:fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ r.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror', e=>errs.push(e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const n of ['starter-guy.jpg','starter-soft.jpg','starter-wet-c.jpg','starter-freckles-c.jpg'])
      localStorage.setItem('seed|'+n,'1');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof syncNow === 'function');
  const R = await pg.evaluate(async () => {
    const out={};
    await fbLoad(); await accWatch();
    const S=globalThis.__FAKE;
    S.user={uid:'u1',email:'d@e.com'}; S.cbs.forEach(c=>c(S.user));
    await new Promise(r=>setTimeout(r,300));
    const c=document.createElement('canvas'); c.width=800; c.height=600;
    c.getContext('2d').fillStyle='#555'; c.getContext('2d').fillRect(0,0,800,600);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.9));
    const id=await galAdd({ ts:Date.now(), name:'r', thumb:await thumbOf(blob,false), blob });
    SYNC_AT=0; await syncNow(true);
    const rec=(await galAll()).find(x=>x.sid);
    galActive=rec.id;

    // the other device changes a LAYER: nothing to download, so this is
    // the honest measure of how fast the app itself reacts
    const { updateDoc, doc, collection } =
      await import('https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js');
    const ref = doc(collection(null,'users','u1','refs'), rec.sid);
    const t0=performance.now();
    await updateDoc(ref, { 'meta.lay':'{"c":{"dk":1,"mid":1}}', mAt: Date.now()+5000 });
    for (let i=0;i<400;i++){
      await new Promise(r=>setTimeout(r,2));
      if (localStorage.getItem('lay|'+rec.id)==='{"c":{"dk":1,"mid":1}}'){
        out.layerMs=Math.round(performance.now()-t0); break;
      }
    }
    // and a settings change
    const pref = doc(collection(null,'users','u1','prefs'),'app');
    const t1=performance.now();
    await updateDoc(pref, { 'v.accent':'#22cc88', pAt: Date.now()+5000 });
    for (let i=0;i<400;i++){
      await new Promise(r=>setTimeout(r,2));
      if (getComputedStyle(document.documentElement).getPropertyValue('--acc').trim()==='#22cc88'){
        out.accentMs=Math.round(performance.now()-t1); break;
      }
    }
    return out;
  });
  console.log('layer change applied in :', (R.layerMs==null?'NEVER':R.layerMs+'ms'));
  console.log('accent change applied in:', (R.accentMs==null?'NEVER':R.accentMs+'ms'));
  console.log('page errors:', errs.length?errs[0]:'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
