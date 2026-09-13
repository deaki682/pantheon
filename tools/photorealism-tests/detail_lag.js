const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  const cdp = await ctx.newCDPSession(pg); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  // let the background pre-cook of the other tools finish, as it would in use
  await pg.waitForTimeout(12000);
  for (const lv of ['fine','hyper','ultra','fine']){
    const r = await pg.evaluate(async (lv)=>{
      LAYERS.dk=true; LAYERS.lt=true; LAYERS.hl=false;   // a couple of tone layers
      DETAIL=lv; COMP.sig=null;
      const t0=performance.now();
      let standIn=false, ms=0;
      for (let i=0;i<600;i++){
        const c=compositeCv();
        const ready = lv==='ultra' ? true : (DET.key===fkey() && !!DET.lv[lv]);
        if (ready){ ms=performance.now()-t0; break; }
        standIn=true;
        await new Promise(r=>setTimeout(r,50));
      }
      return { ms:Math.round(ms), standIn };
    }, lv);
    console.log(('switch to '+lv).padEnd(18), String(r.ms).padStart(5)+'ms',
      r.standIn ? ' (showed Ultra while it loaded)' : ' (instant)');
  }
  console.log('(4x CPU throttle)');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
