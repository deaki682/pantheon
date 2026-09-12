const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror', e=>errs.push(e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof galAdd==='function' && document.querySelectorAll('#gallery .gitem').length>=2, null, {timeout:30000});
  await pg.waitForFunction(() => !document.getElementById('introSplash').classList.contains('on'), null, {timeout:15000});
  // six references, so the row scrolls and several neighbours must move
  await pg.evaluate(async () => {
    for (let i=0;i<6;i++){
      const c=document.createElement('canvas'); c.width=c.height=300;
      const g=c.getContext('2d'); g.fillStyle=['#a33','#3a3','#33a','#aa3','#a3a','#3aa'][i];
      g.fillRect(0,0,300,300);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.8));
      await galAdd({ ts:Date.now()+i, name:'r'+i+'.jpg', thumb:await thumbOf(b,false), blob:b, ord:100+i });
    }
    renderGallery();
  });
  await pg.waitForFunction(() => document.querySelectorAll('#gallery .gitem').length>=8, null, {timeout:15000});
  await pg.waitForTimeout(400);
  const before = await pg.evaluate(() => [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('before :', before.join(','));

  // lift the LAST tile and carry it left across the row, resting at the edge
  const n = before.length;
  await pg.locator('#gallery .gitem').nth(n-1).scrollIntoViewIfNeeded();
  await pg.waitForTimeout(250);
  const last = await pg.locator('#gallery .gitem').nth(n-1).boundingBox();
  await pg.mouse.move(last.x+last.width/2, last.y+last.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(560);
  const up = await pg.evaluate(()=>({fly:!!document.querySelector('.gdrag'),
    ghost:!!document.querySelector('.ghosted')}));
  console.log('lifted :', JSON.stringify(up), up.fly&&up.ghost?'ok':'FAIL');
  await pg.waitForTimeout(280);
  const sl0 = await pg.evaluate(()=>document.getElementById('gallery').scrollLeft);
  // walk to the left edge and HOLD there: the row should keep scrolling
  for (let i=1;i<=12;i++){ await pg.mouse.move(last.x+last.width/2 - (last.x)*i/12, last.y+last.height/2); await pg.waitForTimeout(16); }
  await pg.mouse.move(26, last.y+last.height/2);
  await pg.waitForTimeout(1400);
  const sl1 = await pg.evaluate(()=>document.getElementById('gallery').scrollLeft);
  console.log('auto-scroll at the edge :', Math.round(sl0)+' -> '+Math.round(sl1), sl1 < sl0-20 ? 'ok' : 'FAIL');
  const shifted = await pg.evaluate(() => [...document.querySelectorAll('#gallery .gitem')]
      .filter(k=>!k.classList.contains('ghosted') && getComputedStyle(k).transform!=='none').length);
  console.log('neighbours moved       :', shifted, shifted>=3 ? 'ok' : 'FAIL');
  await pg.mouse.up();
  await pg.waitForTimeout(700);
  const after = await pg.evaluate(() => [...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  console.log('after  :', after.join(','));
  const moved=before[n-1], landed=after.indexOf(moved);
  console.log('carried to the front   :', 'index '+(n-1)+' -> '+landed, landed<=1 ? 'ok' : 'FAIL');
  const rest=before.filter(x=>x!==moved);
  const expect=[...rest]; expect.splice(landed,0,moved);
  console.log('everyone else in order :', expect.join(',')===after.join(',') ? 'ok' : 'FAIL');
  const st = await pg.evaluate(async () => {
    const o={}; for (const r of await galAll()) o[r.id]=r.ord;
    return { dom:[...document.querySelectorAll('#gallery .gitem')].map(t=>o[+t.dataset.gid]),
      leftovers: document.querySelectorAll('.gdrag,.ghosted,.reorder').length,
      dragging: document.documentElement.classList.contains('dragging') };
  });
  const asc = st.dom.every((v,i,a)=> i===0 || v>=a[i-1]);
  console.log('ord matches the row    :', asc ? 'ok' : 'FAIL', st.dom.join(','));
  console.log('no leftovers           :', st.leftovers===0 && !st.dragging ? 'ok' : 'FAIL');
  console.log('page errors            :', errs.length, errs.slice(0,2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
