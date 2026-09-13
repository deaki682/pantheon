// The risk I flagged: a 4GB phone, a big photo, drawing screen + cook +
// compare all live at once. Same device class that was crashing.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{
    Object.defineProperty(navigator,'deviceMemory',{get:()=>4});
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
  });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  pg.on('crash',()=>errs.push('PAGE CRASHED'));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const cdp = await ctx.newCDPSession(pg);
  const heap = async () => {
    const m = await cdp.send('Runtime.getHeapUsage').catch(()=>null);
    const j = await pg.evaluate(()=>performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):0);
    return j;
  };
  console.log('idle heap                 :', await heap(), 'MB');
  // a 12MP phone photo, the common case
  await pg.evaluate(async ()=>{
    const w=4032,h=3024; const c=document.createElement('canvas'); c.width=w;c.height=h;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,w,h);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,w,h);
    for (let i=0;i<20000;i++){ g.fillStyle='rgba(255,255,255,.5)'; g.fillRect(Math.random()*w,Math.random()*h,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone12mp.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
  });
  console.log('after importing a 12MP photo:', await heap(), 'MB');
  await pg.evaluate(async ()=>{
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<2000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  const dr = await pg.evaluate(()=>({ heap: performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):0,
    world:[WORLD.w,WORLD.h], backing:[$('refImg').width,$('refImg').height],
    canvasMB: +(($('refImg').width*$('refImg').height*4)/1048576).toFixed(1) }));
  console.log('on the drawing screen     :', dr.heap, 'MB   world', dr.world.join('x'),
    ' reference canvas', dr.backing.join('x'), '=', dr.canvasMB, 'MB of canvas');
  // zoom deep, toggle layers, then open compare - everything alive at once
  await pg.evaluate(async ()=>{
    const r=$('viewport').getBoundingClientRect();
    view.s=Math.min(r.width/WORLD.w,r.height/WORLD.h)*4; applyView(); paintWorld();
    await new Promise(r=>setTimeout(r,400));
    LAYERS.hl=false; viewRepaint(); await new Promise(r=>setTimeout(r,400));
    LAYERS.hl=true; viewRepaint(); await new Promise(r=>setTimeout(r,400));
    try{ $('compareBtn').click(); }catch(e){}
    await new Promise(r=>setTimeout(r,1800));
  });
  console.log('zoomed + layers + compare :', await heap(), 'MB');
  console.log('page errors / crash       :', errs.length?errs.slice(0,3):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
