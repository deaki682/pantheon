// 18ms of script then ~80ms before the frame lands. Bisect it: show the
// screen, sync the controls, build the preview, render - each followed by a
// forced frame, so the browser's layout/paint is attributed to a step.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
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
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const out = await pg.evaluate(async ()=>{
    const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    const step=async fn=>{ const t=performance.now(); fn(); const s=performance.now()-t;
      await frame(); return [Math.round(s), Math.round(performance.now()-t)]; };
    const res={};
    const sliders=document.querySelectorAll('input[type=range]').length;
    const inEditor=document.querySelectorAll('#scrEdit input[type=range]').length;
    res.__sliders=sliders+' in the app, '+inEditor+' in the editor';
    // set ED up by hand so each piece can be timed on its own
    ED.on=true; ED.orig=photo; ED.gid=galActive; ED.mode='tone';
    ED.colr=isColor(galActive); ED.z={s:1,x:0,y:0}; ED.showOrig=false;
    ED.R={...EDIT_DEF};
    res.show      = await step(()=>show('scrEdit'));
    res.edSync    = await step(()=>edSync());
    res.slFillAll = await step(()=>slFillAll());
    res.edBuildPre= await step(()=>edBuildPre());
    res.edRender  = await step(()=>edRender());
    res.edRender2 = await step(()=>edRender());          // warm
    const cv=document.getElementById('edCv');
    res.__cv=cv.width+'x'+cv.height;
    res.__nodes=document.querySelectorAll('#scrEdit *').length+' nodes in #scrEdit';
    edClose(false);
    return res;
  });
  for (const [k,v] of Object.entries(out)){
    if (k.startsWith('__')) { console.log('  '+k.slice(2).padEnd(11)+v); continue; }
    console.log('  '+k.padEnd(11)+'script '+String(v[0]).padStart(4)+'ms   to frame '+String(v[1]).padStart(4)+'ms');
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
