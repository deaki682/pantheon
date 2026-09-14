// the entire reference, filling the screen, auto vs punch
const { chromium } = require('playwright-core');
const WHICH = process.argv[2]||'starter-guy.jpg';
const CELL  = +(process.argv[3]||3);
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:1100,height:820}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const info = await pg.evaluate(async (a)=>{
    const [name,cell]=a;
    const r=await fetch(name); const b=await r.blob();
    await addRef(new File([b],name,{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    const ar = photo.width/photo.height;
    $('unit').value='cm';
    $('widthIn').value = ar>=1 ? '40' : '30';
    $('heightIn').value = String(Math.round((ar>=1?40:30)/ar));
    $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    CELLSZ.u='cm'; CELLSZ.v=cell; GRID_ON=true; GRID_STYLE='sq'; GRID_LAB=false;
    GRID_OP=0.9; GRID_THK=2;
    return {photo:photo.width+'x'+photo.height, sheet:$('widthIn').value+'x'+$('heightIn').value};
  }, [WHICH, CELL]);
  console.log('  '+WHICH+'  photo '+info.photo+'  sheet '+info.sheet+'cm  cells '+CELL+'cm');
  await pg.waitForTimeout(8000);
  // fit the whole sheet in the viewport
  await pg.evaluate(async ()=>{
    const r=$('viewport').getBoundingClientRect();
    const {w,h}=worldSize();
    view.s=Math.min(r.width/w, r.height/h)*0.97;
    view.x=(r.width-w*view.s)/2; view.y=(r.height-h*view.s)/2;
    applyView(); drawGrid();
    await new Promise(x=>requestAnimationFrame(()=>requestAnimationFrame(x)));
  });
  const fs=require('fs');
  for (const col of ['auto','punch']){
    await pg.evaluate(async c=>{ GRID_COL=c; applyGrid(); drawGrid();
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))); }, col);
    await pg.waitForTimeout(900);
    const buf = await pg.locator('#viewport').screenshot();
    fs.writeFileSync('whole_'+col+'.png', buf);
  }
  console.log('  shot');
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
