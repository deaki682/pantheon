// the real jank: how far does a neighbour TELEPORT in one frame?
const { chromium } = require('playwright-core');
const PORT = process.argv[2] || '8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
  });
  await pg.goto('http://localhost:'+PORT+'/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof galAdd==='function', null, {timeout:30000});
  await pg.waitForFunction(() => !document.getElementById('introSplash').classList.contains('on'), null, {timeout:15000});
  await pg.evaluate(async () => {
    for (let i=0;i<6;i++){
      const c=document.createElement('canvas'); c.width=c.height=300;
      const g=c.getContext('2d'); g.fillStyle='hsl('+(i*50)+',50%,50%)'; g.fillRect(0,0,300,300);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.85));
      await galAdd({ ts:Date.now()+i, name:'j'+i+'.jpg', thumb:await thumbOf(b,false), blob:b, ord:100+i });
    }
    renderGallery();
  });
  await pg.waitForTimeout(500);
  await pg.locator('#gallery .gitem').nth(1).scrollIntoViewIfNeeded();
  await pg.waitForTimeout(250);
  const a = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  console.log('  press at x='+Math.round(a.x));
  await pg.mouse.move(a.x+a.width/2, a.y+a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(700);
  const diag = await pg.evaluate(()=>({ n:document.querySelectorAll('#gallery .gitem').length,
    lifted: !!document.querySelector('.gdrag')||!!document.querySelector('.gitem.dragging'),
    left3: (document.querySelectorAll('#gallery .gitem')[3]||{getBoundingClientRect:()=>({left:-1})}).getBoundingClientRect().left }));
  console.log('  diag:', JSON.stringify(diag));
  // watch the tile two places along: it must make room as we pass it
  await pg.evaluate(() => {
    window.__j=[]; const k=[...document.querySelectorAll('#gallery .gitem')][3];
    let prev=k.getBoundingClientRect().left;
    const t=()=>{ const n=k.getBoundingClientRect().left;
      window.__j.push(Math.abs(n-prev)); prev=n; requestAnimationFrame(t); };
    requestAnimationFrame(t);
  });
  for (let i=0;i<30;i++){ await pg.mouse.move(a.x+a.width/2 + i*9, a.y+a.height/2); await pg.waitForTimeout(16); }
  const j = await pg.evaluate(()=>window.__j.slice());
  await pg.mouse.up(); await pg.waitForTimeout(400);
  const max=Math.max(...j), total=j.reduce((x,y)=>x+y,0);
  console.log('port '+PORT+' | frames '+j.length
    +' | biggest single-frame move: '+max.toFixed(1)+'px'
    +' | total travel: '+total.toFixed(0)+'px');
  console.log(max<40 ? '  -> slides (ok)' : '  -> TELEPORTS');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
