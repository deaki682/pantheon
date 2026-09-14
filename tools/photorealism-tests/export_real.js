// Capture the canvas Download actually hands off, and check it.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=9; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<50000;i++){ g.fillStyle='rgba(255,255,255,.5)'; g.fillRect(rnd()*W,rnd()*H,3,3); }
    const b=await new Promise(x=>c.toBlob(x,'image/jpeg',.95));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(x=>setTimeout(x,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(x=>setTimeout(x,50)); }
    CELLSZ.u='cm'; CELLSZ.v=3; GRID_ON=true; GRID_COL='auto'; GRID_THK=2; GRID_OP=0.9;
  });
  await pg.waitForTimeout(9000);
  // intercept whatever the composer hands off
  await pg.evaluate(()=>{
    window.__grab=null;
    const o1=HTMLCanvasElement.prototype.toBlob, o2=HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toBlob=function(...a){ if(!window.__grab) window.__grab=this; return o1.apply(this,a); };
    HTMLCanvasElement.prototype.toDataURL=function(...a){ if(!window.__grab) window.__grab=this; return o2.apply(this,a); };
  });
  const probe = async (label, setup) => {
    const r = await pg.evaluate(async (setup)=>{
      window.__grab=null;
      await (new Function('return (async()=>{'+setup+'})()'))();
      await new Promise(x=>setTimeout(x,600));
      try{ $('expBtn').onclick(); }catch(e){}
      for (let i=0;i<120;i++){ if (window.__grab) break; await new Promise(x=>setTimeout(x,50)); }
      const c=window.__grab;
      if (!c) return {err:'nothing handed off'};
      const q=c.getContext('2d',{willReadFrequently:true});
      // sample a band and count how many pixels are near-white or near-black
      // relative to their neighbours - the grid lines
      const y=Math.round(c.height*0.5);
      const d=q.getImageData(0,y,c.width,1).data;
      let lines=0, last=-99;
      for (let x=4;x<c.width-4;x++){
        const v=d[x*4], nb=(d[(x-4)*4]+d[(x+4)*4])/2;
        if (Math.abs(v-nb)>40 && x-last>6){ lines++; last=x; }
      }
      const {w,h}=worldSize();
      return { dims:c.width+'x'+c.height, mp:+((c.width*c.height)/1e6).toFixed(1),
               world:w+'x'+h, ref:state.img.width+'x'+state.img.height,
               shown:(viewSrc()===state.img?'photograph':'composite'), lines };
    }, setup);
    if (r.err){ console.log('  '+label.padEnd(24)+r.err); return; }
    console.log('  '+label.padEnd(24)+r.dims.padEnd(12)+r.mp+'MP   showing the '+r.shown.padEnd(11)
      +'grid lines across: '+r.lines);
  };
  await probe('all layers on', "LAYERS.dk=LAYERS.lt=LAYERS.hl=true; COMP.sig=null; viewRepaint();");
  await probe('one layer off',  "LAYERS.hl=false; COMP.sig=null; viewRepaint();");
  await probe('detail on Fine', "LAYERS.hl=true; DETAIL='fine'; COMP.sig=null; viewRepaint(); await new Promise(r=>setTimeout(r,2500));");
  console.log('  reference held at: '+(await pg.evaluate(()=>state.img.width+'x'+state.img.height)));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
