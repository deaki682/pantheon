const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2,
    isMobile:true, hasTouch:true, permissions:[] });
  const pg = await ctx.newPage();
  pg.on('pageerror', e => console.log('PAGEERROR', e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof openPhoto === 'function');
  await pg.waitForTimeout(1800);

  // make a colour project and open it the way a tap does
  const id = await pg.evaluate(async () => {
    const c=document.createElement('canvas'); c.width=600; c.height=400;
    const g=c.getContext('2d'); g.fillStyle='#d81b60'; g.fillRect(0,0,600,400);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.95));
    const id=await galAdd({ ts:Date.now(), name:'colour', thumb:await thumbOf(blob,true), blob });
    localStorage.setItem('mode|'+id,'c');
    localStorage.setItem('fmt|'+id, JSON.stringify({w:8,h:10,u:'in',cell:1,on:1}));
    await renderGallery();
    return id;
  });
  await pg.evaluate(async (id) => {
    const r = await galGet(id);
    openPhoto(r.blob, id);
  }, id);
  await pg.waitForFunction(() => { try { return !!GRID_READY } catch(e){ return false } },
                           null, { timeout: 60000 });
  await pg.waitForTimeout(500);

  const state = await pg.evaluate(() => ({
    refMode: REFMODE, colorRefClass: document.body.classList.contains('colorRef'),
    isColor: isColor(galActive), ckey: String(CKEY).slice(-3),
  }));
  console.log('after opening the project:', JSON.stringify(state));

  // go to compare the way a tap does, then feed it a colour photo
  await pg.evaluate(() => { window.__origCamStart = camStart;
    window.camStart = async () => false; });          // no camera in headless
  await pg.evaluate(() => $('compareBtn').onclick());
  await pg.waitForTimeout(900);

  const shot = await pg.evaluate(async () => {
    const isGrey = (cv) => { const g=cv.getContext('2d',{willReadFrequently:true});
      const d=g.getImageData(0,0,Math.min(60,cv.width),Math.min(60,cv.height)).data;
      let seen=0;
      for (let i=0;i<d.length;i+=4){ if (d[i+3]<8) continue; seen++;
        if (Math.abs(d[i]-d[i+1])>6 || Math.abs(d[i+1]-d[i+2])>6) return false; }
      return seen ? true : 'blank'; };
    const c=document.createElement('canvas'); c.width=600; c.height=400;
    c.getContext('2d').fillStyle='#1e88e5'; c.getContext('2d').fillRect(0,0,600,400);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.95));
    await cmpSetPhoto(blob);
    await new Promise(r=>setTimeout(r,300));
    cmpSize(); cmpRender();
    await new Promise(r=>setTimeout(r,200));
    return {
      refMode: REFMODE,
      colorRefClass: document.body.classList.contains('colorRef'),
      rawGrey: CMP.raw ? isGrey(CMP.raw) : 'none',
      imgGrey: CMP.img ? isGrey(CMP.img) : 'none',
      canvasGrey: isGrey(document.getElementById('cmpCv')),
      showing: CMP.showing, mode: CMP.mode,
    };
  });
  console.log('after taking a photo      :', JSON.stringify(shot));
  await pg.screenshot({ path: __dirname + '/color-compare.png' });
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
