// Where does the memory actually go when a low-tier phone exports?
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch({...require('./browser.js'),
    args:[...(require('./browser.js').args||[]),'--enable-precise-memory-info']});
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    try{ Object.defineProperty(navigator,'deviceMemory',{get:()=>3,configurable:true}); }catch(e){}
  });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#f8e0c0'); gr.addColorStop(1,'#201008'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(x=>c.toBlob(x,'image/jpeg',.95));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(x=>setTimeout(x,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(x=>setTimeout(x,50)); }
  });
  await pg.waitForTimeout(9000);
  const r = await pg.evaluate(async ()=>{
    const px=c=>c&&c.width?c.width*c.height*4:0;
    const tally=()=>{
      const held={};
      held['the reference (state.img)']=px(state.img);
      held['the photograph canvas (refHi)']=px(document.getElementById('refHi'));
      held['the world canvas (refImg)']=px(document.getElementById('refImg'));
      held['the composite (COMP.cv)']=px(COMP.cv);
      held['the grid canvas']=px(document.getElementById('gridCv'));
      let planes=0;
      try{ for (const k in (DET.lv||{})){ const p=DET.lv[k];
        for (const f of ['dD','lD','hl']) if (p&&p[f]) planes+=p[f].length; } }catch(e){}
      held['cooked detail planes']=planes;
      let parts=0;
      try{ for (const f of ['ph','sh','dp','hl','rgb'])
        if (COMP[f]) parts += COMP[f].length*(COMP[f].BYTES_PER_ELEMENT||1); }catch(e){}
      held['the cook (COMP parts)']=parts;
      held['crop preview caches']=px(FMT_PHOTO&&FMT_PHOTO.cv)+px(FMT_PUNCH)+px(FMT_GRID&&FMT_GRID.cv);
      held['editor preview cache']=px(PRE_CACHE&&PRE_CACHE.cv);
      held['the grid decision map']=px(PUNCH_MAP&&PUNCH_MAP.cv);
      return held;
    };
    const before=tally();
    // what the export frees before it composes
    expFreeRoom();
    await new Promise(r=>setTimeout(r,200));
    const after=tally();
    // what a Download then adds, at the size a 3GB phone gets
    const {w,h}=worldSize();
    let k=Math.max(1,Math.min(2,(state.img.width||w)/w));
    const shown=viewSrc(); if (shown&&shown.width>w*k) k=shown.width/w;
    k *= 1.18;
    const MAXPX = refCap()<=2560 ? 11e6 : refCap()<4096 ? 16e6 : 17e6;
    if (w*h*k*k>MAXPX) k=Math.sqrt(MAXPX/(w*h));
    const eW=Math.round(w*k), eH=Math.round(h*k);
    return { before, after, exportCanvas:eW*eH*4, exportDims:eW+'x'+eH, cap:refCap() };
  });
  const mb=n=>+(n/1e6).toFixed(1);
  let tot=0, tot2=0;
  console.log('  deviceMemory 3GB, refCap '+r.cap);
  console.log('    '+'held'.padEnd(34)+' drawing   freed for the export');
  for (const [k,v] of Object.entries(r.before)){ const a=r.after[k]||0;
    if(!v&&!a) continue; tot+=v; tot2+=a;
    console.log('    '+k.padEnd(34)+String(mb(v)).padStart(6)+' MB '
      +String(mb(a)).padStart(11)+' MB'+(a<v?'   <- released':'')); }
  console.log('    '+'TOTAL'.padEnd(34)+String(mb(tot)).padStart(6)+' MB '
    +String(mb(tot2)).padStart(11)+' MB');
  console.log('  the export canvas: '+mb(r.exportCanvas)+' MB for '+r.exportDims);
  console.log('  peak during a download: was '+mb(tot+r.exportCanvas)
    +' MB, now '+mb(tot2+r.exportCanvas)+' MB');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
