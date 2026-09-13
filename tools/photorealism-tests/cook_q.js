// The tools must stay the same physical size. At q=3 the marks must be
// identical to q=1, only sampled more finely.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof cookFineQ==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});

  // the tool geometry itself: run the worker's own opening at q=1 and q=3 on
  // the SAME picture and compare the marks it keeps
  const geo = await pg.evaluate(async ()=>{
    const mk=(W,H,q)=>{
      // a test field: strokes of several widths, in PAPER terms
      const d=new Float32Array(W*H);
      for (const [wpx,y0] of [[1,0.15],[2,0.3],[3,0.45],[5,0.6],[9,0.78]]){
        const w=Math.max(1,Math.round(wpx*q));
        const y=Math.round(H*y0);
        for (let dy=0; dy<w; dy++) for (let x=Math.round(W*0.1); x<W*0.9; x++)
          d[(y+dy)*W+x]=255;
      }
      return d;
    };
    const run=(q)=>new Promise(res=>{
      const W=Math.round(300*q), H=Math.round(300*q);
      const wk=new Worker(URL.createObjectURL(new Blob([DETAIL_SRC],{type:'text/javascript'})));
      const dD=mk(W,H,q), lD=new Float32Array(W*H), hl=new Float32Array(W*H);
      wk.onmessage=ev=>{ if (!ev.data.dD) return;
        const a=ev.data.dD; const keep=[];
        for (const [wpx,y0] of [[1,0.15],[2,0.3],[3,0.45],[5,0.6],[9,0.78]]){
          const y=Math.round(H*y0)+Math.floor(Math.max(1,Math.round(wpx*q))/2);
          keep.push(a[y*W+Math.round(W*0.5)]>40 ? 1 : 0);
        }
        wk.terminate(); res(keep.join(''));
      };
      wk.postMessage({dD,lD,hl,W,H,shape:'mid',q},[dD.buffer,lD.buffer,hl.buffer]);
    });
    return { q1: await run(1), q3: await run(3) };
  });
  console.log('strokes the 3-across tool keeps (1,2,3,5,9 px of paper):');
  console.log('   sampled at 1x :', geo.q1);
  console.log('   sampled at 3x :', geo.q3);
  console.log('   same tool     :', geo.q1===geo.q3 ? 'ok' : 'FAIL - the tool changed size');
  console.log('page errors:', errs.length?errs.slice(0,3):'none');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
