// Picking a photo and waiting to land on the size screen. Every phase of it,
// with a real phone-sized JPEG, on a mid and a slow device.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', RATE=+(process.argv[3]||4);
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: RATE });
  const r = await pg.evaluate(async ()=>{
    // a 12MP photograph, the size a phone camera actually produces
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(0.5,'#8a7f6e'); gr.addColorStop(1,'#111');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<60000;i++){ g.fillStyle='rgba(255,255,255,.35)'; g.fillRect(rnd()*W,rnd()*H,3,3); }
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    const file=new File([blob],'camera.jpg',{type:'image/jpeg'});
    const out={ fileKB: Math.round(blob.size/1024) };

    // time each phase the way addRef runs them
    const t=(k,p)=>{ const a=performance.now(); return Promise.resolve(p()).then(v=>{
      out[k]=Math.round(performance.now()-a); return v; }); };
    const th = await t('1 thumbOf', ()=>thumbOf(file,false));
    const gid = await t('2 galAdd (writes the original to disk)',
      ()=>galAdd({ts:Date.now(), name:'camera.jpg', thumb:th, blob:file}));
    await t('3 renderGallery', ()=>renderGallery());
    const a=performance.now();
    openPhoto(file,gid);
    for (let i=0;i<6000;i++){
      if (document.querySelector('#scrFormat.on') && photo && photo.width) break;
      await new Promise(r=>setTimeout(r,20));
    }
    out['4 openPhoto -> size screen'] = Math.round(performance.now()-a);
    out.total = out['1 thumbOf']+out['2 galAdd (writes the original to disk)']
              +out['3 renderGallery']+out['4 openPhoto -> size screen'];
    out.photo = photo? photo.width+'x'+photo.height : '-';
    return out;
  });
  console.log('CPU x'+RATE+'   '+r.fileKB+'KB jpeg, 4032x3024 -> photo '+r.photo);
  for (const k of Object.keys(r)) if (/^\d /.test(k))
    console.log('   '+k.padEnd(38)+String(r[k]).padStart(6)+' ms');
  console.log('   '+'TOTAL before the artist sees anything'.padEnd(38)+String(r.total).padStart(6)+' ms');
  if (errs.length) console.log('   page errors:', errs.slice(0,2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
