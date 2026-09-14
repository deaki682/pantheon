// Instrument the REAL functions by wrapping them - the old probe reimplemented
// edBuildPre inline and so measured a copy that had drifted from the code.
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
    let sd=3; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
  });
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await pg.evaluate(()=>{
    window.__T={};
    const wrap=(name, isAsync)=>{
      const o=window[name]; if (typeof o!=='function') return;
      window[name]=isAsync
        ? async function(...a){ const t=performance.now();
            try{ return await o.apply(this,a); } finally{ window.__T[name]=(window.__T[name]||0)+(performance.now()-t); } }
        : function(...a){ const t=performance.now();
            try{ return o.apply(this,a); } finally{ window.__T[name]=(window.__T[name]||0)+(performance.now()-t); } };
    };
    for (const n of ['edBuildPre','edRender','edSync','editApply','flatten','forceGray',
                     'show','edOpen','editLoad','slFillAll','isColor','refCap','edEnsureGray'])
      wrap(n,false);
    for (const n of ['galGet','openSrc','blobImage']) wrap(n,true);
  });
  const runs=[];
  for (let r=0;r<5;r++){
    const t = await pg.evaluate(async ()=>{
      window.__T={};
      const t0=performance.now();
      await edOpenFor('tone');
      const sync=performance.now()-t0;
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const total=performance.now()-t0;
      const T={...window.__T};
      for (const k in T) T[k]=Math.round(T[k]);
      T.__sync=Math.round(sync); T.__total=Math.round(total);
      edClose(false);
      return T;
    });
    runs.push(t);
    await pg.waitForTimeout(500);
  }
  const keys=[...new Set(runs.flatMap(Object.keys))];
  const med=a=>{const b=[...a].sort((x,y)=>x-y);return b[Math.floor(b.length/2)];};
  const rows=keys.map(k=>[k, med(runs.map(r=>r[k]||0)), runs.map(r=>r[k]||0).join('/')]);
  rows.sort((a,b)=>b[1]-a[1]);
  for (const [k,m,all] of rows)
    console.log('  '+String(m).padStart(5)+'ms  '+k.padEnd(14)+'  ('+all+')');
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
