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
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
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
    ['zoom back to fit',        `fitView&&fitView(); applyView();`],
    ['open settings',           `$('gearBtn')&&$('gearBtn').click();`],
    ['close settings',          `$('gearModal').style.display='none';`],
    ['change the accent',       `try{localStorage.setItem('accent','#4aa3df');}catch(e){} applyAccent&&applyAccent();`],
    ['home screen',             `show('scrUpload');`],
    ['render the gallery',      `renderGallery();`],
    ['back to the drawing',     `show('scrMain'); applyView();`],
    ['open compare',            `$('compareBtn')&&$('compareBtn').click();`],
    ['leave compare',           `show('scrMain');`],
  ];
  const rows=[];
  for (const [name, code] of steps){
    const r = await pg.evaluate(async (code)=> await window.__time(new Function(code)), code);
    rows.push({ name, ...r });
    await pg.waitForTimeout(220);
  }
  rows.sort((a,b)=>b.ms-a.ms);
  console.log('port '+PORT+'  CPU x'+RATE+'   budget '+BUDGET+'ms to painted');
  for (const r of rows)
    console.log('  '+(r.ms>BUDGET?'OVER ':'ok   ')+String(r.ms).padStart(5)+'ms'
      +'  (sync '+String(r.sync).padStart(5)+'ms)  '+r.name+(r.err?('  ERR '+r.err):''));
  console.log('  over budget: '+rows.filter(r=>r.ms>BUDGET).length+' of '+rows.length);
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
