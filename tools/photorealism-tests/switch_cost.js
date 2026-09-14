// How long does a layer toggle / detail switch take to actually repaint?
const { chromium } = require('playwright-core');
const PORT = process.argv[2] || '8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const info = await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    const cv=$('refImg');
    return { world:[WORLD.w,WORLD.h], canvas:[cv.width,cv.height] };
  });
  await pg.waitForTimeout(9000);            // let background cooking settle
  const t = await pg.evaluate(async ()=>{
    const time=(fn)=>{ const t0=performance.now(); fn(); return performance.now()-t0; };
    const out={};
    // warm everything first
    DETAIL='ultra'; LAYERS.dk=LAYERS.lt=LAYERS.hl=true; COMP.sig=null; viewRepaint();
    await new Promise(r=>setTimeout(r,400));
    // a) the plain reference repaint
    out.plain = Math.round(time(()=>{ COMP.sig=null; viewRepaint(); }));
    // b) toggle one layer off (a composite repaint)
    out.toggleOff = Math.round(time(()=>{ LAYERS.hl=false; COMP.sig=null; viewRepaint(); }));
    // c) toggle it back on (back to the plain photo)
    out.toggleOn = Math.round(time(()=>{ LAYERS.hl=true; COMP.sig=null; viewRepaint(); }));
    // d) repeated composite repaints, averaged
    LAYERS.hl=false; viewRepaint(); await new Promise(r=>setTimeout(r,200));
    let s=0; for (let i=0;i<6;i++){ s+=time(()=>{ LAYERS.dk=!LAYERS.dk; COMP.sig=null; viewRepaint(); }); }
    out.layerAvg = Math.round(s/6);
    // e) the blit alone: draw the composite into the reference canvas
    const comp=compositeCv(); const cv=$('refImg'); const g=cv.getContext('2d');
    let b=0; for (let i=0;i<6;i++) b+=time(()=>{ g.drawImage(comp,0,0,cv.width,cv.height); });
    out.blitAvg = Math.round(b/6);
    return out;
  });
  console.log('port '+PORT+'  world '+info.world.join('x')+'  reference canvas '+info.canvas.join('x'));
  console.log('   plain repaint '+t.plain+'ms | layer off '+t.toggleOff+'ms | layer on '+t.toggleOn
    +'ms | repeated layer toggles avg '+t.layerAvg+'ms | the blit alone '+t.blitAvg+'ms');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
