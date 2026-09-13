const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof addRef==='function',null,{timeout:20000});
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  // one fresh image per size, so every cook is a real one
  for (const [i,[w,cm,hcm]] of [[4096,20,15],[4096,40,30],[4096,60,45]].entries()){
    const r = await pg.evaluate(async ([seed,w,cm,hcm])=>{
      const h=Math.round(w*0.75);
      const c=document.createElement('canvas'); c.width=w;c.height=h;
      const g=c.getContext('2d');
      const gr=g.createLinearGradient(seed*7,0,w,h);
      gr.addColorStop(0,'#fff'); gr.addColorStop(.5,'#606060'); gr.addColorStop(1,'#000');
      g.fillStyle=gr; g.fillRect(0,0,w,h);
      for (let k=0;k<6000;k++){ g.fillStyle='rgba(255,255,255,.45)';
        g.fillRect(Math.random()*w,Math.random()*h,2,2); }
      g.fillStyle='#fff'; g.fillRect(seed*11, seed*13, 40, 40);   // unique -> unique cache key
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
      await addRef(new File([b],'c'+seed+'.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      PERF.cook={};
      $('unit').value='cm'; $('widthIn').value=String(cm); $('heightIn').value=String(hcm);
      const t0=performance.now(); $('fmtGo').click();
      for (let i=0;i<1500;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
      const ms=Math.round(performance.now()-t0);
      show('scrUpload'); await new Promise(r=>setTimeout(r,150));
      return { world:WORLD.w+'x'+WORLD.h, mp:+((WORLD.w*WORLD.h)/1e6).toFixed(2), ms, cook:PERF.cook };
    }, [i+1,w,cm,hcm]);
    console.log(String(cm)+'x'+hcm+'cm -> '+r.world+'  '+String(r.mp).padStart(5)+' MP   ready in '+String(r.ms).padStart(5)+'ms   '+JSON.stringify(r.cook));
  }
  console.log('(4x CPU throttle, so roughly a mid-range phone)');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
