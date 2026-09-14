// How big is the base64 the bridge has to carry, in colour and in grey?
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
  const r = await pg.evaluate(async ()=>{
    // a detailed colour photograph, the case that was failing
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#f8e0c0'); gr.addColorStop(0.5,'#8a5a3a'); gr.addColorStop(1,'#201008');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=5; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<120000;i++){
      g.fillStyle='rgba('+Math.floor(rnd()*255)+','+Math.floor(rnd()*160)+','+Math.floor(rnd()*120)+',0.5)';
      g.fillRect(rnd()*W, rnd()*H, 4, 4);
    }
    const out={};
    const meas=(cv,label)=>{
      const res={};
      for (const q of [0.95, 0.9, 0.84, 0.76, 0.68]){
        const du=cv.toDataURL('image/jpeg',q);
        res[q]=+(du.length/1e6).toFixed(2);
      }
      out[label]={dims:cv.width+'x'+cv.height, mb:res};
    };
    meas(c,'colour 12MP');
    // the same picture in grey, which is what black-and-white projects export
    const gcv=document.createElement('canvas'); gcv.width=W; gcv.height=H;
    const gg=gcv.getContext('2d');
    gg.filter='grayscale(1)'; gg.drawImage(c,0,0); gg.filter='none';
    meas(gcv,'grey   12MP');
    // and at the size the export USED to be
    const s=document.createElement('canvas'); s.width=3024; s.height=2268;
    s.getContext('2d').drawImage(c,0,0,3024,2268);
    meas(s,'colour 6.9MP');
    return out;
  });
  console.log('  base64 the bridge must carry, in MB (limit set to 8.0)');
  console.log('  '+'image'.padEnd(14)+'dims'.padEnd(12)+['0.95','0.90','0.84','0.76','0.68'].map(x=>x.padStart(7)).join(''));
  for (const [k,v] of Object.entries(r))
    console.log('  '+k.padEnd(14)+v.dims.padEnd(12)
      +Object.values(v.mb).map(x=>String(x).padStart(7)).join(''));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
