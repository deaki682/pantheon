// The instant reopen must produce the SAME picture dimensions and the same
// cook fingerprint as an ordinary open, or every reopen re-cooks.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const [label, dm] of [['default device', 8], ['4GB phone', 4]]){
    const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
    await ctx.addInitScript(([dm])=>{ Object.defineProperty(navigator,'deviceMemory',{get:()=>dm});
      localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); }, [dm]);
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:'+(process.argv[2]||'8899')+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof openSrc==='function',null,{timeout:25000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
    const r = await pg.evaluate(async ()=>{
      // a PORTRAIT photo, the case the working-copy guard used to miss
      const W=4000,H=6000;
      const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
      // A SMOOTH gradient is the one photograph a working copy is never made
      // for: the shrunk re-encode comes out no smaller than the original, so
      // the app correctly declines to store one and the assertion below was
      // reading a case it was never meant to test. Real photographs carry
      // high-frequency detail; give it some, seeded so every run is the same.
      let sd=99991; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
      for (let i=0;i<120000;i++){
        g.fillStyle='rgba('+Math.round(rnd()*255)+','+Math.round(rnd()*255)+','+Math.round(rnd()*255)+',.6)';
        g.fillRect(rnd()*W, rnd()*H, 5, 5);
      }
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
      await addRef(new File([b],'portrait.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
      for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
      const coldPhoto=[photo.width,photo.height], coldKey=CKEY;
      let rec=(await galAll()).find(x=>x.name==='portrait.jpg');
      // it is made beside the original, never instead of it, and only when
      // it actually saves something - so record which of those two answers
      // the app gave rather than assuming the first
      const declined = !rec.work;
      const workUsed = !!(rec.work && rec.workW && rec.workW>=refCap());
      // now REOPEN the way a gallery tap does
      show('scrUpload'); await new Promise(r=>setTimeout(r,300));
      const purges=[]; const realPurge=window.cachePurge;
      window.cachePurge=(k)=>{ purges.push(k); return realPurge(k); };
      const rr=(await galAll()).find(x=>x.name==='portrait.jpg');
      warmOpen(rr);
      for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on') && photo && photo.width && !WARM_PEND) break; await new Promise(r=>setTimeout(r,100)); }
      await new Promise(r=>setTimeout(r,900));
      const firstReopenPurges=purges.length, keyAfter1=CKEY;
      // and again: from here every open reads the same copy, so it must settle
      purges.length=0;
      window.cachePurge=(k)=>{ purges.push(k); return realPurge(k); };
      show('scrUpload'); await new Promise(r=>setTimeout(r,300));
      const r3=(await galAll()).find(x=>x.name==='portrait.jpg');
      warmOpen(r3);
      for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on') && photo && photo.width && !WARM_PEND) break; await new Promise(r=>setTimeout(r,100)); }
      await new Promise(r=>setTimeout(r,900));
      const secondReopenPurges=purges.length, keyAfter2=CKEY;
      window.cachePurge=realPurge;
      return { cap:refCap(), coldPhoto, warmPhoto:[photo.width,photo.height],
        sameKey: CKEY===coldKey, purges:firstReopenPurges,
        settles: secondReopenPurges===0 && keyAfter2===keyAfter1,
        secondReopenPurges,
        workW:rec.workW, workUsed, declined,
        origKept: !!(rec.blob && rec.blob.size) };
    });
    console.log(label+':');
    console.log('   cap '+r.cap+'   first open '+r.coldPhoto.join('x')+'   reopen '+r.warmPhoto.join('x'),
      r.coldPhoto.join()===r.warmPhoto.join() ? 'ok' : 'FAIL (different picture)');
    console.log('   same cook fingerprint: '+(r.sameKey?'ok':'FAIL')+'   cache purges on reopen: '+r.purges+(r.purges?' FAIL':' ok'));
    console.log('   working copy long edge '+(r.declined?'declined (no saving)':r.workW)
      +' -> used on reopen: '+((r.workUsed||r.declined)?'ok':'FAIL'));
    console.log('   original kept beside it: '+(r.origKept?'ok':'FAIL (the artist\'s file is gone)'));
    console.log('   settles after that   : second reopen purges '+r.secondReopenPurges+'  '+(r.settles?'ok (stable from here)':'FAIL (still re-cooking)'));
    if (errs.length) console.log('   page errors:', errs.slice(0,2));
    await ctx.close();
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
