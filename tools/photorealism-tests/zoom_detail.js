// How much detail can the app actually SHOW at deep zoom, in each state?
// The file can only be asked to carry what the app has.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(x=>c.toBlob(x,'image/jpeg',.95));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(x=>setTimeout(x,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(x=>setTimeout(x,50)); }
  });
  await pg.waitForTimeout(8000);
  const r = await pg.evaluate(async ()=>{
    const out=[];
    const look = async (label, set)=>{
      set(); COMP.sig=null; viewRepaint();
      await new Promise(x=>setTimeout(x,2200));
      const src=viewSrc();
      const {w,h}=worldSize();
      out.push({label, src: src? src.width+'x'+src.height : '-',
        isPhoto: src===state.img, world:w+'x'+h,
        exportsAt:(()=>{ let k=Math.max(1,Math.min(2,(state.img.width||w)/w));
          if (src && src.width > w*k) k=src.width/w;
          const M=refCap()<=2560?8e6:refCap()<4096?12e6:17e6;
          if (w*h*k*k>M) k=Math.sqrt(M/(w*h));
          return Math.round(w*k)+'x'+Math.round(h*k); })() });
    };
    await look('all layers on, Ultra', ()=>{ LAYERS.dk=LAYERS.lt=LAYERS.hl=true; DETAIL='ultra'; });
    await look('one layer off',        ()=>{ LAYERS.hl=false; });
    await look('all on, detail Fine',  ()=>{ LAYERS.hl=true; DETAIL='fine'; });
    return out;
  });
  console.log('  state                    what the app can show   exports at');
  for (const o of r)
    console.log('  '+o.label.padEnd(25)+(o.src+(o.isPhoto?' (photo)':' (composite)')).padEnd(24)+o.exportsAt);
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
