// The FIRST layer toggle and the FIRST detail switch after opening a drawing.
const { chromium } = require('playwright-core');
const PORT = process.argv[2] || '8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const r = await pg.evaluate(async ()=>{
    // a real 12MP phone photo, not the 2000px starter
    {
      const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(.5,'#6a6a6a'); gr.addColorStop(1,'#111');
      g.fillStyle=gr; g.fillRect(0,0,W,H);
      for (let i=0;i<30000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
      await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    const t0=performance.now();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    const openMs=Math.round(performance.now()-t0);
    // straight into the layer workshop, exactly as an artist would
    const t1=performance.now();
    LAYERS.hl=false; COMP.sig=null; viewRepaint();
    const firstToggle=Math.round(performance.now()-t1);
    await new Promise(r=>setTimeout(r,80));
    const t2=performance.now();
    LAYERS.dk=false; COMP.sig=null; viewRepaint();
    const secondToggle=Math.round(performance.now()-t2);
    // and the first detail switch, waiting until the level's planes are in
    const t3=performance.now();
    DETAIL='fine'; COMP.sig=null; viewRepaint();
    const firstDetailPaint=Math.round(performance.now()-t3);
    let settled=0;
    for (let i=0;i<400;i++){
      if (DET.key===fkey() && DET.lv.fine){ settled=Math.round(performance.now()-t3); break; }
      compositeCv(); await new Promise(r=>setTimeout(r,25));
    }
    return { openMs, firstToggle, secondToggle, firstDetailPaint, detailSettled:settled,
      canvas:[$('refImg').width,$('refImg').height], world:[WORLD.w,WORLD.h] };
  });
  console.log('port '+PORT+'  open '+r.openMs+'ms   canvas '+r.canvas.join('x')+'  world '+r.world.join('x'));
  console.log('   FIRST layer toggle '+r.firstToggle+'ms | second '+r.secondToggle
    +'ms | first detail switch paints in '+r.firstDetailPaint+'ms, settles at '+r.detailSettled+'ms');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
