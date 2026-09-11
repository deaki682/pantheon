const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
    const n = route.request().url().split('/').pop();
    try { route.fulfill({ status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8') }); }
    catch(e){ route.fulfill({ status:404, body:'' }); }
  });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2400);

  console.log('0) home prompt   :', await pg.evaluate(() => {
    const e = document.getElementById('accHome');
    const b = document.getElementById('accHomeBtn').getBoundingClientRect();
    const r = document.getElementById('titleRule').getBoundingClientRect();
    return getComputedStyle(e).display + ' "' + document.getElementById('accHomeBtn').textContent
      + '" below-ruler=' + (b.top >= r.bottom - 1);
  }));

  // one real user-made reference (the starters must NOT upload)
  console.log('1) seed a photo  :', await pg.evaluate(async () => {
    const c = document.createElement('canvas'); c.width = 3000; c.height = 2000;
    const g = c.getContext('2d');
    g.fillStyle = '#777'; g.fillRect(0,0,3000,2000);
    g.fillStyle = '#fff'; g.fillRect(400,300,900,700);
    const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.95));
    const id = await galAdd({ ts: Date.now(), name: 'my shot', thumb: await thumbOf(blob, false), blob });
    const all = await galAll();
    return 'id=' + id + ' local=' + all.length + ' starters=' + all.filter(r => r.seed).length
      + ' bytes=' + blob.size;
  }));

  console.log('2) sign in       :', await pg.evaluate(async () => {
    const fb = await fbLoad();
    await accWatch();
    globalThis.__FAKE.user = { uid: 'u1', email: 'dylan@example.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
    return 'ACC_USER=' + (ACC_USER ? ACC_USER.email : 'none');
  }));
  await pg.waitForTimeout(2500);   // sign-in kicks a sync

  console.log('2b) byte-for-byte:', await pg.evaluate(async () => {
    const S = globalThis.__FAKE;
    const mine = await galAll();
    const r = mine.find(x => x.sid);
    const up = S.objects.get('users/u1/refs/' + r.sid + '.jpg');
    return 'local=' + r.blob.size + 'B uploaded=' + up.size + 'B identical='
      + (r.blob.size === up.size) + ' type=' + up.type;
  }));

  console.log('3) after push    :', await pg.evaluate(async () => {
    const S = globalThis.__FAKE;
    const mine = await galAll();
    const synced = mine.filter(r => r.sid).length;
    const upl = [...S.objects.entries()].map(([k,v]) => k.split('/').pop().slice(0,6) + '=' + Math.round(v.size/1024) + 'KB');
    return 'localWithSid=' + synced + ' objects=' + S.objects.size + ' docs=' + [...S.docs.keys()].filter(k=>!k.endsWith('/_prefs')).length
      + ' [' + upl.join(' ') + '] state="' + document.getElementById('accState').textContent + '"';
  }));

  // a second device: same account, empty gallery
  console.log('4) wipe device   :', await pg.evaluate(async () => {
    const d = await gdb();
    await new Promise(r => { const t = d.transaction('photos','readwrite').objectStore('photos').clear(); t.onsuccess=()=>r(); t.onerror=()=>r(); });
    return 'local=' + (await galAll()).length;
  }));

  console.log('5) pull back     :', await pg.evaluate(async () => {
    SYNC_AT = 0;
    await syncNow(true);
    const all = await galAll();
    const r = all[0] || {};
    return 'local=' + all.length + ' name="' + (r.name||'') + '" hasBlob=' + !!r.blob
      + ' sid=' + (r.sid ? 'yes' : 'no') + ' thumb=' + (r.thumb ? 'yes' : 'no')
      + ' state="' + document.getElementById('accState').textContent + '"';
  }));

  console.log('6) no duplicates :', await pg.evaluate(async () => {
    SYNC_AT = 0; await syncNow(true);
    SYNC_AT = 0; await syncNow(true);
    const all = await galAll();
    return 'local=' + all.length + ' objects=' + globalThis.__FAKE.objects.size;
  }));

  console.log('7) delete syncs  :', await pg.evaluate(async () => {
    const all = await galAll(); const r = all.find(x => x.sid);
    await syncDrop(r); await galDel(r.id);
    const S = globalThis.__FAKE;
    const tomb = S.docs.get('users/u1/refs/' + r.sid);
    SYNC_AT = 0; await syncNow(true);
    return 'objects=' + S.objects.size + ' tombstoned=' + !!(tomb && tomb.deleted)
      + ' localAfterResync=' + (await galAll()).length;
  }));

  console.log(errs.length ? errs.slice(0,5).join('\n') : '8) page errors   : none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
