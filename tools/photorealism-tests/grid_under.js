// Colour mode, the default (auto) grid: tapping through the underpainting
// options changes what is UNDER the grid, so the grid's own per-cell
// black/white decision has to be re-made. The report is that it is not -
// the lattice stays coloured for the photograph, so over a pale ground half
// the lines are white on white. Sample the grid canvas in each state and see.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', OUT=process.argv[3]||'.';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    // a picture with a clearly DARK half and a clearly LIGHT half, so a
    // correct map has both colours in it and a stale one is obvious
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    g.fillStyle='#111'; g.fillRect(0,0,W/2,H);
    g.fillStyle='#f2f2f2'; g.fillRect(W/2,0,W/2,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));
    await addRef(new File([b],'half.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    REFMODE='c';                       // colour mode
    $('unit').value='cm'; $('widthIn').value='30';
    show('scrFormat'); await new Promise(r=>setTimeout(r,400));
    $('fmtGo').onclick();
    for (let i=0;i<600;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    GRID_COL='auto'; GRID_ON=true;
    await new Promise(r=>setTimeout(r,800));
  });
  await pg.evaluate(()=>{ window.__gridDraws=0;
    const f=window.drawGrid; window.drawGrid=function(){ window.__gridDraws++; return f.apply(this,arguments); }; });
  console.log('  punch active:', await pg.evaluate(()=>punchOn()),
              '  mode:', await pg.evaluate(()=>REFMODE));
  // read the lattice's own ink across the canvas in each ground state
  // drive the REAL buttons, the way the artist does
  const read = async (label, btn) => {
    await pg.evaluate(async (b)=>{
      if (b) $(b).onclick();
      await new Promise(r=>setTimeout(r,650));
    }, btn);
    return await pg.evaluate((label)=>{
      const cv=$('gridCv'), g=cv.getContext('2d');
      const d=g.getImageData(0,0,cv.width,cv.height).data;
      let dark=0, light=0, n=0;
      for (let i=0;i<d.length;i+=4){
        if (d[i+3]<40) continue;        // not lattice
        n++;
        const v=(d[i]+d[i+1]+d[i+2])/3;
        if (v<90) dark++; else if (v>165) light++;
      }
      // what the paper actually looks like underneath, for comparison
      const ref=refCanvas(); let refLight=0, refN=0;
      if (ref && ref.width){
        const rg=ref.getContext('2d');
        const rd=rg.getImageData(0,0,ref.width,ref.height).data;
        for (let i=0;i<rd.length;i+=4*97){
          refN++; if ((rd[i]+rd[i+1]+rd[i+2])/3 > 150) refLight++;
        }
      }
      // ...and the decisive question: does FORCING a redraw change the ink?
      // If it does, the lattice simply was not re-run. If it does not, the
      // staleness is inside the colouring.
      drawGrid();
      const d2=g.getImageData(0,0,cv.width,cv.height).data;
      let dark2=0, light2=0;
      for (let i=0;i<d2.length;i+=4){
        if (d2[i+3]<40) continue;
        const v=(d2[i]+d2[i+1]+d2[i+2])/3;
        if (v<90) dark2++; else if (v>165) light2++;
      }
      return { label, n, dark, light, dark2, light2,
               paperLight:refN?Math.round(100*refLight/refN):-1 };
    }, label);
  };
  const rows=[];
  rows.push(await read('the photograph', null));
  rows.push(await read('Detailed ground', 'uFull'));
  rows.push(await read('Shading ground', 'uSh'));
  rows.push(await read('Midtone ground', 'uMid'));
  rows.push(await read('None - blank paper', 'uNone'));
  for (const r of rows)
    console.log('  '+r.label.padEnd(22)+'lattice '+String(r.n).padStart(6)
      +'   dark '+String(r.dark).padStart(6)+'  light '+String(r.light).padStart(6)
      +'   paper '+String(r.paperLight).padStart(3)+'% light'
      +'   | forced redraw: dark '+String(r.dark2).padStart(6)
      +'  light '+String(r.light2).padStart(6));
  // a map that never re-keys is the bug
  // and the test that matters: on BLANK PAPER the lattice must be all dark -
  // a white line on white paper is an invisible line
  const blank=rows[rows.length-1];
  ok(blank.paperLight>80, 'blank paper really is pale ('+blank.paperLight+'% light)');
  ok(blank.light===0, 'no white lattice on blank paper (found '+blank.light+' white px)');
  ok(blank.light2===0, '...and none after a forced redraw either (found '+blank.light2+')');
  ok(errs.length===0, 'no page errors'+(errs.length?' -> '+errs[0]:''));
  require('fs').writeFileSync(OUT+'/grid_under.png', await pg.screenshot());
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ngrid adapts');
  process.exit(bad?1:0);
})();
