const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof plainRef==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  // helper: mean absolute difference between two sources, sampled
  await pg.evaluate(()=>{
    window.__diff=(a,b)=>{
      const W=256,H=256;
      const c1=document.createElement('canvas'); c1.width=W;c1.height=H;
      const c2=document.createElement('canvas'); c2.width=W;c2.height=H;
      c1.getContext('2d').drawImage(a,0,0,W,H);
      c2.getContext('2d').drawImage(b,0,0,W,H);
      const d1=c1.getContext('2d').getImageData(0,0,W,H).data;
      const d2=c2.getContext('2d').getImageData(0,0,W,H).data;
      let s=0; for (let i=0;i<d1.length;i+=4) s+=Math.abs(d1[i]-d2[i]);
      return +(s/(W*H)).toFixed(1);
    };
  });
  for (const lv of ['ultra','hyper','fine']){
    const r = await pg.evaluate(async (lv)=>{
      DETAIL=lv; LAYERS.dk=LAYERS.lt=LAYERS.hl=true;
      COMP.sig=null;
      // make sure the level's planes are cooked before judging
      for (let i=0;i<600;i++){
        const c=compositeCv();
        if (lv==='ultra' || (DET.key===fkey() && DET.lv[lv])) break;
        await new Promise(r=>setTimeout(r,200));
      }
      COMP.sig=null;
      const comp=compositeCv();
      const src=viewSrc();
      return { showsPhoto: src===state.img,
               compVsPhoto: window.__diff(comp, state.img),
               compSize:[comp.width,comp.height] };
    }, lv);
    console.log(('detail='+lv).padEnd(14),
      'all layers on ->', r.showsPhoto ? 'SHOWS THE BARE PHOTO' : 'shows the composite',
      ' | composite differs from the photo by', r.compVsPhoto, 'levels');
  }
  console.log('page errors:', errs.length?errs.slice(0,2):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
