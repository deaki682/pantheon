// Nothing the user must read or press may sit under the ad strip, at ANY
// strip height. The shell measures the real one; 76 was only ever a guess.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  let bad = 0;
  for (const AD of [76, 104, 132]) {          // default, large font, largest
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('lang','en'); });
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
    await pg.waitForFunction(()=>typeof window.__adH==='function', null, {timeout:20000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'), null, {timeout:20000});
    await pg.waitForTimeout(900);
    await pg.evaluate((AD)=>{ window.__adOn(true); window.__adH(AD); }, AD);
    await pg.waitForTimeout(500);            // .screen transitions its padding
    const r = await pg.evaluate((AD)=>{
      const floor = innerHeight - AD;
      const out=[];
      // every modal panel, opened one at a time
      const modals=['introModal','gearModal','a11yModal','accModal','shModal','gridModal',
                    'setModal','refModal','dlModal','arModal','modeModal','delModal','gsdModal','dgModal'];
      for (const id of modals){
        const m=document.getElementById(id); if (!m) continue;
        const prev=m.style.display; m.style.display='flex';
        const p=m.firstElementChild;
        const b=p?p.getBoundingClientRect():null;
        if (b && b.height && b.bottom > floor+0.5) out.push({what:id, over:Math.round(b.bottom-floor)});
        m.style.display=prev;
      }
      // a tip bubble anchored on a LOW target, which is what the tour does
      const low=document.getElementById('calBtn')||document.getElementById('gallery');
      if (typeof tip==='function' && low){
        tip(low.id, 'A tip anchored low on the page, below its target.', {below:true});
        if (TIPSTATE && TIPSTATE.re) TIPSTATE.re();
        const bb=document.getElementById('tourBubble').getBoundingClientRect();
        if (bb.height && bb.bottom > floor+0.5) out.push({what:'tourBubble', over:Math.round(bb.bottom-floor)});
        const x=document.getElementById('tourX').getBoundingClientRect();
        if (x.height && x.bottom > floor+0.5) out.push({what:'tour close button', over:Math.round(x.bottom-floor)});
        tipClose(false);
      }
      // the home screen's own bottom content
      const sc=document.getElementById('scrUpload');
      const pb=parseFloat(getComputedStyle(sc).paddingBottom)||0;
      return { floor, out, reserved:Math.round(pb), adh:getComputedStyle(document.documentElement).getPropertyValue('--adh').trim() };
    }, AD);
    const ok = r.out.length===0 && r.reserved>=AD;
    if (!ok) bad++;
    console.log('strip '+String(AD).padStart(3)+'px -> --adh '+r.adh
      +', screen reserves '+r.reserved+'px  '+(ok?'ok':'FAIL'));
    for (const o of r.out) console.log('      COVERED: '+o.what+' by '+o.over+'px');
    if (errs.length) console.log('      page errors:', errs.slice(0,2));
    await ctx.close();
  }
  console.log(bad===0 ? 'ALL CLEAR' : bad+' height(s) still cover something');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
