const { chromium } = require('playwright-core');
async function run(br, tag, w, h, native) {
  const ctx = await br.newContext({ viewport:{width:w,height:h}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  await pg.addInitScript((nat) => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    if (nat) window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){}, authGoogle(){} };
  }, native);
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2600);
  const m = await pg.evaluate(() => {
    const r = document.getElementById('titleRule').getBoundingClientRect();
    const p = document.getElementById('accHomeBtn').getBoundingClientRect();
    const first = document.querySelector('#gallery .gitem');
    const g = first ? first.getBoundingClientRect() : null;
    if (!g) return 'no thumbnails yet';
    const above = Math.round(p.top - r.bottom), below = Math.round(g.top - p.bottom);
    return 'ruler->pill=' + above + ' pill->thumb=' + below +
           ' centred=' + (Math.abs(above - below) < 24 ? 'yes' : 'no (off by ' + Math.abs(above-below) + ')');
  });
  console.log(tag.padEnd(12), m);
  await pg.screenshot({ path: __dirname + '/pill-' + tag + '.png' });
  await ctx.close();
}
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  await run(br, 'app', 390, 844, true);
  await run(br, 'web', 390, 844, false);
  await run(br, 'tablet', 1280, 800, true);
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
