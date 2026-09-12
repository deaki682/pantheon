const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
let pass=0, fail=0;
const ok=(n,c,d)=>{ (c?pass++:fail++); console.log((c?'  ok   ':'  FAIL ')+n+(d?'  '+d:'')); };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', r => {
    const n=r.request().url().split('/').pop();
    try{ r.fulfill({status:200, contentType:'text/javascript', body:fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ r.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  const boot = async () => {
    await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
    await pg.waitForFunction(() => typeof accPaint === 'function', null, { timeout: 20000 });
  };
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const n of ['starter-guy.jpg','starter-soft.jpg','starter-wet-c.jpg','starter-freckles-c.jpg'])
      localStorage.setItem('seed|'+n,'1');
  });
  await boot();

  await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE.user = { uid:'u1', email:'d@e.com' };
    globalThis.__FAKE.cbs.forEach(c => c(globalThis.__FAKE.user));
  });
  ok('signed in', await pg.evaluate(() => !!ACC_USER));
  ok('remembered on the device', await pg.evaluate(() => localStorage.getItem('acct')==='1'));

  // an app update = a fresh launch. The in-memory fake loses the session
  // entirely, which is the WORST case: a real Firebase would restore it.
  await boot();
  const r = await pg.evaluate(() => ({
    remembered: localStorage.getItem('acct')==='1',
    restoring: ACC_RESTORING,
    pill: getComputedStyle(document.getElementById('accHome')).display,
    panelSaysIn: (accPaint(), getComputedStyle(document.getElementById('accIn')).display !== 'none'),
    mail: document.getElementById('accMail').textContent,
  }));
  ok('still remembered after relaunch', r.remembered);
  ok('does not beg for sign-in', r.pill === 'none', 'pill=' + r.pill);
  ok('panel shows the account', r.panelSaysIn, r.mail);

  // a transient null from Firebase must not evict anybody
  const t = await pg.evaluate(async () => {
    await fbLoad(); await accWatch();
    globalThis.__FAKE.cbs.forEach(c => c(null));       // a dropped connection
    return { remembered: localStorage.getItem('acct')==='1',
             pill: getComputedStyle(document.getElementById('accHome')).display };
  });
  ok('a dropped connection does not sign you out', t.remembered && t.pill === 'none');

  // but a deliberate sign-out does
  const d = await pg.evaluate(async () => {
    await accSignOut();
    return { remembered: localStorage.getItem('acct')==='1',
             pill: getComputedStyle(document.getElementById('accHome')).display };
  });
  ok('signing out actually signs out', !d.remembered && d.pill !== 'none');

  await br.close();
  console.log((fail?'FAILED '+fail+' of ':'all ')+(pass+fail)+' checks');
  process.exit(fail?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
