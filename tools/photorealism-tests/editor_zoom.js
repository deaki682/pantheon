// Zooming and panning in the Edit / Crop window must not re-tone the picture.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof edOpenFor==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<30000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
  });
  const cdp = await ctx.newCDPSession(pg); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  console.log(await pg.evaluate(async ()=>{
    const out={};
    await edOpenFor('tone');
    for (let i=0;i<300;i++){ if (ED && ED.on && ED.pre) break; await new Promise(r=>setTimeout(r,50)); }
    out.pre=[ED.pre.width, ED.pre.height];
    const t=(f)=>{ const a=performance.now(); f(); return performance.now()-a; };
    out.firstPaintMs=Math.round(t(()=>edRender()));
    // now zoom repeatedly, which changes no adjustment at all
    let s=0; for (let i=0;i<10;i++){ ED.z.s=1+((i%5)*0.6); s+=t(()=>edRender()); }
    out.zoomPaintMs=Math.round(s/10);
    // and a real adjustment, which must still re-tone
    const before=ED.toneKey;
    s=0; for (let i=0;i<4;i++){ ED.R.con=10+i*7; s+=t(()=>edRender()); }
    out.adjustPaintMs=Math.round(s/4);
    out.retonedOnAdjust = ED.toneKey!==before;
    return out;
  }));
  console.log('page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
