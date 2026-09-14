// Two ways to get a grey preview over white. OLD: draw, then draw the canvas
// onto ITSELF through a grayscale filter. NEW: the filter rides the same
// draw. Same pixels? Cheaper? Tested on an opaque jpeg AND a transparent png.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof flatten==='function',null,{timeout:30000});
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const out = await pg.evaluate(async ()=>{
    const TW=1280, TH=960;
    const make=async (alpha)=>{
      const W=2048,H=1536; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d');
      if (!alpha){ const gr=g.createLinearGradient(0,0,W,H);
        gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H); }
      let sd=5; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
      // saturated colours make any greyscale discrepancy obvious
      for (let i=0;i<6000;i++){
        g.fillStyle='rgba('+Math.floor(rnd()*256)+','+Math.floor(rnd()*256)+','
          +Math.floor(rnd()*256)+','+(alpha? (0.2+rnd()*0.8).toFixed(2) : 1)+')';
        g.fillRect(rnd()*W, rnd()*H, 40, 40);
      }
      const b=await new Promise(r=>c.toBlob(r, alpha?'image/png':'image/jpeg', .95));
      const u=URL.createObjectURL(b);
      return await new Promise((res,rej)=>{const i=new Image(); i.onload=()=>res(i); i.onerror=rej; i.src=u;});
    };
    const flush=cv=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
    const OLD=(img)=>{ const t=document.createElement('canvas'); t.width=TW;t.height=TH;
      const q=t.getContext('2d'); q.imageSmoothingQuality='high';
      flatten(q,TW,TH); q.drawImage(img,0,0,TW,TH);
      q.filter='grayscale(1)'; q.drawImage(t,0,0); q.filter='none';
      forceGray(t); return t; };
    const NEW=(img)=>{ const t=document.createElement('canvas'); t.width=TW;t.height=TH;
      const q=t.getContext('2d'); q.imageSmoothingQuality='high';
      flatten(q,TW,TH);
      q.filter='grayscale(1)'; q.drawImage(img,0,0,TW,TH); q.filter='none';
      forceGray(t); return t; };
    const res={};
    for (const alpha of [false,true]){
      const img=await make(alpha);
      const time=fn=>{ fn(img); const ts=[];
        for(let k=0;k<5;k++){ const a=performance.now(); const t=fn(img); flush(t); ts.push(performance.now()-a); }
        ts.sort((x,y)=>x-y); return Math.round(ts[2]); };
      const to=time(OLD), tn=time(NEW);
      const pa=OLD(img).getContext('2d',{willReadFrequently:true}).getImageData(0,0,TW,TH).data;
      const pb=NEW(img).getContext('2d',{willReadFrequently:true}).getImageData(0,0,TW,TH).data;
      let max=0, over=0, sum=0, n=0, nonGrey=0;
      for (let i=0;i<pa.length;i+=4){
        for (let k=0;k<3;k++){ const d=Math.abs(pa[i+k]-pb[i+k]); if(d>max)max=d; if(d>2)over++; sum+=d; n++; }
        if (pb[i]!==pb[i+1]||pb[i+1]!==pb[i+2]) nonGrey++;
        if (pb[i+3]!==255) nonGrey++;
      }
      res[alpha?'transparent png':'opaque jpeg']=
        {old:to, neu:tn, max, over, mean:+(sum/n).toFixed(3), nonGrey};
    }
    return res;
  });
  for (const [k,v] of Object.entries(out))
    console.log('  '+k.padEnd(17)+'old '+String(v.old).padStart(4)+'ms   new '+String(v.neu).padStart(4)
      +'ms    maxdiff '+String(v.max).padStart(3)+'  pixels>2 '+String(v.over).padStart(7)
      +'  mean '+v.mean+'   non-grey/transparent px in new: '+v.nonGrey);
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
