// How BROKEN is the line? Walk each grid line and count how many times it
// changes between white and black along its length. One or two changes is a
// line that follows the picture; dozens is the speckle being reported.
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
  await pg.evaluate(async (CELL_TEST)=>{
    const r=await fetch('starter-guy.jpg'); const b=await r.blob();
    await addRef(new File([b],'starter-guy.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    CELLSZ.u='cm'; CELLSZ.v=CELL_TEST; GRID_ON=true; GRID_STYLE='sq'; GRID_LAB=false;
    GRID_OP=0.9; GRID_THK=2; GRID_COL='punch';
  }, +(process.argv[2]||3));
  await pg.waitForTimeout(7000);
  const fs=require('fs');
  console.log('  cell     changes/line   SPECKS   longest run');
  for (const f of [1]){
    const r = await pg.evaluate(async (frac)=>{
       drawGrid();
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      const cv=$('gridCv'), q=cv.getContext('2d',{willReadFrequently:true});
      const d=q.getImageData(0,0,cv.width,cv.height).data;
      // find the columns that ARE vertical lines, then walk each one
      // the sheet is a band in the middle of the viewport, so find where the
      // grid actually IS before looking for its lines
      let y0=cv.height, y1=0;
      for (let y=0;y<cv.height;y++) for (let x=0;x<cv.width;x+=3)
        if (d[(y*cv.width+x)*4+3]>120){ if(y<y0)y0=y; if(y>y1)y1=y; break; }
      const band=Math.max(1,y1-y0);
      const colHits=new Uint32Array(cv.width);
      for (let y=y0;y<=y1;y++) for (let x=0;x<cv.width;x++)
        if (d[(y*cv.width+x)*4+3]>120) colHits[x]++;
      const cols=[]; let last=-99;
      for (let x=0;x<cv.width;x++)
        if (colHits[x]>band*0.5 && x-last>6){ cols.push(x); last=x; }
      let changes=0, runs=[], lines=0;
      for (const x of cols){
        let prev=null, run=0; lines++;
        for (let y=y0;y<=y1;y++){
          const i=(y*cv.width+x)*4;
          if (d[i+3]<120) continue;
          const w=d[i]>128;
          if (prev===null){ prev=w; run=1; continue; }
          if (w!==prev){ changes++; runs.push(run); run=1; prev=w; } else run++;
        }
        runs.push(run);
      }
      // a SPECK is a short run of the opposite colour - one intersection or a
      // few pixels flipping in an otherwise solid line. That is the thing
      // being reported, not the long clean changes.
      // a speck is a run shorter than HALF a segment - at a fine grid the
      // segments themselves are only a few pixels, and counting those as
      // specks flagged every one of them
      const seg=Math.max(3, (y1-y0)/Math.max(1,(cols.length||1)));
      const specks=runs.filter(r=>r<Math.max(4, seg*0.45)).length;
      runs.sort((a,b)=>b-a);
      return { lines, changes, band:(y1-y0), specks,
               perLine:+(changes/Math.max(1,lines)).toFixed(1), longest:runs[0]||0 };
    }, f);
    console.log('  '+String(f).padEnd(9)+String(r.perLine).padStart(8)
      +String(r.specks).padStart(12)+String(r.longest).padStart(12)+'px');
    const buf = await pg.locator('#viewport').screenshot();
    fs.writeFileSync('tune_c'+(process.argv[2]||3).toString().replace('.','_')+'_'+String(f).replace('.','_')+'.png', buf);
  }
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
