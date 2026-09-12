const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ try{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); }catch(e){} });
  const page = await ctx.newPage();
  await page.goto('http://127.0.0.1:8899/index.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>typeof addRef==='function');
  const r = await page.evaluate(async () => {
    const c=document.createElement('canvas'); c.width=c.height=900;
    const g=c.getContext('2d');
    g.fillStyle='#d8b08c'; g.beginPath(); g.arc(450,450,300,0,7); g.fill();
    const blob=await new Promise(r=>c.toBlob(r,'image/png'));
    await addRef(new File([blob],'cut.png',{type:'image/png'}), false);
    for(let i=0;i<200;i++){ if(photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('widthIn').value='25'; $('unit').value='cm'; $('fmtGo').click();
    for(let i=0;i<900;i++){ if(document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    // what the drawing actually shows: sample the cooked form plane at a corner
    const out={};
    try{ const f=FORM&&FORM.g; if (f) out.formCorner=f[5*WORLD.w+5]; }catch(e){ out.formErr=String(e); }
    // and the on-screen canvas
    try{ const cv=document.querySelector('#scrMain canvas'); const gg=cv.getContext('2d');
      const d=gg.getImageData(4,4,1,1).data; out.screenCorner=[d[0],d[1],d[2],d[3]]; }catch(e){ out.scrErr=String(e); }
    // and what an export/jpeg encode produces
    try{ const b=canvasBlob(photo,'image/jpeg',0.9); out.jpegBytes=b?b.size:0;
      const im=await createImageBitmap(b); const q=document.createElement('canvas');
      q.width=im.width;q.height=im.height;q.getContext('2d').drawImage(im,0,0);
      const d2=q.getContext('2d').getImageData(4,4,1,1).data; out.jpegCorner=[d2[0],d2[1],d2[2]]; }catch(e){ out.jpegErr=String(e); }
    return out;
  });
  console.log(JSON.stringify(r,null,1));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
