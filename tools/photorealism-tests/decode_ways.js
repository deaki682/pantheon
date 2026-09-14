// COLD: a 12MP jpeg blob -> a 1280x960 preview canvas. Each run uses a blob
// the engine has never decoded, so we measure the decode, not a cache hit.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const out = await pg.evaluate(async ()=>{
    const W=4032,H=3024, TW=1280, TH=960, N=4;
    // N distinct blobs so no run reuses another's decode
    const blobs=[];
    for (let n=0;n<N+1;n++){
      const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
      let sd=7+n*13; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
      for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.45)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
      blobs.push(await new Promise(r=>c.toBlob(r,'image/jpeg',.92)));
    }
    const flush=cv=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
    const viaImg=async b=>{
      const u=URL.createObjectURL(b);
      const i=await new Promise((res,rej)=>{const x=new Image(); x.onload=()=>res(x); x.onerror=rej; x.src=u;});
      const t=document.createElement('canvas'); t.width=TW; t.height=TH;
      const q=t.getContext('2d'); q.imageSmoothingQuality='high';
      q.drawImage(i,0,0,TW,TH); flush(t);
      URL.revokeObjectURL(u); return t;
    };
    const viaBitmap=q=>async b=>{
      const bm=await createImageBitmap(b,{resizeWidth:TW,resizeHeight:TH,
        resizeQuality:q, imageOrientation:'from-image'});
      const t=document.createElement('canvas'); t.width=TW; t.height=TH;
      t.getContext('2d').drawImage(bm,0,0); flush(t); bm.close(); return t;
    };
    const ways={ '<img> + drawImage': viaImg,
                 'createImageBitmap high': viaBitmap('high'),
                 'createImageBitmap medium': viaBitmap('medium'),
                 'createImageBitmap low': viaBitmap('low') };
    const res={};
    for (const [name,fn] of Object.entries(ways)){
      await fn(blobs[N]);                       // warm the code path only
      const ts=[];
      for (let k=0;k<N;k++){
        const a=performance.now(); await fn(blobs[k]); ts.push(performance.now()-a);
      }
      ts.sort((x,y)=>x-y);
      res[name]={ms:Math.round(ts[Math.floor(N/2)]), all:ts.map(x=>Math.round(x)).join('/')};
    }
    return res;
  });
  console.log('  cold 4032x3024 jpeg -> 1280x960 preview');
  for (const [k,v] of Object.entries(out))
    console.log('  '+k.padEnd(26)+String(v.ms).padStart(5)+'ms   ('+v.all+')');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
