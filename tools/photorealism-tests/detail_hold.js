// Switching detail must never flash the full-detail reading on the way.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  const r = await pg.evaluate(async ()=>{
    const out={};
    LAYERS.dk=true; LAYERS.lt=true; LAYERS.hl=false;     // a layer view, so detail shows
    // settle on Fine with its planes resident
    DETAIL='fine'; COMP.sig=null;
    for (let i=0;i<400;i++){ compositeCv(); if (DET.key===fkey() && DET.lv.fine) break; await new Promise(r=>setTimeout(r,40)); }
    COMP.sig=null; compositeCv();
    const lvOf=()=>{ const m=/T(ultra|prog|hyper|fine)/.exec(COMP.sig||''); return m?m[1]:'?'; };
    out.settledOn = lvOf();
    // drop Hyper's planes so the switch has to load, exactly like a first switch
    delete DET.lv.hyper; delete DET.done.hyper;
    // now switch, and watch what is drawn on each frame until it settles
    DETAIL='hyper'; COMP.sig=null;
    const seen=[];
    for (let i=0;i<400;i++){
      COMP.sig=null; compositeCv();
      seen.push(lvOf());
      if (DET.key===fkey() && DET.lv.hyper) break;
      await new Promise(r=>setTimeout(r,40));
    }
    out.drawnDuringLoad = [...new Set(seen)];
    out.flashedUltra = seen.includes('ultra');
    out.endedOn = lvOf();
    return out;
  });
  console.log(JSON.stringify(r));
  console.log('no flash to full detail:', !r.flashedUltra ? 'ok' : 'FAIL (showed ultra mid-switch)');
  console.log('landed on the new level:', r.endedOn==='hyper' ? 'ok' : 'FAIL');
  console.log('page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
