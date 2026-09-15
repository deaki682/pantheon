// The editor now picks its resampling filter by how much it is actually
// reducing. At every zoom and in both modes the picture must be the same.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', TAG=process.argv[3]||'now', OUT=process.argv[4]||'.';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof edPaint==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; show('scrFormat');
    await new Promise(r=>setTimeout(r,800));
  });
  const fs=require('fs');
  for (const mode of ['tone','crop']){
    for (const z of [1, 1.5, 2.5, 4, 8]){
      const png = await pg.evaluate(async ([mode,z])=>{
        if (!ED.on) await edOpenFor(mode); else { ED.mode=mode; }
        await new Promise(r=>setTimeout(r,250));
        ED.z.s=z; ED.z.x=0; ED.z.y=0;
        // a real adjustment, so the toned path is exercised too
        ED.R.exp=12; ED.R.con=118; ED.R.shp=20;
        edPaint();
        await new Promise(r=>setTimeout(r,200));
        return $('edCv').toDataURL('image/png');
      }, [mode,z]);
      fs.writeFileSync(OUT+'/ed_'+mode+'_z'+z+'_'+TAG+'.png', Buffer.from(png.split(',')[1],'base64'));
    }
  }
  if (errs.length) console.log('page errors:', errs.slice(0,3));
  console.log(TAG+': 10 editor frames');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
