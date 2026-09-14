// Two drag defects: a rebuild landing mid-gesture, and dropping into the
// last slot landing after the "+" tile.
const { chromium } = require('playwright-core');
const seed = async (pg, n) => pg.evaluate(async (n)=>{
  for (let i=0;i<n;i++){
    const c=document.createElement('canvas'); c.width=c.height=300;
    const g=c.getContext('2d'); g.fillStyle='hsl('+(i*60)+',50%,45%)'; g.fillRect(0,0,300,300);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
    await galAdd({ ts:Date.now()+i, name:'d'+i+'.jpg', thumb:await thumbOf(b,false), blob:b, ord:i });
  }
  renderGallery();
}, n);
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof galAdd==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await seed(pg, 4);
  await pg.waitForFunction(()=>document.querySelectorAll('#gallery .gitem').length>=6,null,{timeout:15000});
  await pg.waitForTimeout(500);

  // A. a sync-driven renderGallery in the middle of a drag
  const before = await pg.evaluate(()=>[...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  await pg.locator('#gallery .gitem').nth(1).scrollIntoViewIfNeeded();
  await pg.waitForTimeout(250);
  let a = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  await pg.mouse.move(a.x+a.width/2, a.y+a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(950);
  await pg.mouse.move(a.x+a.width/2+120, a.y+a.height/2);
  await pg.evaluate(()=>renderGallery());            // what a background sync does
  await pg.waitForTimeout(150);
  await pg.mouse.up();
  await pg.waitForTimeout(900);
  const afterA = await pg.evaluate(()=>({
    fly:document.querySelectorAll('.gdrag').length,
    dragging:document.documentElement.classList.contains('dragging'),
    reorder:document.getElementById('gallery').classList.contains('reorder'),
    ghost:document.querySelectorAll('.ghosted').length,
    touch:getComputedStyle(document.documentElement).touchAction,
    tiles:document.querySelectorAll('#gallery .gitem').length }));
  console.log('rebuild mid-drag :', JSON.stringify(afterA),
    !afterA.fly && !afterA.dragging && !afterA.reorder && !afterA.ghost && afterA.tiles>=6 ? 'ok' : 'FAIL');

  // B. drop into the LAST slot
  await pg.waitForTimeout(400);
  const ids = await pg.evaluate(()=>[...document.querySelectorAll('#gallery .gitem')].map(t=>t.dataset.gid));
  await pg.locator('#gallery .gitem').first().scrollIntoViewIfNeeded();
  await pg.waitForTimeout(250);
  a = await pg.locator('#gallery .gitem').first().boundingBox();
  await pg.mouse.move(a.x+a.width/2, a.y+a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(950);
  for (let i=1;i<=14;i++){ await pg.mouse.move(a.x+a.width/2+ i*60, a.y+a.height/2); await pg.waitForTimeout(30); }
  await pg.mouse.move(395, a.y+a.height/2);
  await pg.waitForTimeout(1600);                      // let the row scroll to the end
  await pg.mouse.up();
  await pg.waitForTimeout(900);
  const afterB = await pg.evaluate(()=>{
    const host=document.getElementById('gallery');
    const kids=[...host.children].map(k=>k.classList.contains('gadd')?'+':k.dataset.gid);
    return { order:kids, plusLast: kids[kids.length-1]==='+' };
  });
  console.log('dropped at the end:', afterB.order.join(' '),
    afterB.plusLast ? 'ok (the + stays last)' : 'FAIL (landed after the +)');
  console.log('page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
