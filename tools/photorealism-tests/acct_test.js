const { chromium } = require('playwright-core');
const OUT = __dirname + '/';
async function shot(br, tag, w, h, native) {
  const ctx = await br.newContext({ viewport:{width:w,height:h}, reducedMotion:'no-preference',
    deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  pg.on('console', m => { if (m.type()==='error') errs.push('CONSOLE ' + m.text().slice(0,140)); });
  await pg.addInitScript((nat) => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    localStorage.setItem('lang','en');
    if (nat) window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){} };
  }, native);
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2400);
  const vis = await pg.evaluate(() => getComputedStyle(document.getElementById('accBtn')).display);
  let opened = 'n/a';
  if (vis !== 'none') {
    await pg.locator('#setBtn, #gearBtn').first().click().catch(()=>{});
    await pg.waitForTimeout(500);
    await pg.locator('#accBtn').click();
    await pg.waitForTimeout(1800);
    opened = await pg.evaluate(() => {
      const m = document.getElementById('accModal');
      const p = m.querySelector('#accPanel').getBoundingClientRect();
      return getComputedStyle(m).display + ' panel=' + Math.round(p.width) + 'x' + Math.round(p.height)
        + ' state="' + document.getElementById('accState').textContent + '"'
        + ' out=' + getComputedStyle(document.getElementById('accOut')).display;
    });
    await pg.screenshot({ path: OUT + 'acct-' + tag + '.png' });
  }
  console.log(tag.padEnd(10), 'accBtn=' + vis, '|', opened);
  errs.slice(0,4).forEach(e => console.log('   ', e));
  await ctx.close();
}
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  await shot(br, 'browser', 390, 844, false);   // PWA: the row should appear
  await shot(br, 'shellold', 390, 844, true);   // native shell, no auth bridge: hidden
  await shot(br, 'tablet', 1280, 800, false);
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
