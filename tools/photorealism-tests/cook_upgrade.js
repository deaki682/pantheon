const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof cookFineQ==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const open = await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob);
    const t0=performance.now();
    openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    return { ms:Math.round(performance.now()-t0), q:COOK_Q, world:[WORLD.w,WORLD.h], wantQ:cookFineQ() };
  });
  console.log('drawing open      :', open.ms+'ms', ' sampling at open q='+open.q,
    ' (target q='+open.wantQ+')', open.q===1 ? 'ok (open not slowed)' : 'FAIL');
  // the background upgrade
  await pg.waitForFunction(()=>COOK_Q>1 && FORM.key===fkey(), null, {timeout:180000}).catch(()=>{});
  const up = await pg.evaluate(()=>({ q:COOK_Q, cook:[cookSize().w,cookSize().h], world:[WORLD.w,WORLD.h],
    formKey:FORM.key===fkey() }));
  console.log('after the upgrade :', 'q='+up.q, ' planes', up.cook.join('x'),
    ' world', up.world.join('x'), up.q===3 && up.formKey ? 'ok' : 'FAIL');
  // toggling a layer must give the layer view at once, not the bare photo
  // with the finer planes in hand, a layer view must be drawn at that rate
  const tog = await pg.evaluate(async ()=>{
    LAYERS.hl=false;
    const src=viewSrc();
    const isPhoto = src===state.img;
    return { q:COOK_Q, isPhoto, size: src&&src!==state.img ? [src.width,src.height] : null };
  });
  console.log('layer view        :', 'q='+tog.q, ' drawn at', tog.size?tog.size.join('x'):'(the bare photo)',
    tog.size && tog.size[0]>2000 && !tog.isPhoto ? 'ok (3x the old 1134px)' : 'FAIL');
  // and if the finer planes are NOT ready, it must still show layers at once
  const fall = await pg.evaluate(async ()=>{
    // faithfully mid-upgrade: the planes in hand are the COARSE ones, and
    // the sampling rate has just been raised, so the fine cook is still out
    LAYERS.hl=true; COOK_Q=1;
    const coarseKey=fkey();
    FORM.key=coarseKey;                    // what ensureForm leaves behind
    COMP.key=null; COMP.sig=null;
    COOK_Q=3;                              // the upgrade has just started
    LAYERS.hl=false;                       // and the artist toggles a layer
    const src=viewSrc();
    return { q:COOK_Q, isPhoto: src===state.img, size: src?[src.width,src.height]:null };
  });
  console.log('mid-upgrade toggle:', 'q fell back to '+fall.q,
    ' showing', fall.isPhoto?'the bare photo':'a layer view at '+(fall.size||[]).join('x'),
    fall.q===1 && !fall.isPhoto ? 'ok' : 'FAIL');
  // and the grid still owns the geometry
  const geo = await pg.evaluate(()=>{ const cv=$('refImg');
    return { laidOut:[cv.offsetWidth,cv.offsetHeight], world:[WORLD.w,WORLD.h] }; });
  console.log('grid geometry     :', JSON.stringify(geo),
    geo.laidOut[0]===geo.world[0] ? 'ok' : 'FAIL');
  console.log('page errors       :', errs.length?errs.slice(0,3):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
