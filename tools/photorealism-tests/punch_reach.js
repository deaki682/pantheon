// Does punch actually reach every surface now? Count the colouring pass.
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
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,0);
    gr.addColorStop(0,'#000'); gr.addColorStop(1,'#fff'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
    await addRef(new File([b],'ramp.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    CELLSZ.u='cm'; CELLSZ.v=3; GRID_ON=true; GRID_STYLE='sq'; GRID_LAB=true; GRID_LPOS='edge';
    GRID_OP=0.9; GRID_THK=2; GRID_COL='punch';
  });
  await pg.waitForTimeout(7000);
  await pg.evaluate(()=>{
    window.__pl=0;
    const o=window.punchLayer;
    window.punchLayer=function(...a){ window.__pl++; return o.apply(this,a); };
  });
  const run = async (label, code) => {
    const r = await pg.evaluate(async (code)=>{
      window.__pl=0; const errs=[];
      try{ await (new Function('return (async()=>{'+code+'})()'))(); }
      catch(e){ errs.push(String(e).slice(0,70)); }
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      return {n:window.__pl, errs};
    }, code);
    console.log('  '+label.padEnd(28)+(r.n>0?'punched x'+r.n:'NOT PUNCHED')
      +(r.errs.length?('   ERR '+r.errs[0]):''));
    return r.n;
  };
  let ok=0, tot=0;
  const check = async (l,c)=>{ tot++; if (await run(l,c)) ok++; };
  await check('drawing screen',      "applyGrid(); drawGrid();");
  await check('margin labels',       "drawEdgeLabs();");
  await check('crop preview',        "show('scrFormat'); FMT_GRID=null; fmtPreview(); show('scrMain');");
  // the export composer is an inline #expBtn handler, so drive the button -
  // and do NOT await it, or the save dialog blocks the page
  await check('the downloaded file',
    "const b=$('expBtn'); if(b) b.onclick(); await new Promise(r=>setTimeout(r,1200));");
  // the compare view needs a CAPTURED DRAWING to compare against - without
  // one every grid block in it is skipped and nothing could ever punch
  await pg.evaluate(async ()=>{
    const b=$('compareBtn'); if (b) b.click();
    await new Promise(r=>setTimeout(r,900));
    const {w,h}=worldSize();
    const c=document.createElement('canvas'); c.width=w; c.height=h;
    const g=c.getContext('2d');
    const gr=g.createLinearGradient(0,0,w,0);
    gr.addColorStop(0,'#111'); gr.addColorStop(1,'#eee');
    g.fillStyle=gr; g.fillRect(0,0,w,h);
    CMP.img=c; CMP.base=c; CMP.raw=c;
    cmpSize();
    await new Promise(r=>setTimeout(r,200));
  });
  await check('compare, flip',       "CMP.mode='flip'; CMP.showing='ref'; CMP.alpha=0; cmpRender();");
  await check('compare, split',      "CMP.mode='split'; cmpRender();");
  await check('compare export',      "cmpExport && cmpExport();");
  await pg.evaluate(()=>{ document.querySelectorAll('.modal,[id$=Modal]').forEach(m=>{
    try{ m.style.display='none'; }catch(e){} }); }).catch(()=>{});
  console.log('  '+ok+' of '+tot+' surfaces punch');
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
