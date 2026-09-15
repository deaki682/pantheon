// The gear and Download are ONE pill, and each half is one of the app's
// ORDINARY buttons - the same square, at the same accessibility scale - so
// the pill reads as two of them fused rather than as a slab of its own.
// #compareBtn stands in for "an ordinary button" here.
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
      const R=el=>{const q=el.getBoundingClientRect();
        return {t:Math.round(q.top),b:Math.round(q.bottom),
                w:Math.round(q.width),h:Math.round(q.height)};};
      return { gear:R($('setBtn')), dl:R($('expBtn')), ord:R($('compareBtn')) };
    });
    const gap = r.dl.t - r.gear.b;
    console.log(n.padEnd(12)+' pill half '+r.gear.w+'x'+r.gear.h
      +'   ordinary button '+r.ord.w+'x'+r.ord.h
      +'   shared edge '+gap+'px'
      +'   pill '+r.gear.w+'x'+(r.dl.b-r.gear.t));
    ok(gap === 0, n+': the two halves share an edge ('+gap+'px apart)');
    ok(Math.abs(r.gear.w - r.ord.w) < 1.5 && Math.abs(r.gear.h - r.ord.h) < 1.5,
       n+': each half is the size of an ordinary button ('
       +r.gear.w+'x'+r.gear.h+' vs '+r.ord.w+'x'+r.ord.h+')');
    ok(Math.abs((r.dl.b - r.gear.t) - r.ord.h*2) < 2,
       n+': so the whole pill is exactly two of them ('
       +(r.dl.b-r.gear.t)+' vs 2x'+r.ord.h+')');
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ncolumn OK');
  process.exit(bad?1:0);
})();
