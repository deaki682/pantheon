// The grid must still be ON THE DRAWING when the where-to-save modal is up.
// Downloading frees the two overlay canvases - 28-47MB of overscan band the
// export does not need - and the export used to ask where to save FIRST and
// encode after, so the drawing sat there with no lattice on it for as long as
// the modal and the system picker behind it took. Half a minute on a tablet,
// and it looks as though the grid will be missing from the file.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const dev of [{n:'phone', w:411, h:891}, {n:'tab', w:800, h:1280}]){
    const ctx = await br.newContext({ viewport:{width:dev.w,height:dev.h}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await pg.evaluate(async ()=>{
      const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
      await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      show('scrFormat'); await new Promise(r=>setTimeout(r,400));
      $('fmtGo').onclick();
      for (let i=0;i<400;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,800));
    });
    const r = await pg.evaluate(async ()=>{
      const grid=()=>{ const c=$('gridCv'); return c ? c.width : 0; };
      const before=grid();
      // stand in for the Android bridge: the save door the export goes through
      let sent=null;
      window.RealismCam = { saveImage:(f,m,b)=>{ sent=b?b.length:0; },
                            saveImageAsk:(f,m,b)=>{ sent=b?b.length:0; } };
      const p = exportImage();
      // wait for the where-to-save modal
      let up=false;
      for (let i=0;i<600;i++){
        if (getComputedStyle($('dlwModal')).display!=='none'){ up=true; break; }
        await new Promise(r=>setTimeout(r,50));
      }
      await new Promise(r=>setTimeout(r,250));   // let the repaint land
      const whileAsking = grid();
      $('dlwPics').onclick();
      await p;
      await new Promise(r=>setTimeout(r,400));
      return { before, up, whileAsking, after:grid(), sent };
    });
    console.log(dev.n+'  grid canvas: '+r.before+'px before, '+r.whileAsking+
                'px while the modal is up, '+r.after+'px after');
    ok(r.before>1,       dev.n+': the grid is on the drawing to begin with');
    ok(r.up,             dev.n+': the where-to-save modal came up');
    ok(r.whileAsking>1,  dev.n+': and the grid is STILL on the drawing while it asks');
    ok(r.after>1,        dev.n+': and after the save');
    ok(r.sent>0,         dev.n+': the picture still reached the bridge ('+r.sent+' bytes of base64)');
    ok(errs.length===0,  dev.n+': no page errors'+(errs.length?' -> '+errs[0]:''));
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ndownload keeps the grid OK');
  process.exit(bad?1:0);
})();
