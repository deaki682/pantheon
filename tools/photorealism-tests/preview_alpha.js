// The grid preview must not decode the uncapped original, and a cutout PNG
// must sit on paper in the preview and in an exported comparison.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof gsdSnap==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  console.log(await pg.evaluate(async ()=>{
    const out={};
    // 1) a big photo: the preview must decode the capped copy, not the original
    const W=8000,H=6000; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<120000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.88));
    await addRef(new File([b],'big.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    await new Promise(r=>setTimeout(r,1500));
    const rec=(await galAll()).find(x=>x.name==='big.jpg');
    out.stored=[rec.blob.size, rec.work?rec.work.size:0, rec.workW||0];
    // gsdLastRefSrc returns { src, gray, w, h, cell }
    const L=await gsdLastRefSrc();
    out.previewDecoded = L ? [L.w, L.h] : null;
    out.cappedNotOriginal = !!L && L.w<=refCap() && L.h<=refCap();
    // 2) a cutout PNG through the preview snapshot and the compare capture
    const p=document.createElement('canvas'); p.width=p.height=600;
    const pg2=p.getContext('2d'); pg2.fillStyle='#c98'; pg2.beginPath(); pg2.arc(300,300,180,0,7); pg2.fill();
    const png=await new Promise(r=>p.toBlob(r,'image/png'));
    const im=await createImageBitmap(png);
    const snap=gsdSnap(im,false);
    const sd=snap.getContext('2d').getImageData(2,2,1,1).data;
    out.previewCorner=[sd[0],sd[1],sd[2],sd[3]];
    await cmpSetPhoto(png);
    const cd=CMP.raw.getContext('2d').getImageData(2,2,1,1).data;
    out.captureCorner=[cd[0],cd[1],cd[2],cd[3]];
    out.bothOnPaper = sd[3]===255 && sd[0]>240 && cd[3]===255 && cd[0]>240;
    return out;
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
