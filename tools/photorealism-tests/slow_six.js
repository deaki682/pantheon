// The six over budget, broken into their parts.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=3; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_ON=true; GRID_COL='auto'; GRID_LAB=false;
  });
  await pg.waitForTimeout(8000);
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await pg.evaluate(()=>{
    window.__T={};
    const wrap=n=>{ const o=window[n]; if(typeof o!=='function')return;
      window[n]=function(...a){ const t=performance.now();
        try{ return o.apply(this,a); } finally{ window.__T[n]=(window.__T[n]||0)+(performance.now()-t); } }; };
    for (const n of ['fmtGridLayer','punchPaint','punchWorld','punchWorldMap',
                     'drawGrid','drawEdgeLabs','drawCircs','applyView','fmtPreview',
                     'compositeCv','viewRepaint','paintWorld','applyGrid']) wrap(n);
  });
  const step = async (label, code) => {
    const r = await pg.evaluate(async (code)=>{
      window.__T={};
      const t0=performance.now();
      await (new Function('return (async()=>{'+code+'})()'))();
      const sync=performance.now()-t0;
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const total=performance.now()-t0;
      const T={}; for (const k in window.__T) if (window.__T[k]>=3) T[k]=Math.round(window.__T[k]);
      return {sync:Math.round(sync), total:Math.round(total), T};
    }, code);
    const parts=Object.entries(r.T).sort((a,b)=>b[1]-a[1]).map(([k,v])=>k+' '+v).join('  ');
    console.log('  '+label.padEnd(26)+String(r.total).padStart(4)+'ms (sync '+String(r.sync).padStart(3)+')   '+parts);
  };
  await step('open the size screen',   "show('scrFormat'); fmtPreview();");
  await step('crop: diagonal grid',    "GRID_STYLE='diag'; FMT_GRID=null; fmtPreview();");
  await step('change the grid style',  "gsSet(GRID_STYLE==='diag'?'sq':'diag');");
  await step('back to the drawing',    "show('scrMain'); applyView();");
  await step('open then leave compare',"$('compareBtn')&&$('compareBtn').click(); await new Promise(r=>setTimeout(r,700)); show('scrMain');");
  await step('close the edit window',  "await edOpenFor('tone'); await new Promise(r=>setTimeout(r,400)); edClose(false);");
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
