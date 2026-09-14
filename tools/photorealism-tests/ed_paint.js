// 16ms of script, 150ms of "paint". What is the paint actually doing?
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
  const runs=[];
  for (let k=0;k<5;k++){
    const r = await pg.evaluate(async ()=>{
      const t0=performance.now();
      await edOpenFor('tone');
      const script=performance.now()-t0;
      const f1=await new Promise(r=>requestAnimationFrame(()=>r(performance.now()-t0)));
      const f2=await new Promise(r=>requestAnimationFrame(()=>r(performance.now()-t0)));
      // how long does it take to force the preview's own queued work through?
      const t1=performance.now();
      try{ ED.pre.getContext('2d',{willReadFrequently:true}).getImageData(0,0,1,1); }catch(e){}
      const flushPre=performance.now()-t1;
      const dims = ED.pre.width+'x'+ED.pre.height;
      const cv=document.getElementById('edCv');
      const cvd = cv.width+'x'+cv.height;
      const reused = ED.orig===photo;
      edClose(false);
      return { script:Math.round(script), f1:Math.round(f1), f2:Math.round(f2),
               flushPre:Math.round(flushPre), dims, cvd, reused };
    });
    runs.push(r);
    await pg.waitForTimeout(500);
  }
  const med=a=>{const b=[...a].sort((x,y)=>x-y);return b[2];};
  console.log('  preview '+runs[0].dims+'   editor canvas '+runs[0].cvd
    +'   reused photo: '+runs[0].reused);
  for (const k of ['script','f1','f2','flushPre'])
    console.log('  '+k.padEnd(10)+String(med(runs.map(r=>r[k]))).padStart(5)+'ms   ('
      +runs.map(r=>r[k]).join('/')+')');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
