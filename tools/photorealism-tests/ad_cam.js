// WHAT THE CARD HAS TO GET OUT OF THE WAY OF.
//
// A LIVE VIEWFINDER. The in-page camera runs INSIDE the comparison screen
// rather than on one of its own, so the "is this a canvas screen" test said
// yes and the card sat over the preview - an ad over someone's viewfinder,
// and the shape that collects accidental taps while they frame a shot.
//
// AND ANY WINDOW THE PAGE OPENS. Settings, the grid designer, the account
// panel: all drawn inside the web view, while the card is a NATIVE view
// sitting on top of it. No z-index the page sets can beat a sibling of the
// web view, so a window that opens under an ad is not a window.
//
// The card is a native view the browser cannot see, so what is checked here
// is the CONTRACT: what the page tells the shell to do.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891},
    deviceScaleFactor:2, isMobile:true, hasTouch:true,
    permissions:['camera'] });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const r = await pg.evaluate(async ()=>{
    // stand in for the shell and record every call the page makes
    const log=[];
    window.RealismCam = {
      saveImage(){}, adPlace(on,bg){ log.push(['place',!!on]); },
      adProj(on){ log.push(['proj',!!on]); }, adSpot(){}, uiScale(){},
    };
    const c=document.createElement('canvas'); c.width=2400;c.height=1800;
    const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,2400,1800);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    show('scrFormat'); await new Promise(r=>setTimeout(r,300));
    $('fmtGo').onclick();
    for (let i=0;i<500;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    show('scrCompare'); adSync(); await new Promise(r=>setTimeout(r,200));
    const last=k=>{ for (let i=log.length-1;i>=0;i--) if (log[i][0]===k) return log[i][1]; return null; };
    const onCompare = { place:last('place'), proj:last('proj') };
    // the viewfinder comes up INSIDE this same screen
    log.length=0;
    CAM.stream = { getTracks:()=>[], getVideoTracks:()=>[{}] };
    adSync(); await new Promise(r=>setTimeout(r,200));
    const onCamera = { place:last('place'), proj:last('proj') };
    const lowering = log.map(x=>x[0]);
    // ...and goes away again
    log.length=0;
    CAM.stream = null;
    adSync(); await new Promise(r=>setTimeout(r,200));
    const after = { place:last('place'), proj:last('proj') };
    const raising = log.map(x=>x[0]);
    // the CROP page - corners mode - lives inside the comparison screen but
    // is not a screen an ad sits on: it is someone dragging four handles to
    // the edges of their picture, and a card in the corner is in the way of
    // the work and exactly where a stray tap lands
    log.length=0;
    const mode0=CMP.mode; CMP.mode='corners';
    adSync(); await new Promise(r=>setTimeout(r,200));
    const onCrop = { place:last('place'), proj:last('proj') };
    log.length=0;
    CMP.mode=mode0;
    adSync(); await new Promise(r=>setTimeout(r,200));
    const offCrop = { place:last('place'), proj:last('proj') };
    // now a WINDOW, opened the way the page opens them - no adSync() call
    // here on purpose: the point is that nobody has to remember to make one
    const wins={};
    for (const id of ['setModal','gsdModal','accModal']){
      log.length=0;
      $(id).style.display='flex';
      await new Promise(r=>setTimeout(r,250));
      const up={ place:last('place'), proj:last('proj') };
      log.length=0;
      $(id).style.display='none';
      await new Promise(r=>setTimeout(r,250));
      wins[id]={ up, down:{ place:last('place'), proj:last('proj') } };
    }
    return { onCompare, onCamera, after, wins, lowering, raising, onCrop, offCrop };
  });
  console.log('comparison screen  place='+r.onCompare.place+' proj='+r.onCompare.proj);
  console.log('viewfinder up      place='+r.onCamera.place+' proj='+r.onCamera.proj);
  console.log('viewfinder gone    place='+r.after.place+' proj='+r.after.proj);
  ok(r.onCompare.place===true && r.onCompare.proj===true,
     'the card is asked for on the comparison screen');
  ok(r.onCamera.place===false && r.onCamera.proj===false,
     'and yielded the moment the viewfinder is live');
  ok(r.after.place===true && r.after.proj===true,
     'and asked for again once the viewfinder is gone');
  console.log('crop page       place='+r.onCrop.place+' proj='+r.onCrop.proj
              +'   back off it place='+r.offCrop.place+' proj='+r.offCrop.proj);
  ok(r.onCrop.place===false && r.onCrop.proj===false,
     'and yielded on the crop page');
  ok(r.offCrop.place===true && r.offCrop.proj===true,
     'and asked for again coming off it');
  // THE ORDER OF THE TWO MESSAGES, which is not cosmetic: the shell shows a
  // bottom strip when ads are WANTED but the card does not own the screen, so
  // a lowering that disowns the screen BEFORE it drops the master flag
  // flashes that strip across the bottom on the way in and out again.
  ok(r.lowering.join(' ')==='place proj',
     'lowering drops the master flag FIRST ('+r.lowering.join(' -> ')+')');
  ok(r.raising.join(' ')==='proj place',
     'raising claims the screen FIRST ('+r.raising.join(' -> ')+')');
  for (const [id,w] of Object.entries(r.wins)){
    console.log(id.padEnd(9)+'  open place='+w.up.place+' proj='+w.up.proj
                +'   closed place='+w.down.place+' proj='+w.down.proj);
    ok(w.up.place===false && w.up.proj===false,
       id+': the card yields when the window opens');
    ok(w.down.place===true && w.down.proj===true,
       id+': and comes back when it closes');
  }
  ok(errs.length===0, 'no page errors'+(errs.length?' -> '+errs[0]:''));
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\nthe card gets out of the way OK');
  process.exit(bad?1:0);
})();
