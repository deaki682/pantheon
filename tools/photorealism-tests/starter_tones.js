// Which starter lives in the midtones? That is where an inverting grid dies:
// invert a value near 128 and you land near 128.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const pg = await (await br.newContext({viewport:{width:800,height:600}})).newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  const names=['starter-soft.jpg','starter-wet-c.jpg','starter-soft-c.jpg','starter-guy-c.jpg','starter-freckles-c.jpg'];
  console.log('  starter               mean   % in the dead band (96-160)   % light (>160)');
  for (const n of names){
    const r = await pg.evaluate(async (name)=>{
      const res=await fetch(name); if(!res.ok) return null;
      const b=await res.blob();
      const u=URL.createObjectURL(b);
      const i=await new Promise((ok,no)=>{const x=new Image();x.onload=()=>ok(x);x.onerror=no;x.src=u;});
      const c=document.createElement('canvas'); c.width=400; c.height=Math.round(400*i.height/i.width);
      const g=c.getContext('2d',{willReadFrequently:true});
      g.drawImage(i,0,0,c.width,c.height);
      const d=g.getImageData(0,0,c.width,c.height).data;
      let sum=0,n2=0,dead=0,light=0;
      for (let k=0;k<d.length;k+=4){
        const v=(d[k]*0.2126+d[k+1]*0.7152+d[k+2]*0.0722);
        sum+=v; n2++;
        if (v>=96&&v<=160) dead++;
        if (v>160) light++;
      }
      URL.revokeObjectURL(u);
      return {mean:Math.round(sum/n2), dead:Math.round(dead/n2*100), light:Math.round(light/n2*100),
              dims:i.width+'x'+i.height};
    }, n);
    if (!r){ console.log('  '+n.padEnd(22)+'not found'); continue; }
    console.log('  '+n.padEnd(22)+String(r.mean).padStart(4)
      +String(r.dead).padStart(22)+'%'+String(r.light).padStart(16)+'%   '+r.dims);
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
