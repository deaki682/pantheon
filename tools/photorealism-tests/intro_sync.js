// THE OPENING: the title and the thumbnail rows travel together. The rows
// used to get a head start - they swept in at 560ms, a beat ahead of the
// title's flight at 750 - so the two movements overlapped without ever
// agreeing, and landed 140ms apart. What is measured here is the real thing:
// sample every element's position each frame, and find when each one starts
// moving and when it stops.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  // a RETURNING visitor: first run has its own choreography, where the rows
  // deliberately wait for the welcome message
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  // start sampling BEFORE the page's own scripts run
  await pg.addInitScript(()=>{
    window.__track=[];
    const t0=performance.now();
    // the TRANSFORM, not the bounding box. The title's entry animation eases
    // its letter-spacing, which moves its left edge for 600ms before the
    // flight begins - a box measurement calls that "moving" and the answer
    // comes out meaningless. The flight is the only thing that touches
    // transform, on either element.
    // ...and BOTH axes of it. The rows fly sideways and the title flies
    // almost straight up - it is already centred, so its horizontal travel is
    // three thousandths of a pixel. Watching only x says the title never
    // moved at all.
    const tx=el=>{ if (!el) return null;
      const m=getComputedStyle(el).transform;
      if (!m || m==='none') return 0;
      const p=m.match(/matrix\(([^)]*)\)/);
      if (!p) return 0;
      const v=p[1].split(',').map(parseFloat);
      return Math.round((Math.abs(v[4])+Math.abs(v[5]))*10)/10; };
    const tick=()=>{
      const g=document.getElementById('gallery');
      const w=document.getElementById('introMain');
      // and only while the splash is still up: done() CLEARS the title's
      // transform, which is a change of value but not a movement
      const ww=document.getElementById('introWordWrap');
      if (g||w) window.__track.push({
        t: performance.now()-t0, g: tx(g), w: tx(w),
        on: !!(ww && ww.classList.contains('on')) });
      if (performance.now()-t0 < 3000) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>window.__track && window.__track.length &&
    window.__track[window.__track.length-1].t > 2600, null, {timeout:20000});
  const r = await pg.evaluate(()=>{
    const s=window.__track.filter(x=>x.g!==null && x.w!==null && x.on);
    // a run of samples where the value changes = the element is moving
    const span=key=>{
      let first=null, last=null;
      for (let i=1;i<s.length;i++){
        if (Math.abs(s[i][key]-s[i-1][key]) > 0.4){
          if (first===null) first=s[i-1].t;
          last=s[i].t;
        }
      }
      return { start:first===null?null:Math.round(first), end:last===null?null:Math.round(last) };
    };
    return { rows:span('g'), title:span('w'), n:s.length };
  });
  console.log('rows   move '+r.rows.start+'ms -> '+r.rows.end+'ms');
  console.log('title  move '+r.title.start+'ms -> '+r.title.end+'ms');
  ok(r.rows.start!==null && r.title.start!==null, 'both of them actually move');
  // one frame at 60Hz is ~17ms; allow two, for the sampler's own jitter
  ok(Math.abs(r.rows.start - r.title.start) <= 34,
     'they START together ('+Math.abs(r.rows.start-r.title.start)+'ms apart)');
  ok(Math.abs(r.rows.end - r.title.end) <= 50,
     'and ARRIVE together ('+Math.abs(r.rows.end-r.title.end)+'ms apart)');
  ok(errs.length===0, 'no page errors'+(errs.length?' -> '+errs[0]:''));
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\nthe opening moves as one OK');
  process.exit(bad?1:0);
})();
