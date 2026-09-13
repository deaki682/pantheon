// Dylan's hypothesis: the grid can't keep up on a slow phone.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const rate of [1, 6, 12]) {
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ Object.defineProperty(navigator,'deviceMemory',{get:()=>4});
      localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:25000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
    await pg.evaluate(async ()=>{
      const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
      for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
      if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
      for (let i=0;i<2000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    });
    const cdp = await ctx.newCDPSession(pg);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate });
    // time one grid rasterisation, and watch how far the grid trails the
    // image through a fast pinch-zoom
    const r = await pg.evaluate(async ()=>{
      const t0=performance.now(); drawGrid(); const one=performance.now()-t0;
      const trail=[];
      GESTURE.active=true;
      const r=$('viewport').getBoundingClientRect();
      for (let i=0;i<24;i++){
        view.s*=1.09;
        view.x=r.width/2-(r.width/2-view.x)*1.09;
        view.y=r.height/2-(r.height/2-view.y)*1.09;
        applyView();
        // the grid's own scale this frame: its ride transform, or its bake
        const m=/scale\(([\d.]+)\)/.exec($('gridCv').style.transform||'');
        const gs=(GRID_DRAWN?GRID_DRAWN.s:view.s)*(m?+m[1]:1);
        trail.push(+(Math.abs(gs-view.s)/view.s*100).toFixed(2));
        await new Promise(r=>requestAnimationFrame(r));
      }
      GESTURE.active=false; const t1=performance.now(); applyView();
      const settle=performance.now()-t1;
      return { one:Math.round(one), settle:Math.round(settle),
        worstTrailPct:Math.max(...trail), lastTrailPct:trail[trail.length-1] };
    });
    console.log('CPU x'+String(rate).padStart(2)+'  one grid redraw '+String(r.one).padStart(4)
      +'ms   redraw at rest '+String(r.settle).padStart(4)+'ms   grid vs image mismatch during the pinch: worst '
      +r.worstTrailPct+'%');
    await ctx.close();
  }
  console.log('(x1 = a fast desktop, x6-x12 ~ an entry-level phone like the Spark 10C)');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
