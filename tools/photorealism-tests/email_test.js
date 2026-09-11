const { chromium } = require('playwright-core');
const fs = require('fs');
const FAKE = __dirname + '/fbfake/';
let pass=0, fail=0;
const ok=(n,c,d)=>{ (c?pass++:fail++); console.log((c?'  ok   ':'  FAIL ')+n+(d?'  '+d:'')); };
async function page(br, shell){
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.route('https://www.gstatic.com/firebasejs/**', r => {
    const n=r.request().url().split('/').pop();
    try{ r.fulfill({status:200, contentType:'text/javascript', body:fs.readFileSync(FAKE+n,'utf8')}); }
    catch(e){ r.fulfill({status:404, body:''}); }
  });
  const pg = await ctx.newPage();
  await pg.addInitScript((sh) => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
    for (const n of ['starter-guy.jpg','starter-soft.jpg','starter-wet-c.jpg','starter-freckles-c.jpg'])
      localStorage.setItem('seed|'+n,'1');
    if (sh==='androidOld') window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){} };
    if (sh==='androidNew') window.RealismCam = { saveImage(){}, adPlace(){}, adProj(){}, adAccent(){}, dlog(){}, authGoogle(){} };
  }, shell);
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof accOpen === 'function', null, { timeout: 20000 });
  return pg;
}
(async () => {
  const t0=Date.now();
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });

  for (const [shell, wantG, wantA] of [['browser',true,true],['androidNew',true,false],['androidOld',false,false]]) {
    const pg = await page(br, shell==='browser'?null:shell);
    const r = await pg.evaluate(() => { accOpen(); return {
      row: getComputedStyle(document.getElementById('accBtn')).display !== 'none',
      g: getComputedStyle(document.getElementById('accGoogle')).display !== 'none',
      a: getComputedStyle(document.getElementById('accApple')).display !== 'none',
      m: getComputedStyle(document.getElementById('accMailBtn')).display !== 'none',
    };});
    ok(shell + ': account reachable', r.row);
    ok(shell + ': email always offered', r.m);
    ok(shell + ': google shown = ' + wantG, r.g === wantG);
    ok(shell + ': apple shown = ' + wantA, r.a === wantA);
    await pg.context().close();
  }

  // the whole email flow, in the shell that has no Google at all
  const pg = await page(br, 'androidOld');
  const R = await pg.evaluate(async () => {
    const out = {};
    const set=(e,p)=>{ document.getElementById('accEmail').value=e;
                       document.getElementById('accPass').value=p; };
    const said=()=>document.getElementById('accState').textContent;
    accOpen();
    document.getElementById('accMailBtn').click();
    out.formOpens = !document.getElementById('accForm').hidden;

    set('notanemail','secret123'); await accMailGo(true); out.badEmail = said();
    set('a@b.com','123');          await accMailGo(true); out.shortPw = said();
    set('a@b.com','secret123');    await accMailGo(true);
    out.created = !!ACC_USER && ACC_USER.email === 'a@b.com';
    await accSignOut();
    set('a@b.com','wrongpass');    await accMailGo(false); out.wrongPw = said();
    set('a@b.com','secret123');    await accMailGo(false);
    out.signedBackIn = !!ACC_USER;
    out.passCleared = document.getElementById('accPass').value === '';
    set('a@b.com',''); await accMailReset(); out.reset = said();
    return out;
  }).catch(e => ({ err: e.message }));

  if (R.err) console.log('  evaluate threw: ' + R.err);
  ok('form opens on tap', R.formOpens);
  ok('rejects a bad address', /does not look right/.test(R.badEmail||''), R.badEmail);
  ok('rejects a short password', /6 characters/.test(R.shortPw||''), R.shortPw);
  ok('creates an account', R.created);
  ok('wrong password is refused', /wrong email or password/.test(R.wrongPw||''), R.wrongPw);
  ok('signs back in', R.signedBackIn);
  ok('password field is cleared', R.passCleared);
  ok('sends a reset email', /reset link/.test(R.reset||''), R.reset);

  await br.close();
  console.log((fail?'FAILED '+fail+' of ':'all ')+(pass+fail)+' checks in '+Math.round((Date.now()-t0)/1000)+'s');
  process.exit(fail?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
