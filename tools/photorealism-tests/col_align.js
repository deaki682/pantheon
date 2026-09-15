// The gear and Download are ONE pill - gear on the top half, Download on the
// bottom - and its bottom edge has to sit level with the bloomed player's.
const { chromium } = require('playwright-core');
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const [n,W,H,ux] of [['phone',411,891,1],['small',320,640,1],
                            ['phone ux1.3',411,891,1.3],['phone ux1.6',411,891,1.6],
                            ['tablet',800,1280,1]]){
    const ctx = await br.newContext({ viewport:{width:W,height:H}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await pg.evaluate(async (ux)=>{
      if (ux!==1) document.documentElement.style.setProperty('--ux', ux);
      const c=document.createElement('canvas'); c.width=2400;c.height=1800;
      const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,2400,1800);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
      await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      show('scrFormat'); await new Promise(r=>setTimeout(r,300));
      $('fmtGo').onclick();
      for (let i=0;i<500;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,400));
    }, ux);
    const r = await pg.evaluate(()=>{
      const gear=$('setBtn').getBoundingClientRect(), dl=$('expBtn').getBoundingClientRect();
      const card=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--adcard'))||120;
      return { gearB:Math.round(gear.bottom), dlT:Math.round(dl.top), dlB:Math.round(dl.bottom),
               btn:Math.round(dl.height), cardB:8+card, card };
    });
    const aligned = Math.abs(r.dlB - r.cardB) <= 1;
    const safeGap = r.dlT - r.gearB;
    console.log(n.padEnd(12)+' button '+String(r.btn).padStart(3)
      +'  gear ends '+String(r.gearB).padStart(4)
      +'  download '+String(r.dlT).padStart(4)+'-'+String(r.dlB).padStart(4)
      +'  card ends '+String(r.cardB).padStart(4)
      +(aligned?'   ALIGNED':'   +'+(r.dlB-r.cardB))+'   gap '+safeGap);
    // one pill now: the two halves SHARE an edge rather than standing apart,
    // and between them they are exactly as tall as the bloomed card
    ok(safeGap === 0, n+': the two halves share an edge ('+safeGap+'px apart)');
    ok(aligned, n+': and the pill ends level with the bloomed player ('
       +(r.dlB-r.cardB)+'px off)');
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ncolumn OK');
  process.exit(bad?1:0);
})();
