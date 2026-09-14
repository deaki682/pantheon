// Across hardware: several CPU levels, a low-memory device, and an engine
// with NO canvas filters at all (an older WebView) - where the grid must
// fall back to the inverting blend rather than come out solid white.
const { chromium } = require('playwright-core');
(async () => {
  const rows=[];
  for (const cell of [
      {name:'flagship',      cpu:1,  mem:8, filters:true},
      {name:'mid-range',     cpu:4,  mem:4, filters:true},
      {name:'entry (Spark)', cpu:8,  mem:3, filters:true},
      {name:'very slow',     cpu:12, mem:2, filters:true},
      {name:'old WebView',   cpu:6,  mem:3, filters:false}]){
    const br = await chromium.launch(require('./browser.js'));
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript(([mem,filters])=>{
      localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
      try{ Object.defineProperty(navigator,'deviceMemory',{get:()=>mem,configurable:true}); }catch(e){}
      if (!filters){
        // an engine with no ctx.filter: assignment is simply ignored
        const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'filter');
        try{ Object.defineProperty(CanvasRenderingContext2D.prototype,'filter',
          { get(){ return 'none'; }, set(v){}, configurable:true }); }catch(e){}
      }
    }, [cell.mem, cell.filters]);
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:40000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:40000});
    await pg.evaluate(async ()=>{
      const r=await fetch('starter-soft.jpg'); const b=await r.blob();
      await addRef(new File([b],'s.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<800;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
      for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
      CELLSZ.u='cm'; CELLSZ.v=3; GRID_ON=true; GRID_STYLE='sq'; GRID_COL='auto';
      GRID_OP=0.9; GRID_THK=2;
    });
    await pg.waitForTimeout(9000);
    const cdp = await ctx.newCDPSession(pg);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: cell.cpu });
    const r = await pg.evaluate(async ()=>{
      applyGrid(); drawGrid();
      await new Promise(x=>requestAnimationFrame(()=>requestAnimationFrame(x)));
      const t0=performance.now(); drawGrid();
      await new Promise(x=>requestAnimationFrame(()=>requestAnimationFrame(x)));
      const ms=Math.round(performance.now()-t0);
      // the same redraw with the OLD inverting grid, for comparison
      const keep=CTX_FILTER_OK;
      try{ Object.defineProperty(window,'CTX_FILTER_OK',{value:false,configurable:true}); }catch(e){}
      const t1=performance.now(); drawGrid();
      await new Promise(x=>requestAnimationFrame(()=>requestAnimationFrame(x)));
      const msOld=Math.round(performance.now()-t1);
      try{ Object.defineProperty(window,'CTX_FILTER_OK',{value:keep,configurable:true}); }catch(e){}
      drawGrid();
      const cvv=$('gridCv'), q=cvv.getContext('2d',{willReadFrequently:true});
      const d=q.getImageData(0,0,cvv.width,cvv.height).data;
      let n=0,w=0,b=0;
      for (let i=0;i<d.length;i+=4){ if (d[i+3]<120) continue; n++;
        if (d[i]>200) w++; else if (d[i]<55) b++; }
      return { ms, msOld, filters:CTX_FILTER_OK, punch:punchOn(),
        blend:cvv.style.mixBlendMode||'normal',
        gridPx:n, white:n?Math.round(w/n*100):0, black:n?Math.round(b/n*100):0,
        cap:refCap(), world:WORLD.w+'x'+WORLD.h };
    });
    rows.push([cell, r, errs]);
    await br.close();
  }
  console.log('  device          cpu  mem  filters  mode        blend       new/old redraw  white/black   refCap');
  let bad=0;
  for (const [c,r,errs] of rows){
    const mode = r.punch ? 'per-cell' : 'invert';
    const okMode = c.filters ? r.punch : !r.punch;
    const okLook = c.filters ? (r.black>2 && r.white>2 && r.white<97) : (r.white>60);
    if (!okMode || !okLook || errs.length) bad++;
    console.log('  '+c.name.padEnd(15)+String(c.cpu).padEnd(5)+String(c.mem).padEnd(5)
      +String(r.filters).padEnd(9)+mode.padEnd(12)+String(r.blend).padEnd(12)
      +String(r.ms+'/'+r.msOld+'ms').padEnd(14)+(r.white+'% / '+r.black+'%').padEnd(14)+r.cap
      +(okMode&&okLook?'':'   <-- WRONG')+(errs.length?('  ERR '+errs[0].slice(0,40)):''));
  }
  console.log('  '+(bad?('FAIL '+bad+' configurations wrong'):'every configuration renders correctly'));
})().catch(e=>{console.error(e);process.exit(1)});
