// The reference canvas must be big only while the photograph is on screen.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof paintWorld==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const r = await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<20000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    const cv=$('refImg'), out={ world:[WORLD.w,WORLD.h] };
    out.plain=[cv.width,cv.height];
    out.laidOutPlain=[cv.offsetWidth,cv.offsetHeight];
    const time=(fn)=>{ const t0=performance.now(); fn(); return performance.now()-t0; };
    let s=0; for (let i=0;i<8;i++){ s+=time(()=>{ LAYERS.dk=!LAYERS.dk; COMP.sig=null; viewRepaint(); }); }
    out.layerAvgMs=Math.round(s/8);
    LAYERS.dk=false; COMP.sig=null; viewRepaint();   // actually ON a layer view
    out.layer=[cv.width,cv.height];
    out.laidOutLayer=[cv.offsetWidth,cv.offsetHeight];
    LAYERS.dk=LAYERS.lt=LAYERS.hl=true; DETAIL='ultra'; COMP.sig=null; viewRepaint();
    out.backToPlain=[cv.width,cv.height];
    out.mbPlain=+((out.plain[0]*out.plain[1]*4)/1048576).toFixed(1);
    out.mbLayer=+((out.layer[0]*out.layer[1]*4)/1048576).toFixed(1);
    return out;
  });
  console.log('world', r.world.join('x'));
  console.log('  photograph on screen :', r.plain.join('x'), '=', r.mbPlain, 'MB   (laid out', r.laidOutPlain.join('x')+')');
  console.log('  layer view on screen :', r.layer.join('x'), '=', r.mbLayer, 'MB   (laid out', r.laidOutLayer.join('x')+')',
    r.layer[0]===r.world[0] ? 'ok' : 'FAIL');
  console.log('  back to the photo    :', r.backToPlain.join('x'), r.backToPlain[0]>r.world[0] ? 'ok' : 'FAIL');
  console.log('  grid box unchanged   :', r.laidOutPlain.join('x')===r.laidOutLayer.join('x')
    && r.laidOutPlain[0]===r.world[0] ? 'ok' : 'FAIL');
  console.log('  repeated layer toggle:', r.layerAvgMs+'ms');
  console.log('  page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
