const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof galAdd==='function', null, {timeout:30000});
  await pg.waitForFunction(() => !document.getElementById('introSplash').classList.contains('on'), null, {timeout:15000});
  await pg.evaluate(async () => {
    for (let i=0;i<8;i++){
      const c=document.createElement('canvas'); c.width=c.height=400;
      const g=c.getContext('2d'); g.fillStyle='hsl('+(i*40)+',50%,50%)'; g.fillRect(0,0,400,400);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.85));
      await galAdd({ ts:Date.now()+i, name:'s'+i+'.jpg', thumb:await thumbOf(b,false), blob:b, ord:100+i });
    }
    renderGallery();
  });
  await pg.waitForTimeout(500);
  // CPU-throttle to something like a budget phone, then drag and count long frames
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await pg.evaluate(() => { window.__f=[]; let p=performance.now();
    const t=()=>{ const n=performance.now(); window.__f.push(n-p); p=n; requestAnimationFrame(t); };
    requestAnimationFrame(t); });
  const a = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  await pg.mouse.move(a.x+a.width/2, a.y+a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(700);
  await pg.evaluate(()=>{ window.__f.length=0; });      // measure the DRAG, not the lift
  for (let i=0;i<40;i++){ await pg.mouse.move(a.x+a.width/2 + Math.sin(i/4)*140, a.y+a.height/2); await pg.waitForTimeout(16); }
  const f = await pg.evaluate(()=>window.__f.slice());
  await pg.mouse.up();
  await pg.waitForTimeout(500);
  f.sort((x,y)=>x-y);
  const p50=f[Math.floor(f.length*0.5)], p95=f[Math.floor(f.length*0.95)];
  const longF=f.filter(v=>v>32).length;
  console.log('frames sampled :', f.length, '(4x CPU throttle)');
  console.log('median frame   :', p50.toFixed(1)+'ms');
  console.log('p95 frame      :', p95.toFixed(1)+'ms');
  console.log('frames > 32ms  :', longF, '('+(100*longF/f.length).toFixed(0)+'%)', longF/f.length < 0.15 ? 'ok' : 'FAIL');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
