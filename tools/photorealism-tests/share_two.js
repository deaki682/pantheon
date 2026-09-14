const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAKklEQVRYhe3OMQEAAAjDMMC/56EDvlRA0zbJzQIAAAAAAAAAAAAAAHwsHhIAAeTbFpMAAAAASUVORK5CYII=','base64');
  for (const p of ['s1','s2']) await pg.route('**/__cap/'+p, r=>r.fulfill({status:200,contentType:'image/png',body:png}));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof window.__shared==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const r = await pg.evaluate(async ()=>{
    await window.__shared('/__cap/s1','image/png','first.png');
    await window.__shared('/__cap/s2','image/png','second.png');
    await new Promise(r=>setTimeout(r,400));
    $('modeBW').click();
    for (let i=0;i<200;i++){ if ((await galAll()).some(x=>x.name==='first.png')) break; await new Promise(r=>setTimeout(r,60)); }
    await new Promise(r=>setTimeout(r,900));
    const reopened = getComputedStyle($('modeModal')).display!=='none';
    if (reopened) $('modeBW').click();
    for (let i=0;i<200;i++){ if ((await galAll()).some(x=>x.name==='second.png')) break; await new Promise(r=>setTimeout(r,60)); }
    const names=(await galAll()).map(x=>x.name);
    return { chooserReopened:reopened, hasFirst:names.includes('first.png'), hasSecond:names.includes('second.png') };
  });
  console.log(JSON.stringify(r), r.hasFirst && r.hasSecond ? 'ok (both kept)' : 'FAIL');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
