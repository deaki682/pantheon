// AdMob: "your layout encourages accidental clicks". Three things make that
// true, and this measures all three.
//   1. clearance - how far a real fingertip is from the ad when it presses
//      the nearest control. A css px is 1/160 inch by definition, so the
//      gap converts straight to millimetres; a fingertip is 8-10mm.
//   2. the dead band - the slice of page directly above the strip must
//      answer to nothing, so a downward drag cannot still be travelling
//      when the finger crosses onto the ad.
//   3. remove-ads - a tap target whose whole purpose is dismissing the ad
//      must not be parked beside it.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const MM = 25.4/160;                       // css px -> mm, by definition
const WANT_MM = 6;                         // below a fingertip is the problem
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  let bad=0;

  // --- 3. where does remove-ads live, before we ever open a project -------
  const na = await pg.evaluate(()=>{
    const el=document.getElementById('noAdsTxt');
    if (!el) return {missing:true};
    const g=document.getElementById('gearPanel');
    return { inSettings: !!(g && g.contains(el)),
             pinned: getComputedStyle(el).position };
  });
  const naOK = !na.missing && na.inSettings && na.pinned!=='absolute' && na.pinned!=='fixed';
  if (!naOK) bad++;
  console.log('remove-ads: '+(na.missing?'MISSING'
    : (na.inSettings?'in Settings':'still on a screen edge')+', position '+na.pinned)
    +'  '+(naOK?'ok':'FAIL'));

  // --- open a project so the drawing screen is the one under the ad ------
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });

  for (const h of [76,104,132]){
    const r = await pg.evaluate(async (h)=>{
      window.__adOn(true); if (window.__adH) window.__adH(h);
      await new Promise(r=>setTimeout(r,450));
      const floor=innerHeight-h, out=[];
      // every control the drawing screen floats over the paper
      for (const id of ['hudWrap','detCorner','gridCorner','underCorner','camCorner']){
        const el=document.getElementById(id); if (!el) continue;
        const st=getComputedStyle(el);
        if (st.display==='none'||st.visibility==='hidden') continue;
        const b=el.getBoundingClientRect();
        if (!b.height) continue;
        out.push({ id, gap: floor-b.bottom });
      }
      const g=document.getElementById('adGuard');
      const gb=g?getComputedStyle(g):null;
      const gr=g?g.getBoundingClientRect():null;
      return { floor, out,
        guard: g ? { shown: gb.display!=='none',
                     top: Math.round(gr.top), bottom: Math.round(gr.bottom) } : null };
    }, h);
    const worst = r.out.reduce((a,o)=>o.gap<a.gap?o:a, {id:'-',gap:1e9});
    const okGap = worst.gap*MM >= WANT_MM;
    if (!okGap) bad++;
    console.log('strip '+String(h).padStart(3)+'px  nearest control: '+worst.id
      +' '+Math.round(worst.gap)+'px = '+(worst.gap*MM).toFixed(1)+'mm clear  '
      +(okGap?'ok':'FAIL (a fingertip is 8-10mm)'));
    // the dead band has to sit between that control and the strip
    const gOK = r.guard && r.guard.shown
      && Math.abs(r.guard.bottom - r.floor) <= 1
      && r.guard.top >= r.floor - h;
    if (!gOK) bad++;
    console.log('           dead band: '
      +(r.guard ? (r.guard.shown ? r.guard.top+'-'+r.guard.bottom+' (ad top '+r.floor+')' : 'hidden')
                : 'absent')+'  '+(gOK?'ok':'FAIL'));
  }

  // --- 2b. does the band actually swallow a pointer? ---------------------
  const sw = await pg.evaluate(async ()=>{
    window.__adOn(true); window.__adH(76);
    await new Promise(r=>setTimeout(r,300));
    const g=document.getElementById('adGuard');
    if (!g) return {absent:true};
    const b=g.getBoundingClientRect();
    let reached=0;
    const spy=()=>{ reached++; };
    document.addEventListener('pointerdown', spy, true);
    // capture-phase on document still sees it; what matters is that the
    // guard stops it before the canvas's own listener, so watch the canvas
    let onCanvas=0;
    const cv=document.getElementById('viewCv')||document.querySelector('#scrMain canvas');
    if (cv) cv.addEventListener('pointerdown', ()=>{onCanvas++;}, false);
    const hit=document.elementFromPoint(Math.round(b.left+b.width/2), Math.round(b.top+b.height/2));
    document.removeEventListener('pointerdown', spy, true);
    return { hitId: hit?(hit.id||hit.tagName):'none', onCanvas };
  });
  const swOK = !sw.absent && sw.hitId==='adGuard';
  if (!swOK) bad++;
  console.log('band takes the hit: elementFromPoint -> '+(sw.absent?'no band':sw.hitId)+'  '+(swOK?'ok':'FAIL'));

  if (errs.length) console.log('page errors:', errs.slice(0,3));
  console.log(bad===0 ? 'ALL CLEAR' : bad+' finding(s)');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
