// What upscaling the export actually costs: file size, encode time, memory.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const r = await pg.evaluate(async ()=>{
    // a real-ish colour photograph at 12MP, the reference's true resolution
    const W=4032,H=3024;
    const src=document.createElement('canvas'); src.width=W; src.height=H;
    const g=src.getContext('2d');
    const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#f8e0c0'); gr.addColorStop(0.5,'#8a5a3a'); gr.addColorStop(1,'#201008');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=5; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<160000;i++){
      g.fillStyle='rgba('+Math.floor(rnd()*255)+','+Math.floor(rnd()*170)+','+Math.floor(rnd()*130)+',0.45)';
      g.fillRect(rnd()*W, rnd()*H, 3, 3);
    }
    const out=[];
    for (const mult of [1, 1.18, 1.5, 2]){
      const w=Math.round(W*mult), h=Math.round(H*mult);
      const px=w*h;
      if (px > 70e6){ out.push({mult, w, h, note:'too large to attempt'}); continue; }
      let c=null, t0=performance.now(), built=0, enc=0, len=0, err='';
      try{
        c=document.createElement('canvas'); c.width=w; c.height=h;
        const cg=c.getContext('2d');
        cg.imageSmoothingQuality='high';
        cg.drawImage(src,0,0,w,h);
        // the grid is drawn at EXPORT size, so it is genuinely sharper
        cg.strokeStyle='rgba(255,255,255,0.9)'; cg.lineWidth=Math.max(1,2*mult);
        const step=w/14;
        for (let x=step;x<w;x+=step){ cg.beginPath(); cg.moveTo(x,0); cg.lineTo(x,h); cg.stroke(); }
        for (let y=step;y<h;y+=step){ cg.beginPath(); cg.moveTo(0,y); cg.lineTo(w,y); cg.stroke(); }
        cg.getImageData(0,0,1,1);
        built=performance.now()-t0;
        const t1=performance.now();
        const du=c.toDataURL('image/jpeg',0.95);
        enc=performance.now()-t1; len=du.length;
      }catch(e){ err=String(e).slice(0,40); }
      out.push({mult, w, h, mp:+(px/1e6).toFixed(1),
        canvasMB:+(px*4/1e6).toFixed(0),
        built:Math.round(built), enc:Math.round(enc),
        fileMB:+(len*0.75/1e6).toFixed(2), b64MB:+(len/1e6).toFixed(2), err});
    }
    return out;
  });
  console.log('  export at      pixels   canvas RAM   compose   encode   file    base64');
  for (const o of r){
    if (o.note){ console.log('  '+(o.mult+'x').padEnd(15)+(o.w+'x'+o.h).padEnd(9)+o.note); continue; }
    console.log('  '+(o.mult+'x  '+o.w+'x'+o.h).padEnd(24)+(o.mp+'MP').padEnd(9)
      +(o.canvasMB+'MB').padEnd(13)+(o.built+'ms').padEnd(10)+(o.enc+'ms').padEnd(9)
      +(o.fileMB+'MB').padEnd(8)+(o.b64MB+'MB')+(o.err?('  ERR '+o.err):''));
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
