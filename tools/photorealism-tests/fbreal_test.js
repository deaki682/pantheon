const { chromium } = require('playwright-core');
const fs = require('fs');
const SDK = __dirname + '/fbsdk/';
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  // serve the real SDK off disk: this sandbox cannot reach the CDN
  await ctx.route('https://www.gstatic.com/firebasejs/**', route => {
    const name = route.request().url().split('/').pop();
    try {
      route.fulfill({ status:200, contentType:'text/javascript',
        body: fs.readFileSync(SDK + name, 'utf8') });
    } catch (e) { route.fulfill({ status:404, body:'' }); }
  });
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(2200);

  console.log('1) SDK init      :', await pg.evaluate(async () => {
    try { const fb = await fbLoad();
      return 'app=' + !!fb.app + ' auth=' + !!fb.auth + ' db=' + !!fb.db + ' st=' + !!fb.st
        + ' project=' + fb.app.options.projectId + ' bucket=' + fb.app.options.storageBucket;
    } catch (e) { return 'ERROR ' + e.message; }
  }));

  console.log('2) every call site:', await pg.evaluate(async () => {
    try { const fb = await fbLoad();
      const need = { U:['setPersistence','onAuthStateChanged','getRedirectResult','GoogleAuthProvider',
                        'OAuthProvider','signInWithPopup','signInWithRedirect','signInWithCredential',
                        'signOut','deleteUser','getAuth','browserLocalPersistence'],
                     S:['getStorage','ref','listAll','deleteObject'],
                     F:['getFirestore','collection','getDocs','deleteDoc'] };
      const miss = [];
      for (const k in need) for (const n of need[k]) if (fb[k][n] === undefined) miss.push(k + '.' + n);
      return miss.length ? 'MISSING ' + miss.join(', ') : 'all present';
    } catch (e) { return 'ERROR ' + e.message; }
  }));

  console.log('3) auth watcher  :', await pg.evaluate(async () => {
    try { await accWatch(); return 'attached, user=' + (ACC_USER ? ACC_USER.uid : 'signed out'); }
    catch (e) { return 'ERROR ' + e.message; }
  }));

  // open the panel and press Google: with no real OAuth it must fail
  // gracefully with a message, never a dead button or an uncaught throw
  await pg.locator('#setBtn, #gearBtn').first().click().catch(()=>{});
  await pg.waitForTimeout(400);
  await pg.locator('#accBtn').click();
  await pg.waitForTimeout(600);
  await pg.locator('#accGoogle').click();
  await pg.waitForTimeout(3000);
  console.log('4) google press  :', await pg.evaluate(() =>
    'state="' + document.getElementById('accState').textContent + '" modal=' +
    getComputedStyle(document.getElementById('accModal')).display));

  // the delete button must arm before it acts
  console.log('5) delete arming :', await pg.evaluate(() => {
    const b = document.getElementById('accDel'); b.click();
    return '"' + b.textContent + '" armed=' + b.dataset.arm;
  }));

  await pg.screenshot({ path: __dirname + '/acct-real.png' });
  console.log(errs.length ? errs.slice(0,5).join('\n') : '6) page errors   : none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
