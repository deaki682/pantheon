const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
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
    const out={}; const T=async(n,f)=>{ const a=performance.now(); const v=await f(); out[n]=Math.round(performance.now()-a); return v; };
    const r=await T('galGet', ()=>galGet(galActive));
    const src=await T('openSrc', ()=>openSrc(galActive, r.blob));
    const i=await T('decode', ()=>blobImage(src||r.blob));
    out.decoded=[i.width,i.height];
    const CAP=refCap(); const sc=Math.min(1,CAP/Math.max(i.width,i.height));
    const cw=Math.round(i.width*sc), ch=Math.round(i.height*sc);
    out.canvas=[cw,ch];
    const c=document.createElement('canvas'); c.width=cw; c.height=ch;
    const g=c.getContext('2d');
    await T('flatten+draw', ()=>{ flatten(g,cw,ch); g.drawImage(i,0,0,cw,ch); });
    await T('greyscale pass', ()=>{ g.filter='grayscale(1)'; g.drawImage(c,0,0); g.filter='none'; });
    await T('forceGray', ()=>{ forceGray(c); });
    await T('edOpen', ()=>{ edOpen(c, galActive, 'tone'); });
    await T('edBuildPre', ()=>{ edBuildPre(); });
    await T('edRender', ()=>{ edRender(); });
    out.pre=[ED.pre.width, ED.pre.height];
    return out;
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
