const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:844,height:390}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof tip==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.waitForTimeout(600);
  console.log(await pg.evaluate(async ()=>{
    tip('calBtn','I find it helpful to keep my reference true-to-life, and you can match this ruler to a real one to calibrate the program',{below:true});
    await new Promise(r=>setTimeout(r,900));
    const bub=document.getElementById('tourBubble');
    const t=document.getElementById('calBtn');
    const r=t.getBoundingClientRect(), b=bub.getBoundingClientRect();
    const bh=bub.offsetHeight, bw=bub.offsetWidth;
    const FLOOR=innerHeight-adPx();
    const roomBelow = FLOOR-10-bh >= r.bottom+16;
    const above=(!true || !roomBelow) && r.top-bh-16>=10;
    return { innerH:innerHeight, innerW:innerWidth, adPx:adPx(),
      target:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)],
      bub:[Math.round(b.left),Math.round(b.top),Math.round(bw),Math.round(bh)],
      FLOOR, roomBelow, above,
      wouldBe: above ? r.top-bh-16 : Math.max(10, Math.min(FLOOR-bh-10, r.bottom+16)),
      styleTop: bub.style.top, side: innerWidth>innerHeight && (r.left>innerWidth*0.8 || r.right<innerWidth*0.2) };
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
