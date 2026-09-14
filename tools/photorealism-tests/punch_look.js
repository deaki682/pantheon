// Auto vs punch over a full tonal ramp - the midtones are where auto dies.
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
  await pg.evaluate(async ()=>{
    // a left-to-right ramp black->white, so every tone is represented
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    const gr=g.createLinearGradient(0,0,W,0);
    gr.addColorStop(0,'#000'); gr.addColorStop(1,'#fff');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
    await addRef(new File([b],'ramp.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30';
    CELLSZ.u='cm'; CELLSZ.v=2; GRID_STYLE='sq'; GRID_ON=true; GRID_LAB=false;
    GRID_OP=0.85; GRID_THK=2;
  });
  const fs=require('fs');
  for (const col of ['auto','punch']){
    const r = await pg.evaluate(async (c)=>{
      GRID_COL=c; FMT_GRID=null; FMT_ZOOM=1; FMT_OFF.x=0.5; FMT_OFF.y=0.5;
      fmtPreview();
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      // read the contrast between the line and its neighbour along the ramp
      const cv=$('fmtCanvas'), q=cv.getContext('2d',{willReadFrequently:true});
      const row=Math.round(cv.height*0.5);
      const d=q.getImageData(0,row,cv.width,1).data;
      // find vertical grid lines: columns that differ most from their surroundings
      const out=[];
      for (let x=4;x<cv.width-4;x++){
        const here=d[x*4], near=(d[(x-4)*4]+d[(x+4)*4])/2;
        if (Math.abs(here-near)>10) out.push({x, line:here, bg:Math.round(near),
          contrast:Math.round(Math.abs(here-near))});
      }
      // one sample per line
      const lines=[]; let last=-99;
      for (const o of out){ if (o.x-last>8) lines.push(o); last=o.x; }
      return lines;
    }, col);
    const buf = await pg.locator('#fmtCanvas').screenshot();
    fs.writeFileSync('punch_'+col+'.png', buf);
    const cs=r.map(o=>o.contrast);
    console.log('  '+col.padEnd(6)+r.length+' lines   contrast vs backdrop: min '
      +Math.min(...cs)+'  median '+cs.sort((a,b)=>a-b)[Math.floor(cs.length/2)]
      +'  max '+Math.max(...cs));
    console.log('         per line: '+r.map(o=>o.bg+'->'+o.line).join('  '));
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
