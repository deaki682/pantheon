const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof resNoteSync==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  for (const [w,h,cm] of [[736,981,30],[736,981,50],[400,500,30],[1800,1200,30]]){
    const r = await pg.evaluate(async ([w,h,cm])=>{
      const c=document.createElement('canvas'); c.width=w;c.height=h;
      const g=c.getContext('2d'); g.fillStyle='#777'; g.fillRect(0,0,w,h);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.85));
      await addRef(new File([b],w+'x'+h+'.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<300;i++){ if (photo&&photo.width===w) break; await new Promise(r=>setTimeout(r,50)); }
      $('unit').value='cm'; $('widthIn').value=String(cm); fmtPreview();
      const out={ ppi:Math.round(cropRect().w/physWIn()),
        note:$('resNote').classList.contains('on')?$('resNote').textContent.slice(0,26):'silent' };
      show('scrUpload'); await new Promise(r=>setTimeout(r,120));
      return out;
    }, [w,h,cm]);
    console.log((w+'x'+h+' at '+cm+'cm').padEnd(22), String(r.ppi).padStart(4)+' ppi  ', r.note);
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
