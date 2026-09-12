const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  pg.on('pageerror', e => console.log('PAGEERROR', e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => document.querySelectorAll('#gallery .gitem').length >= 2,
                           null, { timeout: 30000 });
  // the boot splash covers everything for its first ~1.4s and swallows
  // a synthetic press that a real finger would never have made yet
  await pg.waitForFunction(() =>
    !document.getElementById('introSplash').classList.contains('on'), null, {timeout:15000});
  await pg.waitForTimeout(300);
  const before = await pg.evaluate(() =>
    [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('before        :', before.join(','));

  // press and hold the first tile, then carry it past the second
  const a = await pg.locator('#gallery .gitem').first().boundingBox();
  const b = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  await pg.mouse.move(a.x + a.width/2, a.y + a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(600);                       // the hold
  const lifted = await pg.evaluate(() =>
    !!document.querySelector('#gallery .gitem.dragging') &&
    !!document.querySelector('#gallery .gph'));
  console.log('lifted        :', lifted);
  for (let i=1;i<=8;i++)
    await pg.mouse.move(a.x + a.width/2 + (b.x - a.x) * i/8 + 20, a.y + a.height/2);
  await pg.waitForTimeout(120);
  await pg.mouse.up();
  await pg.waitForTimeout(400);

  const after = await pg.evaluate(() =>
    [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('after         :', after.join(','));
  console.log('order changed :', before.join()!==after.join());
  const saved = await pg.evaluate(async () => {
    const all = await galAll();
    return all.filter(r=>r.ord!=null).map(r=>r.id+':'+r.ord).sort().join(' ');
  });
  console.log('saved order   :', saved || 'NOTHING SAVED');
  const stuck = await pg.evaluate(() =>
    document.documentElement.classList.contains('dragging') ||
    !!document.querySelector('.gitem.dragging') || !!document.querySelector('.gph'));
  console.log('cleaned up    :', !stuck);
  // a plain tap must still open the project
  await pg.locator('#gallery .gitem').first().click();
  await pg.waitForTimeout(900);
  console.log('tap still opens:', await pg.evaluate(() =>
    !document.getElementById('scrUpload').classList.contains('on')));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
