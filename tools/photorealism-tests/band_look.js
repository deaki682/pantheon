// Colour mode with only some bands chosen: the border against the bare paper
// is where the staircase shows. Shoot it at several feather widths.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const setup = await pg.evaluate(async ()=>{
    // a soft colour subject: broad smooth gradients are exactly where an
    // iso-tone border turns into a staircase
    const W=2000,H=1500; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    g.fillStyle='#6a5a4a'; g.fillRect(0,0,W,H);
    const blob=(x,y,r,c1,c2)=>{ const rg=g.createRadialGradient(x,y,0,x,y,r);
      rg.addColorStop(0,c1); rg.addColorStop(1,c2); g.fillStyle=rg;
      g.beginPath(); g.arc(x,y,r,0,6.2832); g.fill(); };
    blob(700,600,560,'#fff4e0','#6a5a4a');
    blob(1400,900,520,'#2a1f18','#6a5a4a');
    blob(1100,400,380,'#d8a060','#6a5a4a');
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
    try{ localStorage.setItem('mode|pending','c'); }catch(e){}
    await addRef(new File([b],'soft.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    // force the project into colour
    try{ localStorage.setItem('mode|'+galActive,'c'); }catch(e){}
    REFMODE='c'; document.body.classList.add('colorRef');
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    GRID_ON=false; applyGrid();
    return {mode:REFMODE, colorRef:document.body.classList.contains('colorRef')};
  });
  console.log('  mode='+setup.mode+'  colorRef='+setup.colorRef);
  await pg.waitForTimeout(6000);
  const fs=require('fs');
  for (const soft of [0, 9, 20]){
    await pg.evaluate(s=>{
      BAND_SOFT=s;
      LAYERS_C.dk=true; LAYERS_C.mid=true; LAYERS_C.lt=false; LAYERS_C.br=false;
      COMP.sig=null; viewRepaint();
    }, soft);
    await pg.waitForTimeout(1600);
    const buf = await pg.locator('#viewport').screenshot();
    fs.writeFileSync('band_'+soft+'.png', buf);
    console.log('  BAND_SOFT='+soft+'  shot');
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
