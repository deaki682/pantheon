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
  await pg.waitForTimeout(2300);
  await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
  });
  await pg.waitForTimeout(1600);
  console.log('listener attached:', await pg.evaluate(() => !!SYNC_OFF));

  // "the phone takes a shot": a new reference appears with no manual sync
  const t = await pg.evaluate(async () => {
    const c = document.createElement('canvas'); c.width=1600; c.height=1200;
    const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,1600,1200);
    const blob = await new Promise(r => c.toBlob(r,'image/jpeg',0.9));
    const t0 = performance.now();
    await galAdd({ ts:Date.now(), name:'camera shot', thumb: await thumbOf(blob,false), blob });
    // wait for it to reach the backend, without ever pressing Sync now
    for (let i=0;i<80;i++){
      await new Promise(r=>setTimeout(r,100));
      if (globalThis.__FAKE.objects.size > 0) return Math.round(performance.now()-t0);
    }
    return -1;
  });
  console.log('auto-push after capture:', t < 0 ? 'NEVER (fail)' : t + 'ms, no manual sync');

  // "the tablet": a document arrives from elsewhere, listener must pull it
  const d = await pg.evaluate(async () => {
    const S = globalThis.__FAKE;
    const c = document.createElement('canvas'); c.width=800; c.height=600;
    c.getContext('2d').fillStyle='#333'; c.getContext('2d').fillRect(0,0,800,600);
    const blob = await new Promise(r => c.toBlob(r,'image/jpeg',0.9));
    const before = (await galAll()).length;
    S.objects.set('users/u1/refs/remote1.jpg', blob);
    const t0 = performance.now();
    const { setDoc, doc, collection } = await import('https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js');
    await setDoc(doc(collection(null,'users','u1','refs'),'remote1'),
                 { name:'from the phone', ts:Date.now(), mode:'bw', thumb:'' });
    for (let i=0;i<80;i++){
      await new Promise(r=>setTimeout(r,100));
      const all = await galAll();
      if (all.length > before) return Math.round(performance.now()-t0) + 'ms, name="' +
        (all.find(x=>x.sid==='remote1')||{}).name + '"';
    }
    return 'NEVER (fail)';
  });
  console.log('auto-pull on live doc :', d);
  console.log('page errors:', errs.length ? errs[0] : 'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
