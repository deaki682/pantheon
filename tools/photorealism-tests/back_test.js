const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof window.__backStep==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  console.log(await pg.evaluate(async ()=>{
    const out={};
    out.homeNoOverlay = window.__backStep();                 // must be 'exit'
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    out.formatScreen = window.__backStep();                  // must step up, not exit
    out.screenAfter = [...document.querySelectorAll('.screen.on')].map(e=>e.id).join(',');
    // gear panel open on the home screen: back closes the panel, not the app
    show('scrUpload'); await new Promise(r=>setTimeout(r,200));
    $('gearModal').style.display='flex';
    out.gearOpen = window.__backStep();
    out.gearClosedAfter = getComputedStyle($('gearModal')).display==='none';
    out.homeAgain = window.__backStep();                     // back to 'exit'
    return out;
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
