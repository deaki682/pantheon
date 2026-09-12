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
  await pg.waitForFunction(() => document.querySelectorAll('#gallery .gitem').length >= 2, null, {timeout:30000});
  await pg.waitForFunction(() => !document.getElementById('introSplash').classList.contains('on'), null, {timeout:15000});
  await pg.waitForTimeout(300);
  const before = await pg.evaluate(() => [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('before         :', before.join(','));
  const w0 = await pg.evaluate(() => document.querySelector('#gallery .gitem').getBoundingClientRect().width);

  const a = await pg.locator('#gallery .gitem').first().boundingBox();
  const b = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  await pg.mouse.move(a.x + a.width/2, a.y + a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(560);                        // the hold
  const lifted = await pg.evaluate(() => ({
    fly: !!document.querySelector('body > .gdrag'),
    ghost: !!document.querySelector('#gallery .gitem.ghosted'),
    reorder: document.getElementById('gallery').classList.contains('reorder'),
    stale: !!document.querySelector('.gph'),
  }));
  console.log('lifted         :', JSON.stringify(lifted),
    lifted.fly && lifted.ghost && lifted.reorder && !lifted.stale ? 'ok' : 'FAIL');
  await pg.waitForTimeout(300);                        // the row draws back
  const w1 = await pg.evaluate(() => document.querySelector('#gallery .gitem').getBoundingClientRect().width);
  console.log('row pulls back :', Math.round(w0)+'px -> '+Math.round(w1)+'px', w1 < w0-14 ? 'ok' : 'FAIL');

  // carry it past the second tile and check the neighbour SLID rather than jumped
  for (let i=1;i<=10;i++){
    await pg.mouse.move(a.x + a.width/2 + (b.x - a.x + 30) * i/10, a.y + a.height/2);
    await pg.waitForTimeout(16);
  }
  await pg.waitForTimeout(140);
  const slid = await pg.evaluate(() => {
    const ks=[...document.querySelectorAll('#gallery .gitem')];
    const moved=ks.filter(k=>!k.classList.contains('ghosted') && /matrix|translate/.test(getComputedStyle(k).transform));
    return { moved:moved.length, hasTransition: moved[0] ? /transform/.test(getComputedStyle(moved[0]).transitionProperty) : false };
  });
  console.log('neighbour slid :', JSON.stringify(slid), slid.moved>0 && slid.hasTransition ? 'ok' : 'FAIL');

  await pg.mouse.up();
  await pg.waitForTimeout(600);
  const after = await pg.evaluate(() => [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('after          :', after.join(','), after[0]===before[1] ? 'ok (moved)' : 'FAIL');
  const clean = await pg.evaluate(async () => {
    const ords = {};
    for (const r of await galAll()) ords[r.id]=r.ord;
    return {
      fly: !!document.querySelector('.gdrag'),
      ghost: !!document.querySelector('.ghosted'),
      reorder: document.getElementById('gallery').classList.contains('reorder'),
      dragging: document.documentElement.classList.contains('dragging'),
      width: Math.round(document.querySelector('#gallery .gitem').getBoundingClientRect().width),
      ords: [...document.querySelectorAll('#gallery .gitem')].map(t=>ords[+t.dataset.gid]),
    };
  });
  console.log('cleaned up     :', JSON.stringify(clean),
    !clean.fly && !clean.ghost && !clean.reorder && !clean.dragging && clean.width===Math.round(w0) ? 'ok' : 'FAIL');
  const asc = clean.ords.every((v,i,arr)=> i===0 || (v??0) >= (arr[i-1]??0));
  console.log('ord persisted  :', asc ? 'ok' : 'FAIL', clean.ords.join(','));

  // a plain tap still opens the project
  await pg.locator('#gallery .gitem').first().click();
  await pg.waitForTimeout(900);
  const opened = await pg.evaluate(() => [...document.querySelectorAll('.screen.on')].map(e=>e.id).join(','));
  console.log('tap still opens:', opened, /scrFormat|scrMain/.test(opened) ? 'ok' : 'FAIL');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
