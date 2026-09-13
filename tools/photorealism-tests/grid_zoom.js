// Does the grid track the image through a zoom? Spark 10C profile (4GB).
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{
    Object.defineProperty(navigator,'deviceMemory',{get:()=>4});
    localStorage.setItem('intro1','1'); localStorage.setItem('tour','done');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
  });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:20000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:20000});
  // open a starter project and get to the drawing screen
  await pg.evaluate(async ()=>{
    const r=(await galAll())[0];
    openPhoto(r.blob, r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<1500;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  const base = await pg.evaluate(()=>({ready:GRID_READY, s:view.s, world:[WORLD.w,WORLD.h],
    refImg:[$('refImg').width,$('refImg').height]}));
  console.log('on the drawing screen:', JSON.stringify(base));
  console.log('image canvas matches the grid world:',
    base.refImg[0]===base.world[0] ? 'ok' : 'MISMATCH (grid and image would drift)');
  // zoom in with the wheel, let it settle, and see whether the grid re-baked
  const vp = await pg.locator('#viewport').boundingBox();
  for (let i=0;i<6;i++){ await pg.mouse.move(vp.x+vp.width/2, vp.y+vp.height/2); await pg.mouse.wheel(0,-240); await pg.waitForTimeout(60); }
  await pg.waitForTimeout(700);
  const after = await pg.evaluate(()=>({
    s:+view.s.toFixed(4),
    drawnS: GRID_DRAWN? +GRID_DRAWN.s.toFixed(4):null,
    ride: $('gridCv').style.transform||'(cleared)',
    ready: GRID_READY,
  }));
  console.log('after zooming:', JSON.stringify(after));
  const tracked = after.drawnS!==null && Math.abs(after.drawnS-after.s)<1e-3 && after.ride==='(cleared)';
  console.log('grid re-baked at the new zoom:', tracked ? 'ok' : 'FAIL (grid left at the old scale)');
  console.log('zoom actually happened:', after.s>base.s ? 'ok' : 'FAIL');
  if (errs.length) console.log('page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
