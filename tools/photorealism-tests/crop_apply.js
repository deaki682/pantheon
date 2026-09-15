// Dylan: "I tried to apply a crop in the image editor but it didn't work at
// all. it says 'applying' but doesn't do anything."
// Drive the real crop gesture on the real canvas, press Done, and report
// what the edit record held and what `photo` actually became.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:393,height:852}, deviceScaleFactor:3, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror', e=>errs.push(String(e)));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=2000,H=1500; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); g.fillStyle='#fff'; g.fillRect(0,0,W,H);
    g.fillStyle='#000'; g.fillRect(W/2-8,0,16,H);
    const b=await new Promise(r=>c.toBlob(r,'image/png'));
    await addRef(new File([b],'v.png',{type:'image/png'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
  });
  const before = await pg.evaluate(()=>({w:photo.width,h:photo.height}));
  await pg.evaluate(()=>edOpenFor('crop'));
  await pg.waitForFunction(()=>ED && ED.on && ED.fit && ED.mode==='crop',null,{timeout:20000});

  // where the crop rect's left edge is on screen, right now
  const g = await pg.evaluate(()=>{
    const cv=$('edCv'), r=cv.getBoundingClientRect(), dpr=cv.width/r.width;
    const {s,ox,oy}=ED.fit, R=ED.R, pre=ED.pre;
    const rx=ox+R.cx*pre.width*s, ry=oy+R.cy*pre.height*s;
    const rw=R.cw*pre.width*s, rh=R.ch*pre.height*s;
    return { left:r.left+rx/dpr, top:r.top+ry/dpr, w:rw/dpr, h:rh/dpr };
  });
  // drag the left edge a quarter of the way in
  const y = g.top + g.h/2;
  await pg.mouse.move(g.left+1, y);
  await pg.mouse.down();
  for (let i=1;i<=8;i++) await pg.mouse.move(g.left+1 + (g.w*0.25)*i/8, y);
  await pg.mouse.up();
  const R = await pg.evaluate(()=>({...ED.R}));
  await pg.evaluate(()=>$('edDone').click());
  await pg.waitForTimeout(2500);
  const after = await pg.evaluate(()=>({w:photo.width,h:photo.height,
    screen:(document.querySelector('.screen.on')||{}).id,
    stored:localStorage.getItem('edit|'+galActive)}));
  console.log('crop rect after the drag: cx',R.cx.toFixed(3),'cw',R.cw.toFixed(3));
  console.log('photo before', before.w+'x'+before.h);
  console.log('photo after ', after.w+'x'+after.h, 'on', after.screen);
  console.log('expected after ~', Math.round(before.w*R.cw)+'x'+before.h);
  console.log('stored edit:', after.stored ? 'yes' : 'NONE');
  console.log(after.w < before.w*0.95 ? 'PASS crop applied' : 'FAIL crop did NOT apply');
  if (errs.length) console.log('page errors:', errs.slice(0,3));
  await br.close();
})();
