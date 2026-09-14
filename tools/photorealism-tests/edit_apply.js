// Opening must be fast, and Done must still produce a full-resolution result.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof edOpenFor==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
  });
  const cdp = await ctx.newCDPSession(pg); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  console.log(await pg.evaluate(async ()=>{
    const out={};
    const t0=performance.now();
    await edOpenFor('tone');
    for (let i=0;i<400;i++){ if (ED.on && ED.pre) break; await new Promise(r=>setTimeout(r,25)); }
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    out.openMs=Math.round(performance.now()-t0);
    out.pre=[ED.pre.width, ED.pre.height];
    out.builtFullAtOpen = !!ED.orig;
    // a real adjustment, then Done
    ED.R.con=25; ED.R.exp=8; edPaint();
    await new Promise(r=>setTimeout(r,200));
    const before=[photo.width,photo.height];
    // the DIMENSIONS are unchanged whether the edit applied or was thrown
    // away, so sample the pixels too - that gap let a release ship where
    // Done silently discarded every edit
    const samp=()=>{ const s1=document.createElement('canvas'); s1.width=s1.height=16;
      const q=s1.getContext('2d',{willReadFrequently:true});
      q.drawImage(photo,0,0,16,16);
      return [...q.getImageData(0,0,16,16).data].filter((_,i)=>i%4===0); };
    const pxBefore=samp();
    const t1=performance.now();
    edClose(true);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on') && photo) break; await new Promise(r=>setTimeout(r,25)); }
    await new Promise(r=>setTimeout(r,400));
    out.applyMs=Math.round(performance.now()-t1);
    out.photoBefore=before; out.photoAfter=[photo.width,photo.height];
    out.fullResult = photo.width===before[0] && photo.height===before[1];
    // and the edit actually changed the picture
    const c=document.createElement('canvas'); c.width=c.height=32;
    c.getContext('2d').drawImage(photo,0,0,32,32);
    const d=c.getContext('2d').getImageData(0,0,32,32).data;
    out.meanLevel=Math.round([...d].filter((_,i)=>i%4===0).reduce((a,b)=>a+b,0)/1024);
    // a black-and-white project must come back grey, and opaque
    let colourLeak=0, transparent=0;
    for (let i=0;i<d.length;i+=4){
      if (Math.abs(d[i]-d[i+1])>4 || Math.abs(d[i+1]-d[i+2])>4) colourLeak++;
      if (d[i+3]<250) transparent++;
    }
    out.colourLeakPx=colourLeak; out.transparentPx=transparent;
    const pxAfter=samp();
    out.samplesMoved = pxBefore.filter((v,i)=>v!==pxAfter[i]).length+'/'+pxBefore.length;
    out.applyVerdict = pxBefore.every((v,i)=>v===pxAfter[i])
      ? 'FAIL the edit was discarded - photo pixels unchanged after Done'
      : 'ok Done applied the edit';
    return out;
  }));
  console.log('page errors:', errs.length?errs.slice(0,3):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
