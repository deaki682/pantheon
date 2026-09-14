// A remote delete arriving for the very tile being dragged.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof galAdd==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.evaluate(async ()=>{
    for (let i=0;i<3;i++){
      const c=document.createElement('canvas'); c.width=c.height=300;
      const g=c.getContext('2d'); g.fillStyle='hsl('+(i*80)+',50%,45%)'; g.fillRect(0,0,300,300);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
      await galAdd({ ts:Date.now()+i, name:'x'+i+'.jpg', thumb:await thumbOf(b,false), blob:b, ord:i });
    }
    renderGallery();
  });
  await pg.waitForFunction(()=>document.querySelectorAll('#gallery .gitem').length>=5,null,{timeout:15000});
  await pg.waitForTimeout(500);
  await pg.locator('#gallery .gitem').nth(1).scrollIntoViewIfNeeded();
  await pg.waitForTimeout(250);
  const a = await pg.locator('#gallery .gitem').nth(1).boundingBox();
  const gid = await pg.evaluate(()=>+document.querySelectorAll('#gallery .gitem')[1].dataset.gid);
  await pg.mouse.move(a.x+a.width/2, a.y+a.height/2);
  await pg.mouse.down();
  await pg.waitForTimeout(950);
  await pg.mouse.move(a.x+a.width/2+130, a.y+a.height/2);
  // the pull loop applying a remote tombstone for the tile in hand
  await pg.evaluate(async (gid)=>{ await galDel(gid, true); galRenderSoon(); }, gid);   // what the pull actually does
  await pg.waitForTimeout(150);
  await pg.mouse.up();
  await pg.waitForTimeout(1200);
  const r = await pg.evaluate(async (gid)=>{
    const recs=await galAll();
    return { deletedStillGone: !recs.some(x=>x.id===gid),
      inDom: !!document.querySelector('.gitem[data-gid="'+gid+'"]'),
      fly:document.querySelectorAll('.gdrag').length,
      dragging:document.documentElement.classList.contains('dragging'),
      ords: recs.map(x=>x.ord).join(','), n:recs.length };
  }, gid);
  console.log('port '+PORT+': ', JSON.stringify(r));
  console.log('   deleted reference stayed deleted:', r.deletedStillGone ? 'ok' : 'FAIL (resurrected)');
  console.log('   no stuck drag state           :', !r.fly && !r.dragging ? 'ok' : 'FAIL');
  console.log('   page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
