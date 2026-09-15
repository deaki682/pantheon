// Download Options: four cumulative layer images, each carrying the grid, all
// at Ultra. They must actually DIFFER from each other - four identical files
// is the failure this test exists to catch - and the app must be left exactly
// as it was found.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
const crypto=require('crypto');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2,
    isMobile:true, hasTouch:true, acceptDownloads:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof dloBuildAll==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  let bad=0;
  const ok=(c,m)=>{ if(!c) bad++; console.log('  '+(c?'ok   ':'FAIL ')+m); };

  // the size screen, from a fresh reference
  await pg.evaluate(async ()=>{
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrMain.on')) { show('scrFormat'); }
    $('unit').value='cm'; $('widthIn').value='30';
    await new Promise(r=>setTimeout(r,500));
  });
  const onFmt = await pg.evaluate(()=>({
    screen:(document.querySelector('.screen.on')||{}).id,
    begin: $('fmtGo').textContent.trim(),
    hasDl: !!$('fmtDl'),
    ready: GRID_READY }));
  ok(onFmt.begin==='Begin', 'the size screen says "'+onFmt.begin+'"');
  ok(onFmt.hasDl, 'it carries a Download button');

  // Download from there commits the format and opens the window over the project
  const tOpen=Date.now();
  await pg.evaluate(()=>$('fmtDl').onclick());
  await pg.waitForFunction(()=>getComputedStyle(document.getElementById('dloModal')).display!=='none',
    null,{timeout:60000}).catch(()=>{});
  console.log('       window on screen '+(Date.now()-tOpen)+'ms after the tap');
  const opened = await pg.evaluate(()=>({
    shown: getComputedStyle($('dloModal')).display!=='none',
    screen:(document.querySelector('.screen.on')||{}).id,
    ready: GRID_READY,
    labels: [0,1,2,3].map(i=>$('dloNm'+i).textContent.trim()) }));
  ok(opened.shown, 'Download Options opened (on '+opened.screen+', grid ready: '+opened.ready+')');
  console.log('       options: '+opened.labels.join(' | '));

  // they must arrive IN ORDER and become downloadable one at a time, not all
  // at the end - that progression is the whole point of the redesign
  const order = await pg.evaluate(async ()=>{
    const seen=[]; const t0=performance.now();
    for (let n=0;n<1200 && seen.length<4;n++){
      for (let i=0;i<4;i++)
        if ($('dloRow'+i).classList.contains('ready') && !seen.some(s=>s.i===i))
          seen.push({i, ms:Math.round(performance.now()-t0)});
      await new Promise(r=>setTimeout(r,100));
    }
    return seen;
  });
  ok(order.length===4, 'all four finished ('+order.map(o=>o.i+'@'+o.ms+'ms').join(', ')+')');
  ok(order.map(o=>o.i).join()==='0,1,2,3', 'they arrive in order, shading first');
  ok(order.length===4 && order[0].ms < order[3].ms,
     'the first is usable '+(order.length===4?(order[3].ms-order[0].ms):0)+'ms before the last');

  const before = await pg.evaluate(()=>({L:{...LAYERS}, det:DETAIL, done:DONE.length, circ:CIRCS.length}));
  const hashes=[];
  for (let i=0;i<4;i++){
    const dl = pg.waitForEvent('download',{timeout:120000}).catch(()=>null);
    await pg.evaluate(i=>$('dlo'+i).onclick(), i);
    const d = await dl;
    if (!d){ ok(false,'option '+i+' produced no file'); continue; }
    const path = await d.path();
    const buf = require('fs').readFileSync(path);
    hashes.push({ name:d.suggestedFilename(), size:buf.length,
                  h:crypto.createHash('sha1').update(buf).digest('hex').slice(0,12) });
  }
  for (const x of hashes) console.log('       '+x.name.padEnd(42)+String(Math.round(x.size/1024)).padStart(5)+' KB  '+x.h);
  ok(hashes.length===4, 'all four downloaded');
  ok(new Set(hashes.map(x=>x.h)).size===hashes.length, 'all four are different images');
  ok(hashes.every(x=>/-(shading|darks|lights|full)-/.test(x.name)), 'each file is named for its layer');

  const landed = await pg.evaluate(()=>(document.querySelector('.screen.on')||{}).id);
  ok(landed==='scrMain', 'downloading from the size screen leaves them in the project (on '+landed+')');
  const after = await pg.evaluate(()=>({L:{...LAYERS}, det:DETAIL, done:DONE.length, circ:CIRCS.length}));
  ok(JSON.stringify(before)===JSON.stringify(after),
     'the app is left as it was found (layers, detail, marks)');

  // the gallery route: an UNFORMATTED reference goes to the size screen
  const unf = await pg.evaluate(async ()=>{
    const W=900,H=700; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
    await addRef(new File([b],'fresh.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')) break; await new Promise(r=>setTimeout(r,50)); }
    const rec=(await galAll()).find(x=>x.name==='fresh.jpg');
    try{ localStorage.removeItem('fmt|'+rec.id); }catch(e){}
    show('scrUpload'); await new Promise(r=>setTimeout(r,400));
    REFM=rec.id; dloForRef(rec.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')) break; await new Promise(r=>setTimeout(r,50)); }
    await new Promise(r=>setTimeout(r,600));
    return { screen:(document.querySelector('.screen.on')||{}).id,
             windowShown: getComputedStyle($('dloModal')).display!=='none' };
  });
  ok(unf.screen==='scrFormat' && !unf.windowShown,
     'an unformatted reference goes to the size screen first (landed on '+unf.screen+')');

  if (errs.length) console.log('  page errors: '+errs.slice(0,3).join(' | '));
  console.log(bad? '\n'+bad+' problem(s)' : '\nDownload Options works');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
