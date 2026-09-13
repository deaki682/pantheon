// What resolution does a reference actually end up at, from import to zoom?
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:20000});
  for (const [w,h,cm] of [[6000,4000,30],[4032,3024,30],[6000,4000,60],[1200,900,30]]){
    const r = await pg.evaluate(async ([w,h,cm])=>{
      const c=document.createElement('canvas'); c.width=w; c.height=h;
      const g=c.getContext('2d');
      // fine detail: 1px checks, the thing you lose when resolution drops
      const im=g.createImageData(w,h); const d=im.data;
      for (let y=0;y<h;y++) for (let x=0;x<w;x++){ const i=(y*w+x)*4;
        const v=((x^y)&1)?235:30; d[i]=d[i+1]=d[i+2]=v; d[i+3]=255; }
      g.putImageData(im,0,0);
      const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));
      await addRef(new File([blob],w+'.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<300;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      const capped=[photo.width,photo.height];
      $('unit').value='cm'; $('widthIn').value=String(cm); $('fmtGo').click();
      for (let i=0;i<900;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
      const inches=cm/2.54;
      return { src:[w,h], capped, world:[WORLD.w,WORLD.h],
        srcPpi:Math.round(w/inches), workPpi:Math.round(WORLD.w/inches),
        lost:+(w/WORLD.w).toFixed(1) };
    }, [w,h,cm]);
    console.log(`${r.src[0]}x${r.src[1]} at ${cm}cm -> stored ${r.capped[0]}px, drawing canvas ${r.world[0]}x${r.world[1]}`);
    console.log(`   source ${r.srcPpi} ppi, app works at ${r.workPpi} ppi, detail thrown away: ${r.lost}x linear`);
    await pg.evaluate(()=>{ try{ show('scrUpload'); }catch(e){} });
    await pg.waitForTimeout(200);
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
