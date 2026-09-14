// A real drag on the crop preview: how many times does fmtPreview() run,
// and how many frames actually painted? Work done beyond one-per-frame is
// thrown away, and it keeps the main thread from ever yielding.
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
    CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_ON=true; GRID_LAB=false; GRID_SUB=false;
    FMT_ZOOM=2.2; fmtPreview();
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  for (const style of ['sq','diag']){
    await pg.evaluate(s=>{
      GRID_STYLE=s; FMT_ZOOM=2.2; FMT_OFF.x=0.5; FMT_OFF.y=0.5; fmtPreview();
      window.__n=0; window.__frames=0; window.__busy=0;
      if (!window.__wrapped){                 // wrap ONCE - re-wrapping each
        window.__wrapped=true;                // style double-counted the second
        const o=window.fmtPreview;
        window.fmtPreview=function(...a){ window.__n++; const t=performance.now();
          const r=o.apply(this,a); window.__busy+=performance.now()-t; return r; };
        const tick=()=>{ window.__frames++; requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
      }
    }, style);
    const box = await pg.evaluate(()=>{ const b=$('fmtCanvas').getBoundingClientRect();
      return {x:b.x+b.width/2, y:b.y+b.height/2}; });
    const t0=Date.now();
    await pg.mouse.move(box.x, box.y);
    await pg.mouse.down();
    for (let i=0;i<120;i++){                    // a 120-step drag, as fast as it will go
      await pg.mouse.move(box.x + Math.sin(i/9)*70, box.y + Math.cos(i/11)*50);
    }
    await pg.mouse.up();
    const wall=Date.now()-t0;
    const r = await pg.evaluate(()=>({n:window.__n, frames:window.__frames, busy:Math.round(window.__busy)}));
    console.log('  '+style.padEnd(6)+'drag '+String(wall).padStart(5)+'ms wall   '
      +'fmtPreview x'+String(r.n).padStart(4)+'   frames painted '+String(r.frames).padStart(4)
      +'   main-thread busy '+String(r.busy).padStart(5)+'ms'
      +'   ('+Math.round(r.busy/wall*100)+'% of the drag)');
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
