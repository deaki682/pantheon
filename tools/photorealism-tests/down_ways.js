// 4032x3024 already-decoded image -> a 1280x960 preview. Which way is cheapest,
// and how different do they look? (flushed, so deferred work is counted)
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
    const W=4032,H=3024, TW=1280, TH=960;
    const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=999; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.45)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    const url=URL.createObjectURL(blob);
    const img=await new Promise((res,rej)=>{const i=new Image(); i.onload=()=>res(i); i.onerror=rej; i.src=url;});
    const flush=cv=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
    const target=()=>{ const t=document.createElement('canvas'); t.width=TW; t.height=TH; return t; };
    const px=cv=>{ const d=cv.getContext('2d',{willReadFrequently:true}).getImageData(0,0,TW,TH).data;
      const a=[]; for(let i=0;i<d.length;i+=4*997) a.push(d[i]); return a; };
    const ways={
      'one shot, high': ()=>{ const t=target(); const q=t.getContext('2d');
        q.imageSmoothingQuality='high'; q.drawImage(img,0,0,TW,TH); return t; },
      'one shot, medium': ()=>{ const t=target(); const q=t.getContext('2d');
        q.imageSmoothingQuality='medium'; q.drawImage(img,0,0,TW,TH); return t; },
      'one shot, low': ()=>{ const t=target(); const q=t.getContext('2d');
        q.imageSmoothingQuality='low'; q.drawImage(img,0,0,TW,TH); return t; },
      'halve then high': ()=>{ const h1=document.createElement('canvas');
        h1.width=W>>1; h1.height=H>>1; const q1=h1.getContext('2d');
        q1.imageSmoothingQuality='medium'; q1.drawImage(img,0,0,h1.width,h1.height);
        const t=target(); const q=t.getContext('2d');
        q.imageSmoothingQuality='high'; q.drawImage(h1,0,0,TW,TH); return t; },
    };
    const res={};
    let ref=null;
    for (const [name,fn] of Object.entries(ways)){
      fn(); // warm
      const ts=[];
      for (let k=0;k<5;k++){ const a=performance.now(); const t=fn(); flush(t); ts.push(performance.now()-a); }
      ts.sort((x,y)=>x-y);
      const t=fn(); flush(t);
      const p=px(t);
      if (!ref) ref=p;
      let max=0,sum=0;
      for (let i=0;i<p.length;i++){ const d=Math.abs(p[i]-ref[i]); if(d>max)max=d; sum+=d; }
      res[name]={ms:Math.round(ts[2]), max, mean:+(sum/p.length).toFixed(2)};
    }
    URL.revokeObjectURL(url);
    return res;
  });
  console.log('  strategy              ms    vs high: max   mean');
  for (const [k,v] of Object.entries(out))
    console.log('  '+k.padEnd(20)+String(v.ms).padStart(4)+'ms'
      +String(v.max).padStart(13)+String(v.mean).padStart(8));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
