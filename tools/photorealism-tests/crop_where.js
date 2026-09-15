// Panning the crop costs ~145ms of MAIN THREAD at 4x. Which part of
// fmtPreview? Turn one thing off at a time and re-measure the same pan.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const RATE = +(process.argv[3]||4);
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
    show('scrFormat');
    await new Promise(r=>setTimeout(r,900));
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: RATE });
  const CASES = [
    ['everything on',        {}],
    ['punch off (red grid)', {col:'#ff3b30'}],
    ['grid off',             {gridOn:false}],
    ['photo blit cached',    {freezePhoto:true}],
    ['photo AND punch off',  {col:'#ff3b30', freezePhoto:true}],
  ];
  for (const [name,opt] of CASES){
    const r = await pg.evaluate(async ([opt])=>{
      GRID_STYLE='diag'; GRID_ON=opt.gridOn===false?false:true;
      GRID_COL=opt.col||'auto';
      FMT_ZOOM=2.2; FMT_OFF.x=0.5; FMT_OFF.y=0.5;
      FMT_GRID=null; FMT_PHOTO=null;
      fmtPreview();
      await new Promise(r=>setTimeout(r,500));
      // freezing the photo blit: pin the cache key so the 12MP resample
      // never re-runs, which is what a pan makes it do every frame
      let realKey=null;
      if (opt.freezePhoto){
        realKey=FMT_PHOTO?FMT_PHOTO.k:null;
        Object.defineProperty(FMT_PHOTO,'k',{get:()=>realKey,set:()=>{},configurable:true});
      }
      const cv=$('fmtCanvas');
      const flush=()=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
      const cost=[];
      for (let i=0;i<14;i++){
        FMT_OFF.x = 0.5 + (i%7)*0.02;
        FMT_OFF.y = 0.5 + (i%5)*0.015;
        const t0=performance.now();
        fmtPreview(); flush();
        cost.push(performance.now()-t0);
        await new Promise(r=>requestAnimationFrame(()=>r()));
      }
      if (opt.freezePhoto && FMT_PHOTO) delete FMT_PHOTO.k;
      cost.sort((a,b)=>a-b);
      return +(cost[Math.floor(cost.length/2)]||0).toFixed(1);
    }, [opt]);
    console.log('  '+name.padEnd(24)+String(r).padStart(7)+'ms per pan frame');
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
