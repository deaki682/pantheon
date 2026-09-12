const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
async function run(br, tag, shell) {
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
    const n = route.request().url().split('/').pop();
    try { route.fulfill({status:200, contentType:'text/javascript', body: fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ route.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.addInitScript((sh) => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    window.__calls = [];
    if (sh === 'android-new')
      window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){},
                            authGoogle(){ __calls.push('native authGoogle'); } };
    if (sh === 'android-old')
      window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){} };
  }, shell);
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2300);
  const vis = await pg.evaluate(() => ({
    home: getComputedStyle(document.getElementById('accHome')).display,
    row:  getComputedStyle(document.getElementById('accBtn')).display,
  }));
  let detail = '';
  if (vis.row !== 'none') {
    await pg.evaluate(() => accOpen());
    await pg.waitForTimeout(500);
    detail = await pg.evaluate(() => 'google=' + getComputedStyle(document.getElementById('accGoogle')).display
      + ' apple=' + getComputedStyle(document.getElementById('accApple')).display);
    await pg.locator('#accGoogle').click();
    await pg.waitForTimeout(900);
    detail += ' | calls=[' + (await pg.evaluate(() => __calls.join(','))) + ']';
    // the shell reporting a cancel must leave no error on screen
    await pg.evaluate(() => window.__authFail(''));
    detail += ' cancelState="' + (await pg.evaluate(() => document.getElementById('accState').textContent)) + '"';
  }
  console.log(tag.padEnd(12), 'homePill=' + vis.home, 'gearRow=' + vis.row, detail, errs[0] || '');
  await ctx.close();
}
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  await run(br, 'browser', null);
  await run(br, 'android-new', 'android-new');
  await run(br, 'android-old', 'android-old');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
