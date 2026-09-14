const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof paintWorld==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(8000);
  const cdp = await ctx.newCDPSession(pg); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  console.log(await pg.evaluate(async ()=>{
    const cv=$('refImg'); const t=(f)=>{ const a=performance.now(); f(); return Math.round(performance.now()-a); };
    const out={};
    LAYERS.hl=true; LAYERS.dk=true; LAYERS.lt=true; DETAIL='ultra'; COMP.sig=null; viewRepaint();
    await new Promise(r=>setTimeout(r,300));
    out.plainCanvas=[cv.width,cv.height];
    // composite -> composite: no resize
    LAYERS.hl=false; COMP.sig=null; viewRepaint(); await new Promise(r=>setTimeout(r,250));
    out.layerCanvas=[cv.width,cv.height];
    let s=0; for (let i=0;i<5;i++){ s+=t(()=>{ LAYERS.dk=!LAYERS.dk; COMP.sig=null; viewRepaint(); }); }
    out.layerToLayerMs=Math.round(s/5);
    // the resize alone, at the size the plain view uses
    const r=refSize();
    out.resizeOnlyMs=t(()=>{ cv.width=r.w; cv.height=r.h; });
    out.drawBigMs=t(()=>{ cv.getContext('2d').drawImage(state.img,0,0,r.w,r.h); });
    out.resizeBackMs=t(()=>{ cv.width=WORLD.w; cv.height=WORLD.h; });
    return out;
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
