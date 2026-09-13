// The review: the bottom ad strip covers the lower part of a panel.
// Device: Galaxy S21 FE 5G (1080x2340 @420dpi -> ~411x891 css), Android 16.
const { chromium } = require('playwright-core');
const AD = 76;                       // what the page reserves, in css px
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const scale of ['default','large']){
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript(([sc]) => {
      localStorage.setItem('lang','en');
      if (sc==='large'){ localStorage.setItem('uiScale','L'); localStorage.setItem('hiCon','1'); }
    }, [scale]);
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
    await pg.waitForFunction(()=>document.getElementById('introModal'), null, {timeout:20000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'), null, {timeout:20000});
    await pg.waitForTimeout(900);
    const r = await pg.evaluate((AD)=>{
      document.documentElement.classList.add('adOn');          // the strip is up
      const out=[];
      const modals=['introModal','gearModal','a11yModal','accModal','shModal',
                    'gridModal','setModal','refModal','dlModal','arModal','modeModal','delModal'];
      const H=innerHeight, lim=H-AD;
      for (const id of modals){
        const m=document.getElementById(id); if (!m) continue;
        const prev=m.style.display; m.style.display='flex';
        const panel=m.querySelector('div,span'); 
        const p=m.firstElementChild;
        const b=p?p.getBoundingClientRect():null;
        if (b && b.height) out.push({ id, bottom:Math.round(b.bottom), over:Math.round(b.bottom-lim) });
        m.style.display=prev;
      }
      return { H, lim, out };
    }, AD);
    console.log('--- '+scale+' (viewport '+r.H+'px, ad covers below '+r.lim+')');
    for (const o of r.out)
      console.log('   '+(o.over>0?'COVERED':'ok     ')+'  '+o.id.padEnd(12)+' bottom '+o.bottom+(o.over>0?('  ('+o.over+'px under the ad)'):''));
    await ctx.close();
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
