// The cached overlay must look like the old per-stroke drawing, and the
// proxy must not soften the photograph. Shoot the crop preview in every
// grid configuration, on both versions, and diff.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const TAG  = process.argv[3]||'now';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    // a photo with real high-frequency detail, so softening would show
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(0.5,'#8a7f6e'); gr.addColorStop(1,'#111');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
    for (let y=0;y<H;y+=6){ g.fillStyle=(y/6)%2?'rgba(0,0,0,.35)':'rgba(255,255,255,.35)';
      g.fillRect(0,y,W,3); }
    // SEEDED: Math.random() gave each run a different photograph, so the
    // diff measured the speckle, not the change under test
    let sd=12345; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<30000;i++){ g.fillStyle='rgba(255,80,40,.5)'; g.fillRect(rnd()*W,rnd()*H,3,3); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30';
  });
  const cases = [
    ['sq',   false, false, 'auto', 1],
    ['diag', false, false, 'auto', 1],
    ['dots', false, false, 'auto', 1],
    ['sq',   true,  false, 'auto', 1],
    ['diag', true,  true,  'auto', 1],
    ['dots', true,  false, 'auto', 1],
    ['diag', false, true,  '#ff3b30', 1],
    ['sq',   false, true,  '#ff3b30', 2.2],
    ['diag', false, false, 'auto', 4],
  ];
  const fs=require('fs');
  for (let i=0;i<cases.length;i++){
    const [style,sub,lab,col,zoom]=cases[i];
    await pg.evaluate(([style,sub,lab,col,zoom])=>{
      GRID_STYLE=style; GRID_SUB=sub; GRID_LAB=lab; GRID_COL=col; GRID_ON=true;
      GRID_OP=0.75; GRID_THK=1; CELLSZ.u='cm'; CELLSZ.v=2;
      FMT_ZOOM=zoom; FMT_OFF.x=0.5; FMT_OFF.y=0.5;
      fmtPreview();
    },[style,sub,lab,col,zoom]);
    await pg.waitForTimeout(250);
    const buf = await pg.locator('#fmtCanvas').screenshot();
    fs.writeFileSync('look_'+TAG+'_'+i+'_'+style+(sub?'_sub':'')+(lab?'_lab':'')+'_z'+zoom+'.png', buf);
  }
  console.log(TAG+': '+cases.length+' shots');
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
