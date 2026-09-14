// The drag is faster; the picture must be the same. Shoot the gridded
// reference at rest in every style and zoom, on both versions, and diff.
// At rest means after the fingers lift - which is when the crisp bake lands.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const TAG  = process.argv[3]||'now';
const OUT  = process.argv[4]||'.';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  const CASES=[];
  for (const st of ['sq','diag','dots'])
    for (const z of [1,2,4])
      for (const col of ['auto','#ff3b30'])
        CASES.push([st,z,col]);
  const fs=require('fs');
  for (const [st,z,col] of CASES){
    await pg.evaluate(async ([st,z,col])=>{
      GRID_STYLE=st; GRID_ON=true; GRID_COL=col; GRID_OP=1; GRID_THK=1;
      const b=vpBox(); const {w,h}=worldSize();
      const fit=Math.min(b.width/w,b.height/h);
      view.s=fit*z;
      // off-centre, so the band's edges are in play rather than the middle
      view.x=(b.width-w*view.s)/2 - 40*(z-1);
      view.y=(b.height-h*view.s)/2 - 25*(z-1);
      PUNCH_MAP=null; GRID_SIG=null; applyView(); drawGrid(); drawCircs();
      await new Promise(r=>setTimeout(r,450));
    },[st,z,col]);
    await pg.waitForTimeout(250);
    const nm=st+'_'+z+'x_'+(col==='auto'?'punch':'red');
    await pg.screenshot({ path: OUT+'/pl_'+nm+'_'+TAG+'.png',
      clip:{x:0,y:120,width:411,height:650} });
  }
  if (errs.length) console.log('page errors:', errs.slice(0,3));
  console.log(TAG+': '+CASES.length+' shots');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
