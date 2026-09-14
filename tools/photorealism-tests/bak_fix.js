// Backups keep the original; a damaged backup changes nothing.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    window.__noReload=1; });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  pg.on('dialog', d=>d.accept());
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof bakBuild==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  console.log(await pg.evaluate(async ()=>{
    const W=8000,H=6000; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<200000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'orig.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    await new Promise(r=>setTimeout(r,1500));
    const out={};
    const bak=await bakBuild();
    const j=JSON.parse(bak);
    const e=j.refs.find(r=>r.name==='orig.jpg');
    const bb=await (await fetch('data:image/jpeg;base64,'+e.blob)).blob();
    const im=await createImageBitmap(bb);
    out.backedUpDims=[im.width,im.height];
    out.keepsOriginal = im.width===8000;
    // now a DAMAGED backup: it must change nothing
    const before=(await galAll()).map(r=>r.name).sort();
    const bad=JSON.parse(bak);
    bad.refs.push({ name:'broken', ts:Date.now(), per:{}, mime:'image/jpeg', blob:'!!!not base64!!!' });
    let said=''; const rt=window.toast; window.toast=(m)=>{ said=String(m); };
    await bakImport(new File([JSON.stringify(bad)],'b.json',{type:'application/json'}));
    window.toast=rt;
    const after=(await galAll()).map(r=>r.name).sort();
    out.damagedToast=said.slice(0,56);
    out.libraryIntact = before.join('|')===after.join('|');
    out.countBefore=before.length; out.countAfter=after.length;
    return out;
  }));
  console.log('page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
