// Every grid setting, timed. A redraw happens on every zoom, pan and repaint.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='40'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(4000);
  const cdp = await ctx.newCDPSession(pg); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  const combos = [];
  for (const style of ['sq','diag','dots'])
    for (const sub of [0,2])
      for (const lab of [false,true])
        combos.push({style, sub, lab});
  const rows = await pg.evaluate(async (combos)=>{
    // and at several grid densities, because a 1cm square on a 40cm drawing
    // is forty columns, not sixteen
    const med=a=>{const b=[...a].sort((x,y)=>x-y);return b[Math.floor(b.length/2)];};
    const out=[];
    // zoomed in, which is where the artist notices it
    const r=$('viewport').getBoundingClientRect();
    view.s=Math.min(r.width/WORLD.w, r.height/WORLD.h)*3;
    for (const cells of [16, 40, 80]){
      GRID_COLS=cells; GRID_ROWS=Math.round(cells*WORLD.h/WORLD.w);
      for (const c of combos){
        GRID_STYLE=c.style; GRID_SUB=c.sub; GRID_LAB=c.lab; GRID_ON=true;
        const t=[];
        for (let i=0;i<7;i++){
          const a=performance.now(); drawGrid(); t.push(performance.now()-a);
          await new Promise(r=>requestAnimationFrame(r));
        }
        out.push({ ...c, cells, ms:Math.round(med(t)), cols:GRID_COLS, rows:GRID_ROWS });
      }
    }
    // and the format screen's own preview, which redraws the whole design
    for (const c of combos){
      GRID_STYLE=c.style; GRID_SUB=c.sub; GRID_LAB=c.lab;
      const t=[];
      show('scrFormat');
      for (let i=0;i<5;i++){
        const a=performance.now(); fmtPreview(); t.push(performance.now()-a);
        await new Promise(r=>requestAnimationFrame(r));
      }
      out.push({ ...c, cells:'fmtPreview', ms:Math.round(med(t)) });
    }
    show('scrMain');
    return out;
  }, combos);
  rows.sort((a,b)=>b.ms-a.ms);
  console.log('port '+PORT+'  CPU x4, zoomed 3x  (median redraw)');
  for (const r of rows)
    console.log('  '+String(r.ms).padStart(4)+'ms   '+String(r.cells).padStart(10)+' cells   style='+r.style.padEnd(5)
      +' sub='+r.sub+' labels='+(r.lab?'on ':'off'));
  console.log('  worst/best ratio: '+(rows[0].ms/Math.max(1,rows[rows.length-1].ms)).toFixed(1)+'x');
  if (errs.length) console.log('  page errors:', errs.slice(0,2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
