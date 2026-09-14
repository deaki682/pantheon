// Where do the ~330 synchronous ms of "open the edit window" actually go?
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(Math.random()*W,Math.random()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  await pg.waitForTimeout(8000);
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });

  const runs = [];
  for (let rep=0; rep<5; rep++){
    const r = await pg.evaluate(async ()=>{
      const T={}; const now=()=>performance.now();
      let t=now();
      const rec=await galGet(galActive);            T.galGet=now()-t; t=now();
      const src=await openSrc(galActive, rec.blob); T.openSrc=now()-t; t=now();
      const i=await blobImage(src||rec.blob);       T.decode=now()-t; t=now();
      T.srcPx = i.width+'x'+i.height;
      const CAP=refCap();
      const sc=Math.min(1, CAP/Math.max(i.width,i.height));
      ED.srcImg=i; ED.srcW=Math.round(i.width*sc); ED.srcH=Math.round(i.height*sc);
      T.cap = ED.srcW+'x'+ED.srcH;
                                                    t=now();
      // edOpen internals, split
      ED.on=true; ED.orig=null; ED.gid=galActive; ED.mode='tone';
      ED.colr=isColor(galActive);
      ED.z={s:1,x:0,y:0}; ED.showOrig=false;
      ED.R = editLoad(galActive) || {...EDIT_DEF};
      show('scrEdit');                              T.show=now()-t; t=now();
      edSync();                                     T.edSync=now()-t; t=now();
      // edBuildPre, split by hand
      {
        const R=ED.R, s2=ED.srcImg, sw=ED.srcW, sh=ED.srcH;
        const k=Math.min(1,1280/Math.max(sw,sh));
        const small=document.createElement('canvas');
        small.width=Math.max(2,Math.round(sw*k)); small.height=Math.max(2,Math.round(sh*k));
        T.prePx = small.width+'x'+small.height;
        const sg=small.getContext('2d'); sg.imageSmoothingQuality='high';
        flatten(sg,small.width,small.height);       T.flatten=now()-t; t=now();
        sg.drawImage(s2,0,0,small.width,small.height); T.downscale=now()-t; t=now();
        if (!ED.colr){
          sg.filter='grayscale(1)'; sg.drawImage(small,0,0); sg.filter='none';
                                                    T.grayFilter=now()-t; t=now();
          forceGray(small);                         T.forceGray=now()-t; t=now();
        }
        ED.pre=editApply(small,{...EDIT_DEF,rot:R.rot,fh:R.fh,fv:R.fv,ang:R.ang});
                                                    T.editApply=now()-t; t=now();
        ED.gray=null; ED.preData=null; ED.tone=null; ED.toneKey=null;
      }
      edRender();                                   T.edRender=now()-t; t=now();
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      T.paint=now()-t;
      edClose(false); await new Promise(r=>setTimeout(r,300));
      for (const k in T) if (typeof T[k]==='number') T[k]=Math.round(T[k]);
      return T;
    });
    runs.push(r);
    await pg.waitForTimeout(400);
  }
  const keys = Object.keys(runs[0]).filter(k=>typeof runs[0][k]==='number');
  const med=a=>{const b=[...a].sort((x,y)=>x-y);return b[Math.floor(b.length/2)];};
  console.log('src '+runs[0].srcPx+'  capped '+runs[0].cap+'  preview '+runs[0].prePx);
  const rows = keys.map(k=>[k, med(runs.map(r=>r[k])), runs.map(r=>r[k]).join('/')]);
  rows.sort((a,b)=>b[1]-a[1]);
  let tot=0; for (const [,m] of rows) tot+=m;
  for (const [k,m,all] of rows) console.log('  '+String(m).padStart(5)+'ms  '+k.padEnd(12)+'  ('+all+')');
  console.log('  ----- total '+tot+'ms');
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
