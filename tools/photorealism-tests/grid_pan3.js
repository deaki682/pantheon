// Honest version: canvas draws are DEFERRED, so timing fmtPreview() in a
// tight loop measures command recording, not the work. Await a real paint
// between calls, which is what a pan actually does.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
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
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30';
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  console.log('  zoom  cell   style    per pan frame (flushed)');
  for (const zoom of [1, 2.2, 4]){
    for (const cell of [2, 0.5]){
      for (const style of ['sq','diag','dots']){
        const r = await pg.evaluate(async ([zoom,cell,style])=>{
          CELLSZ.u='cm'; CELLSZ.v=cell; GRID_STYLE=style; GRID_SUB=false;
          GRID_ON=true; GRID_LAB=false; FMT_ZOOM=zoom;
          FMT_OFF.x=0.5; FMT_OFF.y=0.5;
          fmtPreview();
          await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
          const times=[];
          for (let k=0;k<9;k++){
            FMT_OFF.x = 0.4 + (k%5)*0.05;        // a real pan: the crop moves
            const t=performance.now();
            fmtPreview();
            // force the queued work through before stopping the clock
            await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
            times.push(performance.now()-t);
          }
          times.sort((a,b)=>a-b);
          return { ms:Math.round(times[4]), prox: (typeof FMT_PROXY!=="undefined") };
        },[zoom,cell,style]);
        console.log('  '+String(zoom+'x').padEnd(6)+String(cell+'cm').padEnd(7)
          +style.padEnd(8)+String(r.ms).padStart(6)+'ms');
      }
    }
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
