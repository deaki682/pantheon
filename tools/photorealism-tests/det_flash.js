// Switching detail levels: record every composite that lands, and at what
// level it was actually drawn. Any 'ultra' between two lower levels is the
// flash of full detail the artist is reporting.
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
    const W=3000,H=2200; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=3; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,3,3); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.94));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(9000);            // let every level finish cooking
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await pg.evaluate(()=>{
    window.__log=[];
    const o=window.compositeCv;
    window.compositeCv=function(...a){
      const r=o.apply(this,a);
      window.__log.push({want:DETAIL, drew:DET_SHOWN,
        keyOk:(DET.key===fkey()), have:!!(DET.lv&&DET.lv[DETAIL]),
        cooked:Object.keys(DET.lv||{}).join('+'), busy:DET.busy||'-',
        plain:(typeof plainRef==='function'?plainRef():null),
        shown:((typeof plainRef==='function'&&plainRef())?'photograph':DET_SHOWN),
        t:Math.round(performance.now())});
      return r;
    };
  });
  const seq=['ultra','fine','hyper','fine','ultra','hyper'];
  for (const d of seq){
    await pg.evaluate(async (lv)=>{
      window.__log=[];
      DETAIL=lv; COMP.sig=null; viewRepaint();
      // let any background cook land and repaint
      for (let i=0;i<60;i++){ await new Promise(r=>requestAnimationFrame(r)); }
    }, d);
    const log = await pg.evaluate(()=>window.__log);
    // collapse repeats: what the artist actually sees, in order
    const seen=[]; for (const e of log) if (seen[seen.length-1]!==e.shown) seen.push(e.shown);
    // a flash is full detail appearing BETWEEN the old view and the new one
    const flashed = seen.length>2 && seen.slice(1,-1).some(v=>v==='ultra'||v==='photograph');
    console.log('  switch to '+d.padEnd(6)+'  sees: '+seen.join(' -> ').padEnd(34)
      +(flashed?'FLASH of full detail':''));
  }
  // what is cooked, and what the stand-in would give
  const st = await pg.evaluate(()=>({
    cooked:Object.keys(DET.lv||{}), keyMatch: DET.key===fkey(), shown:DET_SHOWN }));
  console.log('  cooked levels: '+st.cooked.join(',')+'   key matches: '+st.keyMatch);
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
