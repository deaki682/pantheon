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
    labels: [0,1,2,3].map(i=>$('dloNm'+i).textContent.trim()),
    cols: getComputedStyle($('dloGrid')).gridTemplateColumns.split(' ').length }));
  ok(opened.shown, 'Download Options opened (on '+opened.screen+', grid ready: '+opened.ready+')');
  console.log('       options: '+opened.labels.join(' | '));
  ok(opened.cols===2, 'laid out two across ('+opened.cols+' columns)');

  // Timed from INSIDE the page, against one mark, so the phases cannot be
  // confused with the test's own polling. Two different questions:
  //   - how fast do the PICTURES appear once the reference is ready
  //   - how far behind do the FILES arrive
  // The reference is already open and cooked here, which is the case that
  // has to feel instant: it is what the gallery route lands in too, once
  // the opening is done.
  const timed = await pg.evaluate(async ()=>{
    // make sure we are fully open and cooked first
    for (let i=0;i<4000;i++){
      if (document.querySelector('#scrMain.on') && GRID_READY
          && FORM.cv && FORM.key===fkey()) break;
      await new Promise(r=>setTimeout(r,50));
    }
    const prev=[], file=[];
    const realPrev = window.dloPreview;
    let t0=0;
    window.dloPreview = function(i){ const r=realPrev.apply(this,arguments);
      prev[i]=Math.round(performance.now()-t0); return r; };
    const obs=[];
    for (let i=0;i<4;i++){
      const row=$('dloRow'+i);
      const o=new MutationObserver(()=>{ if (row.classList.contains('ready') && file[i]==null)
        file[i]=Math.round(performance.now()-t0); });
      o.observe(row,{attributes:true,attributeFilter:['class']}); obs.push(o);
    }
    dloReset();
    t0=performance.now();
    dloOpen();
    for (let n=0;n<1200 && file.filter(x=>x!=null).length<4; n++)
      await new Promise(r=>setTimeout(r,50));
    obs.forEach(o=>o.disconnect());
    window.dloPreview=realPrev;
    const th=$('dloTh0');
    return { prev, file, backing: th.width,
             icons: [0,1,2,3].map(i=>getComputedStyle($('dlo'+i)).display) };
  });
  console.log('       pictures at  '+timed.prev.map(x=>x+'ms').join(', '));
  console.log('       files at     '+timed.file.map(x=>x+'ms').join(', '));
  ok(timed.prev.filter(x=>x!=null).length===4, 'all four pictures drew');
  ok(timed.prev[3]!=null && timed.prev[3] < 900,
     'and they are all up in '+timed.prev[3]+'ms, without waiting on a file');
  ok(timed.backing>=140, 'each is a large picture ('+timed.backing+'px backing), not a tile');
  ok(timed.file.filter(x=>x!=null).length===4, 'all four files finished');
  ok(timed.file[0]!=null && timed.prev[3]!=null && timed.file[0] > timed.prev[3],
     'the pictures beat the first file by '+(timed.file[0]-timed.prev[3])+'ms');
  ok(timed.file[3] > timed.file[0],
     'the files arrive in order, '+(timed.file[3]-timed.file[0])+'ms apart');
  ok(timed.icons.every(d=>d!=='none'), 'each one reveals its own download icon');

  const before = await pg.evaluate(()=>({L:{...LAYERS}, det:DETAIL, done:DONE.length, circ:CIRCS.length}));
  const hashes=[];
  for (let i=0;i<4;i++){
    const dl = pg.waitForEvent('download',{timeout:120000}).catch(()=>null);
    await pg.evaluate(i=>$('dlo'+i).onclick(), i);
    const d = await dl;
    if (!d){ ok(false,'option '+i+' produced no file'); continue; }
    const buf = require('fs').readFileSync(await d.path());
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
