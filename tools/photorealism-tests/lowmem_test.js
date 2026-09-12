// a 4GB phone: deviceMemory=4 → cap 3072, world ≤9MP, a 16MP import opens
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:360,height:780}, deviceScaleFactor:2 });
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 4 });
    try{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); }catch(e){}
  });
  const page = await ctx.newPage();
  const errs=[]; page.on('pageerror', e=>errs.push(String(e)));
  await page.goto('http://127.0.0.1:8899/index.html', { waitUntil:'domcontentloaded' });
  await page.waitForFunction(() => typeof refCap === 'function' && typeof addRef === 'function');
  const cap = await page.evaluate(() => refCap());
  console.log('cap', cap, cap===3072 ? 'ok' : 'FAIL');
  // a 4800x3600 jpeg made in-page (16MP), imported through addRef
  const r = await page.evaluate(async () => {
    const c=document.createElement('canvas'); c.width=4800; c.height=3600;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,4800,3600);
    gr.addColorStop(0,'#f00'); gr.addColorStop(1,'#00f'); g.fillStyle=gr; g.fillRect(0,0,4800,3600);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.9));
    const f=new File([blob],'big.jpg',{type:'image/jpeg'});
    const t0=performance.now();
    await addRef(f, true);
    for (let i=0;i<300;i++){ if (photo && photo.width) break; await new Promise(r=>setTimeout(r,100)); }
    const recs=await galAll(); const rec=recs.find(x=>x.name==='big.jpg');
    const th = rec && rec.thumb;
    return { ms:Math.round(performance.now()-t0), pw:photo&&photo.width, ph:photo&&photo.height,
      screen:[...document.querySelectorAll('.screen.on')].map(e=>e.id).join(','),
      thumb: th instanceof Blob ? th.size : (th||'').length };
  });
  console.log(JSON.stringify(r), r.pw===3072 && r.ph===2304 && r.screen==='scrFormat' ? 'ok' : 'FAIL');
  // shrunk stored copy lands async
  await page.waitForFunction(async () => { const rs=await galAll(); const x=rs.find(q=>q.name==='big.jpg'); return x && x.blob && x.blob.size < 2.5e6; }, null, {timeout:15000}).catch(()=>console.log('stored copy not shrunk (FAIL)'));
  await page.evaluate(() => { $('widthIn').value='30'; $('fmtGo').click(); });
  await page.waitForFunction(() => document.querySelector('#scrMain.on') && GRID_READY, null, {timeout:60000});
  const wm = await page.evaluate(() => (WORLD.w*WORLD.h));
  console.log('world px', wm, wm<=9.1e6 ? 'ok' : 'note');
  console.log('page errors', errs.length, errs.slice(0,3));
  await br.close();
})().catch(e=>{ console.error(e); process.exit(1); });
