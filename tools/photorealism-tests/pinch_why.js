// A pan and a pinch both call fmtPreview once. Why does the pinch cost twice?
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=3; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30';
    CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_STYLE='diag'; GRID_ON=true; GRID_LAB=false; GRID_SUB=false;
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const out = await pg.evaluate(async ()=>{
    const cv=$('fmtCanvas');
    const snap=()=>({ cvw:cv.width, cvh:cv.height,
      cr:(()=>{const c=cropRect(); return Math.round(c.w)+'x'+Math.round(c.h);})(),
      gridKey: FMT_GRID? FMT_GRID.k : 'none' });
    const step = async (label, mutate)=>{
      mutate();
      const before=snap();
      const t=performance.now();
      fmtPreview();
      const sync=performance.now()-t;
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const total=performance.now()-t;
      const after=snap();
      return { label, sync:Math.round(sync), total:Math.round(total),
        resized: before.cvw!==after.cvw||before.cvh!==after.cvh,
        cv:after.cvw+'x'+after.cvh, cr:after.cr,
        gridRebuilt: before.gridKey!==after.gridKey };
    };
    FMT_ZOOM=1; FMT_OFF.x=0.5; FMT_OFF.y=0.5; fmtPreview();
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    const rows=[];
    for (let k=0;k<3;k++){
      rows.push(await step('pan       ', ()=>{ FMT_OFF.x = FMT_OFF.x>0.5?0.35:0.65; }));
      rows.push(await step('pinch     ', ()=>{ FMT_ZOOM = FMT_ZOOM>2?1.4:2.6; }));
    }
    return rows;
  });
  for (const r of out)
    console.log('  '+r.label+'sync '+String(r.sync).padStart(4)+'ms  total '+String(r.total).padStart(4)
      +'ms   canvas '+r.cv.padEnd(11)+' crop '+r.cr.padEnd(11)
      +(r.resized?' CANVAS RESIZED':'')+(r.gridRebuilt?'  GRID REBUILT':''));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
