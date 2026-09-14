// The compare view draws its grid inside a pan/zoom transform, so it cannot
// use the crop preview's cached overlay. Is it actually slow there?
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
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(6000);
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const opened = await pg.evaluate(()=>{ const b=$('compareBtn'); if(!b) return 'no button';
    b.click(); return document.querySelector('#scrCompare.on')?'open':'not open'; });
  await pg.waitForTimeout(1200);
  console.log('  compare: '+opened+'   mode='+await pg.evaluate(()=>CMP&&CMP.mode));
  for (const cell of [2,0.5]){
    for (const style of ['sq','diag','dots']){
      const r = await pg.evaluate(async ([cell,style])=>{
        CELLSZ.u='cm'; CELLSZ.v=cell; GRID_STYLE=style; GRID_ON=true;
        if (typeof cmpRender!=='function') return {err:'no cmpRender'};
        cmpRender();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        const t=[];
        for (let k=0;k<7;k++){
          if (window.CMP && CMP.alpha!==undefined) CMP.alpha=(k%2)?0.35:0.65;
          const a=performance.now(); cmpRender();
          await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
          t.push(performance.now()-a);
        }
        t.sort((x,y)=>x-y); return { ms:Math.round(t[3]) };
      },[cell,style]);
      console.log('  '+String(cell+'cm').padEnd(7)+style.padEnd(7)
        +(r.err? r.err : String(r.ms).padStart(6)+'ms per compare frame'));
    }
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
