// The preview canvas now holds a stable size instead of wobbling by a pixel.
// The picture is drawn to fill it, so check the stretch that costs: where a
// known feature in the source lands, against where it should.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    // white, with a single black row at exactly the vertical midpoint
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); g.fillStyle='#fff'; g.fillRect(0,0,W,H);
    g.fillStyle='#000'; g.fillRect(0, H/2-6, W, 12);
    const b=await new Promise(r=>c.toBlob(r,'image/png'));
    await addRef(new File([b],'mid.png',{type:'image/png'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30';
    CELLSZ.u='cm'; CELLSZ.v=0.5; GRID_STYLE='diag'; GRID_ON=false; GRID_LAB=false;
  });
  const out = await pg.evaluate(async ()=>{
    const cv=$('fmtCanvas'); const rows=[];
    for (const z of [1, 1.4, 2.2, 2.6, 4]){
      FMT_ZOOM=z; FMT_OFF.x=0.5; FMT_OFF.y=0.5;
      fmtPreview();
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const q=cv.getContext('2d',{willReadFrequently:true});
      const col=Math.round(cv.width/2);
      const d=q.getImageData(col,0,1,cv.height).data;
      let first=-1,last=-1;
      for (let y=0;y<cv.height;y++){ if (d[y*4]<100){ if(first<0)first=y; last=y; } }
      const mid=(first+last)/2;
      const cr=cropRect();
      // where SHOULD it be? the source midpoint, mapped through the crop
      const want=( (3024/2) - cr.y ) / cr.h * cv.height;
      rows.push({z, cv:cv.width+'x'+cv.height, mid:+mid.toFixed(1),
                 want:+want.toFixed(1), off:+(mid-want).toFixed(2)});
    }
    return rows;
  });
  let bad=0;
  for (const r of out){
    const ok=Math.abs(r.off)<=1.0;
    if(!ok) bad++;
    console.log('  zoom '+String(r.z).padEnd(5)+'canvas '+r.cv.padEnd(11)
      +'feature at row '+String(r.mid).padStart(7)+'   expected '+String(r.want).padStart(7)
      +'   off by '+String(r.off).padStart(6)+'px   '+(ok?'ok':'FAIL misaligned'));
  }
  console.log('  '+(bad?('FAIL '+bad+' zoom levels misaligned'):'the picture lands where the grid expects it at every zoom'));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
