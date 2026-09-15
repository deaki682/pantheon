// Every interaction in the app, timed from the tap to the next paint, with a
// budget. Under CPU throttle, so the numbers mean something for a phone.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const RATE = +(process.argv[3]||4);
const BUDGET = 100;              // ms from the tap to the painted result
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  // a real photo, since that is what the artist has
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    // SEEDED: an unseeded photograph gave every run a different picture, so
    // a 10ms move between runs could be the change under test or could be
    // the noise. Same picture every time, on every version.
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(8000);                 // let background cooking finish
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: RATE });
  await pg.evaluate(()=>{
    window.__time = async (fn) => {
      const t0=performance.now();
      try{ await fn(); }catch(e){ return {ms:-1, err:String(e).slice(0,40)}; }
      const sync=performance.now()-t0;
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      return { ms:Math.round(performance.now()-t0), sync:Math.round(sync) };
    };
  });
  const steps = [
    ['toggle a layer off',      `LAYERS.hl=false; COMP.sig=null; viewRepaint();`],
    ['toggle a layer on',       `LAYERS.hl=true; COMP.sig=null; viewRepaint();`],
    ['switch detail to Fine',   `DETAIL='fine'; COMP.sig=null; viewRepaint();`],
    ['switch detail to Ultra',  `DETAIL='ultra'; COMP.sig=null; viewRepaint();`],
    ['open the layer panel',    `$('hudToggle').click();`],
    ['close the layer panel',   `$('hudToggle').click();`],
    ['open the grid menu',      `$('gridCorner').click();`],
    ['close the grid menu',     `if($('gridModal'))$('gridModal').style.display='none';`],
    ['zoom in one step',        `const r=$('viewport').getBoundingClientRect(); view.s*=1.6; applyView();`],
    ['pan',                     `view.x-=60; applyView();`],
    ['zoom back to fit',        `const r=$('viewport').getBoundingClientRect(); view.s=Math.min(r.width/WORLD.w, r.height/WORLD.h); view.x=(r.width-WORLD.w*view.s)/2; view.y=(r.height-WORLD.h*view.s)/2; applyView();`],
    ['open settings',           `$('gearBtn')&&$('gearBtn').click();`],
    ['close settings',          `$('gearModal').style.display='none';`],
    ['change the accent',       `applyAccent('#4aa3df');`],
    ['home screen',             `show('scrUpload');`],
    ['render the gallery',      `renderGallery();`],
    ['back to the drawing',     `show('scrMain'); applyView();`],
    ['open compare',            `$('compareBtn')&&$('compareBtn').click();`],
    ['leave compare',           `show('scrMain');`],
    // added this pass: the Edit window, where the artist reported lag
    ['open the edit window',    `return edOpenFor('tone');`],
    ['zoom in the edit window', `ED.z.s=Math.min(8,(ED.z.s||1)*1.6); edPaint();`],
    ['close the edit window',   `edClose(false);`],
    // added this pass: the crop preview, where the artist reported that a
    // diagonal grid "lags like crazy" while a square one is fine
    ['open the size screen',    `show('scrFormat'); fmtPreview();`],
    // Each pan step must NOT change the grid style: switching it rebuilds the
    // overlay, so alternating styles here would time a cache rebuild and call
    // it a pan. Pick the style in its own step, then pan.
    ['crop: pick a square grid',  `CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_STYLE='sq'; fmtPreview();`],
    ['pan the crop, square',      `fmtLive(true); FMT_OFF.x=(FMT_OFF.x>0.5?0.35:0.65); fmtPreview();`],
    ['crop: pick a diagonal grid',`CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_STYLE='diag'; fmtPreview();`],
    ['pan the crop, diagonal',    `fmtLive(true); FMT_OFF.x=(FMT_OFF.x>0.5?0.35:0.65); fmtPreview();`],
    ['pinch the crop, diagonal',  `fmtLive(true); FMT_ZOOM=(FMT_ZOOM>2?1.4:2.6); fmtPreview();`],
    // and the crisp pass that lands once the hand comes off it - off the
    // critical path, but a stall you can still feel after lifting
    ['crop settles crisp',        `FMT_LIVE=0; FMT_PHOTO=null; fmtPreview();`],
    ['crop: pick a dotted grid',  `CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_STYLE='dots'; fmtPreview();`],
    ['pan the crop, dots',        `fmtLive(true); FMT_OFF.x=(FMT_OFF.x>0.5?0.35:0.65); fmtPreview();`],
    ['change the grid style',     `gsSet(GRID_STYLE==='diag'?'sq':'diag');`],
  ];
  // A single reading is noisy enough to cross the budget by itself, so each
  // interaction is run REPS times and reported by its median. Chasing one
  // unlucky sample is how a loop like this wastes a day.
  const REPS = +(process.argv[4]||5);
  const med = a => { const b=[...a].sort((x,y)=>x-y); return b[Math.floor(b.length/2)]; };
  const acc = new Map(steps.map(([n])=>[n,{ms:[],sync:[],err:null}]));
  for (let rep=0; rep<REPS; rep++){
    for (const [name, code] of steps){
      const r = await pg.evaluate(async (code)=> await window.__time(new Function(code)), code);
      const a=acc.get(name);
      if (r.err){ a.err=r.err; } else { a.ms.push(r.ms); a.sync.push(r.sync); }
      await pg.waitForTimeout(160);
    }
  }
  const rows=[...acc].map(([name,a])=>({ name, err:a.err,
    ms:a.ms.length?med(a.ms):-1, sync:a.sync.length?med(a.sync):-1,
    lo:a.ms.length?Math.min(...a.ms):-1, hi:a.ms.length?Math.max(...a.ms):-1 }));
  rows.sort((a,b)=>b.ms-a.ms);
  console.log('port '+PORT+'  CPU x'+RATE+'   budget '+BUDGET+'ms to painted   median of '+REPS);
  for (const r of rows)
    console.log('  '+(r.ms>BUDGET?'OVER ':'ok   ')+String(r.ms).padStart(5)+'ms'
      +'  (sync '+String(r.sync).padStart(4)+'  spread '+String(r.lo).padStart(4)+'-'+String(r.hi).padStart(4)+')  '
      +r.name+(r.err?('  ERR '+r.err):''));
  console.log('  over budget: '+rows.filter(r=>r.ms>BUDGET).length+' of '+rows.length);
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
