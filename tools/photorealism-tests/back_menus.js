// The system back button steps up one screen. With one of the drawing
// screen's popup menus open it should close THAT first - the way it already
// does for every panel - rather than leaving the drawing screen with a menu
// still hanging open over the gallery.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof __backStep==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const open = async () => pg.evaluate(async ()=>{
    if (document.querySelector('#scrMain.on')) return;
    show('scrUpload'); await new Promise(r=>setTimeout(r,200));
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  await open();
  let bad=0;
  // 1. plain back from the drawing screen
  const plain = await pg.evaluate(()=>{
    const r=__backStep();
    return { r, screen:(document.querySelector('.screen.on')||{}).id };
  });
  const ok1 = plain.screen==='scrUpload' && plain.r!=='exit';
  if(!ok1) bad++;
  console.log('  back from the drawing screen  -> '+plain.screen+'  ('+plain.r+')  '+(ok1?'ok':'FAIL'));

  // 2. with each popup open, back should close the popup and STAY
  for (const [id, opener] of [
      ['detMenu',   "$('detBtn').click()"],
      ['gridMenu',  "$('gridBtn').click()"],
      ['underMenu', "UNDER=true; $('underMenu').style.display='flex'"],
      ['hud',       "$('hudToggle').click()"]]){
    await open();
    const r = await pg.evaluate(async ([id,opener])=>{
      try{ eval(opener); }catch(e){ return {skip:e.message}; }
      await new Promise(r=>setTimeout(r,350));
      const el=document.getElementById(id);
      const wasOpen = !!el && getComputedStyle(el).display!=='none'
                   && getComputedStyle(el).visibility!=='hidden';
      const res=__backStep();
      await new Promise(r=>setTimeout(r,350));
      const stillOpen = !!el && getComputedStyle(el).display!=='none'
                     && getComputedStyle(el).visibility!=='hidden';
      return { wasOpen, stillOpen, res, screen:(document.querySelector('.screen.on')||{}).id };
    }, [id,opener]);
    if (r.skip){ console.log('  '+id.padEnd(11)+' could not open: '+r.skip); continue; }
    if (!r.wasOpen){ console.log('  '+id.padEnd(11)+' did not open, skipped'); continue; }
    // correct: the popup closed AND we are still on the drawing screen
    const good = !r.stillOpen && r.screen==='scrMain';
    if (!good) bad++;
    console.log('  '+id.padEnd(11)+' open, then back -> screen '+String(r.screen).padEnd(10)
      +' popup '+(r.stillOpen?'STILL OPEN':'closed')+'   '+(good?'ok':'FAIL'));
  }
  console.log(bad? '\n'+bad+' case(s) where back does the wrong thing' : '\nback behaves');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
