// First open vs reopen, reported separately - the cache only helps the second.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
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
  const times=[];
  for (let k=0;k<6;k++){
    const r = await pg.evaluate(async ()=>{
      const t0=performance.now();
      await edOpenFor(k=>k);
      const sync=performance.now()-t0;
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const total=performance.now()-t0;
      const cached = !!(typeof PRE_CACHE!=='undefined' && PRE_CACHE && PRE_CACHE.cv===ED.pre);
      const dims=ED.pre.width+'x'+ED.pre.height;
      edClose(false);
      return {sync:Math.round(sync), total:Math.round(total), cached, dims};
    });
    times.push(r);
    await pg.waitForTimeout(500);
  }
  times.forEach((r,i)=>console.log('  open #'+(i+1)+'  '+String(r.total).padStart(4)+'ms  (sync '
    +String(r.sync).padStart(3)+')   preview '+r.dims+'   '+(r.cached?'from cache':'built')));
  const re=times.slice(1).map(r=>r.total).sort((a,b)=>a-b);
  console.log('  first open '+times[0].total+'ms   reopen median '+re[Math.floor(re.length/2)]+'ms');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
