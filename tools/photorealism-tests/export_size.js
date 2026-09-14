// What resolution is the app actually holding, and what does Download produce?
const { chromium } = require('playwright-core');
(async () => {
  for (const mem of [8,4,3]){
    const br = await chromium.launch(require('./browser.js'));
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript((m)=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
      try{ Object.defineProperty(navigator,'deviceMemory',{get:()=>m,configurable:true}); }catch(e){}
    }, mem);
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    const r = await pg.evaluate(async ()=>{
      // a 12MP phone photo, the common case
      const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
      const b=await new Promise(x=>c.toBlob(x,'image/jpeg',.95));
      await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(x=>setTimeout(x,50)); }
      $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
      for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(x=>setTimeout(x,50)); }
      await new Promise(x=>setTimeout(x,6000));
      const {w,h}=worldSize(); const rs=refSize();
      const src=viewSrc();
      let k=Math.max(1, Math.min(2, (state.img.width||w)/w));
      if (src && src.width > w*k) k = src.width / w;
      const MAXPX = refCap()<=2560 ? 8e6 : refCap()<4096 ? 12e6 : 17e6;
      if (w*h*k*k > MAXPX) k = Math.sqrt(MAXPX/(w*h));
      return {
        photo: photo.width+'x'+photo.height,
        stateImg: state.img.width+'x'+state.img.height,
        world: w+'x'+h,
        refQ: +refQ().toFixed(2),
        refShown: rs.w+'x'+rs.h,
        viewSrcIs: (src===state.img?'the photograph':'the composite')
          +' '+(src?src.width+'x'+src.height:'-'),
        exportNow: Math.round(w*k)+'x'+Math.round(h*k),
        exportMP: +((w*k*h*k)/1e6).toFixed(1),
        refMP: +((rs.w*rs.h)/1e6).toFixed(1),
        cap: refCap()
      };
    });
    console.log('  deviceMemory '+mem+'GB  refCap '+r.cap);
    console.log('    photo '+r.photo+'   held as '+r.stateImg+'   world '+r.world);
    console.log('    the app shows '+r.refShown+' ('+r.refMP+'MP, refQ '+r.refQ+')   viewSrc: '+r.viewSrcIs);
    console.log('    Download gives '+r.exportNow+' ('+r.exportMP+'MP)'
      + (r.exportMP < r.refMP ? '   <-- SMALLER than what is on screen' : ''));
    await br.close();
  }
})().catch(e=>{console.error(e);process.exit(1)});
