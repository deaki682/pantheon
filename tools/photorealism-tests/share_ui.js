const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.route('**/__cap/s1', r=>r.fulfill({status:200,contentType:'image/png',
    body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==','base64')}));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof window.__shared==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const r = await pg.evaluate(async ()=>{
    const out={};
    // a share arriving with the settings panel open
    $('gearModal').style.display='flex';
    await window.__shared('/__cap/s1','image/png','from-chrome.png');
    await new Promise(r=>setTimeout(r,400));
    const cs=getComputedStyle($('modeModal')), gs=getComputedStyle($('gearModal'));
    out.chooserVisible = cs.display!=='none';
    out.gearClosed = gs.display==='none';
    const el=document.elementFromPoint(innerWidth/2, innerHeight/2);
    out.topmostIsChooser = !!(el && el.closest && el.closest('#modeModal'));
    // back must dismiss the chooser, not close the app
    out.backStep = window.__backStep();
    out.chooserAfterBack = getComputedStyle($('modeModal')).display!=='none';
    out.modeWithCleared = (typeof MODE_WITH==='undefined') || MODE_WITH===null;
    return out;
  });
  console.log(JSON.stringify(r,null,1));
  console.log('chooser on top      :', r.chooserVisible && r.gearClosed && r.topmostIsChooser ? 'ok':'FAIL');
  console.log('back dismisses it   :', r.backStep==='ok' && !r.chooserAfterBack && r.modeWithCleared ? 'ok':'FAIL');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
