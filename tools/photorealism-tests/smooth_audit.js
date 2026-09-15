// Three times now the expensive smoothing filter has been the whole cost of
// an interaction, on a resample where it bought nothing. Rather than find a
// fourth by tripping over it: instrument every drawImage in the app, drive a
// real session, and rank what actually runs by how much it reduces. Below
// about 2x reduction the filter is measurably indistinguishable from
// bilinear, so anything hot and under that is paying for nothing.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    // instrument before any app code runs
    const P=CanvasRenderingContext2D.prototype;
    const realDraw=P.drawImage;
    const qd=Object.getOwnPropertyDescriptor(P,'imageSmoothingQuality');
    window.__SM={};
    Object.defineProperty(P,'imageSmoothingQuality',{
      get(){ return qd.get.call(this); },
      set(v){ this.__q=v; qd.set.call(this,v); }, configurable:true });
    P.drawImage=function(img, ...a){
      try{
        let sw,sh,dw,dh;
        const iw = img.naturalWidth||img.width||0, ih = img.naturalHeight||img.height||0;
        if (a.length>=8){ sw=a[2]; sh=a[3]; dw=a[6]; dh=a[7]; }
        else if (a.length>=4){ sw=iw; sh=ih; dw=a[2]; dh=a[3]; }
        else { sw=iw; sh=ih; dw=iw; dh=ih; }
        if (dw>0 && sw>0){
          const red = sw/dw;
          const q = this.__q || 'low';
          const site = (new Error()).stack.split('\n')[2]||'?';
          const k = q+' | reduction '+(red<1 ? 'UPSCALE '+(1/red).toFixed(1)+'x'
                    : red.toFixed(2)+'x') .padEnd(10)
                    +' | '+Math.round(sw)+'x'+Math.round(sh)+' -> '+Math.round(dw)+'x'+Math.round(dh);
          const e=window.__SM[k]||(window.__SM[k]={n:0, mpx:0, site});
          e.n++; e.mpx += (dw*dh)/1e6;
        }
      }catch(e){}
      return realDraw.call(this, img, ...a);
    };
  });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  // a realistic session
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
    // crop screen: pan and pinch
    show('scrFormat'); await new Promise(r=>setTimeout(r,700));
    for (let i=0;i<8;i++){ typeof fmtLive==='function'&&fmtLive(true);
      FMT_OFF.x=0.4+0.02*i; FMT_ZOOM=1.6; fmtPreview(); await new Promise(r=>setTimeout(r,40)); }
    if (typeof FMT_LIVE!=='undefined') FMT_LIVE=0; fmtPreview();
    // into the drawing
    $('fmtGo').click();
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,80)); }
    await new Promise(r=>setTimeout(r,6000));
    // pan and zoom the reference
    for (let i=0;i<8;i++){ view.x-=14; view.y-=7; applyView(); await new Promise(r=>setTimeout(r,40)); }
    view.s*=2; applyView(); await new Promise(r=>setTimeout(r,300));
    // layers and detail
    LAYERS.dk=false; COMP.sig=null; paintWorld(); await new Promise(r=>setTimeout(r,300));
    DETAIL='fine'; COMP.sig=null; paintWorld(); await new Promise(r=>setTimeout(r,800));
    DETAIL='ultra'; COMP.sig=null; paintWorld(); await new Promise(r=>setTimeout(r,400));
    // the editor
    await edOpenFor('tone'); await new Promise(r=>setTimeout(r,700));
    for (let i=0;i<5;i++){ ED.z.s=1+0.4*i; edPaint(); await new Promise(r=>setTimeout(r,60)); }
    edClose(false); await new Promise(r=>setTimeout(r,600));
    // compare
    show('scrCompare'); await new Promise(r=>setTimeout(r,900));
    show('scrMain'); await new Promise(r=>setTimeout(r,600));
    show('scrUpload'); await new Promise(r=>setTimeout(r,600));
  });
  const rows = await pg.evaluate(()=>Object.entries(window.__SM)
    .map(([k,v])=>({k, n:v.n, mpx:+v.mpx.toFixed(1)}))
    .sort((a,b)=>b.mpx-a.mpx));
  console.log('every resample the session ran, by destination megapixels touched\n');
  for (const r of rows.slice(0,26))
    console.log('  '+String(r.n).padStart(4)+'x  '+String(r.mpx).padStart(7)+' Mpx   '+r.k);
  const waste = rows.filter(r=>r.k.startsWith('high') &&
    (r.k.includes('UPSCALE') || (parseFloat(r.k.split('reduction ')[1])||9) < 2));
  console.log('\nHIGH quality where the reduction is under 2x (the filter buys nothing there):');
  if (!waste.length) console.log('   none');
  for (const r of waste) console.log('  '+String(r.n).padStart(4)+'x  '+String(r.mpx).padStart(7)+' Mpx   '+r.k);
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
