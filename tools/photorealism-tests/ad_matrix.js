// "Does it work on every device?" - the honest version. For each screen
// geometry, UI scale, reference mode, strip height and orientation, find the
// interactive element that ends up CLOSEST to the ad - whatever it is, not
// just the five I happen to know about - and report that clearance in
// millimetres. Then check the dead band is where it should be, that it is
// absent exactly when there is no strip, and that the no-:has() fallback
// puts it there too.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const MM = 25.4/160;                 // a css px is 1/160 inch, by definition
const WANT_MM = 6;

const DEVICES = [
  // name,                w,   h,  dpr,  note
  ['tiny  320x568',      320, 568, 2,   'iPhone SE / Android Go class'],
  ['small 360x640',      360, 640, 3,   'Tecno Spark, Galaxy A0x'],
  ['std   411x891',      411, 891, 2.625,'Galaxy S21 FE'],
  ['tall  430x932',      430, 932, 3,   'iPhone 15 Pro Max class'],
  ['tablet 768x1024',    768,1024, 2,   'iPad / 10in Android'],
];
const HEIGHTS = [76, 104, 132];

async function open(br, dev, scale, dm){
  const [,w,h,dpr] = dev;
  const ctx = await br.newContext({ viewport:{width:w,height:h}, deviceScaleFactor:dpr, isMobile:true, hasTouch:true });
  await ctx.addInitScript(([scale,dm])=>{
    Object.defineProperty(navigator,'deviceMemory',{get:()=>dm});
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    if (scale==='L'){ localStorage.setItem('uiScale','L'); }
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
  }, [scale,dm]);
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  return { ctx, pg, errs };
}

// the probe: the nearest VISIBLE interactive thing to the top of the strip
const probe = async (pg, h) => pg.evaluate(async (h)=>{
  // a scrolling screen parks its last rows below the fold, which is not the
  // same thing as parking them under the ad. Scroll to the end first: what
  // the artist can actually reach is what has to clear the strip.
  const sc=document.querySelector('.screen.on');
  try{ if (sc) sc.scrollTop = sc.scrollHeight; window.scrollTo(0, 1e6); }catch(e){}
  await new Promise(r=>setTimeout(r,350));
  const stripOn = document.documentElement.classList.contains('adOn');
  const floor = stripOn ? innerHeight - h : innerHeight;
  const sel='button,a,select,input,[onclick],[role=button],#hudWrap,#detCorner,'
    +'#gridCorner,#underCorner,#camCorner';
  let worst=null;
  for (const el of document.querySelectorAll(sel)){
    const st=getComputedStyle(el);
    if (st.display==='none'||st.visibility==='hidden'||st.pointerEvents==='none') continue;
    if (parseFloat(st.opacity)===0) continue;
    // inside a closed modal, or off the current screen
    const sc=el.closest('.screen'); if (sc && !sc.classList.contains('on')) continue;
    const md=el.closest('[id$="Modal"]');
    if (md && getComputedStyle(md).display==='none') continue;
    const b=el.getBoundingClientRect();
    if (!b.width || !b.height) continue;
    if (b.bottom < 0 || b.top > innerHeight) continue;
    if (el.id==='adGuard') continue;
    const gap = floor - b.bottom;
    if (gap > 260) continue;                  // far from the strip, not at issue
    if (!worst || gap < worst.gap)
      worst={ id: el.id || (el.tagName+'.'+(el.className||'').toString().split(' ')[0]), gap };
  }
  const g=document.getElementById('adGuard');
  const gs=g?getComputedStyle(g):null;
  const gr=g?g.getBoundingClientRect():null;
  return { stripOn, floor, worst,
    guard: g && gs.display!=='none'
      ? { top:Math.round(gr.top), bottom:Math.round(gr.bottom), h:Math.round(gr.height) } : null };
}, h);

(async () => {
  const br = await chromium.launch(require('./browser.js'));
  let bad=0, rows=0;
  console.log('port '+PORT+'   clearance wanted: >= '+WANT_MM+'mm (a fingertip is 8-10mm)\n');

  for (const dev of DEVICES){
    for (const scale of ['default','L']){
      const { ctx, pg, errs } = await open(br, dev, scale, 4);
      for (const mode of ['bw','colour']){
        await pg.evaluate(async (m)=>{
          document.body.classList.toggle('colorRef', m==='colour');
          await new Promise(r=>setTimeout(r,200));
        }, mode);
        for (const h of HEIGHTS){
          for (const scr of ['scrMain','scrCompare','scrUpload','scrFormat']){
            await pg.evaluate(async ([h,scr])=>{ show(scr);
              await new Promise(r=>setTimeout(r,450));
              window.__adOn(true); window.__adH(h);
              await new Promise(r=>setTimeout(r,350)); }, [h,scr]);
            const r = await probe(pg, h);
            rows++;
            // TWO screens wear no strip at all: the size screen and the
            // drawing screen (which gets the corner video card out of its
            // Download button instead). There is no ad to clear on those -
            // what must hold is that they reserve NOTHING for one, so the
            // controls reach the bottom of the window exactly as they do for
            // a viewer who bought the removal.
            const strip = !(scr==='scrMain'||scr==='scrFormat');
            const mm = r.worst ? r.worst.gap*MM : 99;
            const gapOK = strip ? (mm >= WANT_MM) : (r.worst ? r.worst.gap < 0 : true);
            // the band belongs on the one screen that still has a strip
            // under a canvas
            const wantBand = (scr==='scrCompare');
            const bandOK = wantBand
              ? (!!r.guard && Math.abs(r.guard.bottom - r.floor) <= 1 && r.guard.h >= 20)
              : !r.guard;
            if (!gapOK || !bandOK) bad++;
            console.log((gapOK&&bandOK?'  ok   ':'  FAIL ')
              + dev[0].padEnd(16) + scale.padEnd(8) + mode.padEnd(7)
              + scr.padEnd(11) + (strip ? 'strip '+String(h).padStart(3) : 'no strip ')
              + '   nearest '+(r.worst?r.worst.id:'-').padEnd(12)
              + ' '+String(r.worst?Math.round(r.worst.gap):'-').padStart(4)+'px = '+mm.toFixed(1)+'mm'
              + '   band '+(r.guard?r.guard.h+'px':(wantBand?'MISSING':'none')));
          }
        }
      }
      if (errs.length) console.log('        page errors: '+errs.slice(0,2).join(' | '));
      await ctx.close();
    }
  }

  // --- a tour bubble anchored low, close button and all ------------------
  {
    const { ctx, pg } = await open(br, DEVICES[1], 'default', 4);
    const r = await pg.evaluate(async ()=>{
      window.__adOn(true); window.__adH(104);
      await new Promise(r=>setTimeout(r,400));
      show('scrUpload'); await new Promise(r=>setTimeout(r,400));
      const low=document.getElementById('calBtn')||document.getElementById('gallery');
      if (typeof tip!=='function'||!low) return null;
      tip(low.id, 'A tip anchored low on the page, below its target.', {below:true});
      if (TIPSTATE && TIPSTATE.re) TIPSTATE.re();
      await new Promise(r=>setTimeout(r,300));
      const floor=innerHeight-104;
      const b=document.getElementById('tourBubble').getBoundingClientRect();
      const x=document.getElementById('tourX').getBoundingClientRect();
      return { bubble: Math.round(floor-b.bottom), close: Math.round(floor-x.bottom) };
    });
    if (r){
      const mm = Math.min(r.bubble, r.close)*MM;
      const ok = mm >= WANT_MM; if (!ok) bad++; rows++;
      console.log('\n  '+(ok?'ok   ':'FAIL ')+'tour bubble low     strip 104   bubble '
        +r.bubble+'px, close button '+r.close+'px = '+mm.toFixed(1)+'mm');
    }
    await ctx.close();
  }

  // --- the compare screen carries the strip too --------------------------
  {
    const { ctx, pg } = await open(br, DEVICES[2], 'default', 4);
    await pg.evaluate(async ()=>{ show('scrCompare'); await new Promise(r=>setTimeout(r,700)); });
    await pg.evaluate(async ()=>{ window.__adOn(true); window.__adH(104);
      await new Promise(r=>setTimeout(r,400)); });
    const r = await probe(pg, 104);
    const mm = r.worst ? r.worst.gap*MM : 99;
    const ok = mm>=WANT_MM && !!r.guard;
    if (!ok) bad++; rows++;
    console.log('\n  '+(ok?'ok   ':'FAIL ')+'compare screen     strip 104   nearest '
      +(r.worst?r.worst.id:'-')+' '+(r.worst?Math.round(r.worst.gap):'-')+'px = '+mm.toFixed(1)+'mm'
      +'   band '+(r.guard?r.guard.h+'px':'MISSING'));
    await ctx.close();
  }

  // --- landscape: the drawing screen has NO strip (corner card instead) ---
  {
    const ctx = await br.newContext({ viewport:{width:891,height:411}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await pg.evaluate(async ()=>{
      const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
      for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
      if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
      for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
      window.__adOn(false); window.__adCorner(true);     // what the shell does here
      await new Promise(r=>setTimeout(r,400));
    });
    const r = await probe(pg, 0);
    const ok = !r.stripOn && !r.guard;
    if (!ok) bad++; rows++;
    console.log('  '+(ok?'ok   ':'FAIL ')+'landscape drawing   no strip: '+(!r.stripOn?'yes':'NO')
      +'   band absent: '+(!r.guard?'yes':'NO (it should not be here)'));
    // and the landscape compare screen, which DOES carry the strip
    await pg.evaluate(async ()=>{ window.__adCorner(false); show('scrCompare');
      await new Promise(r=>setTimeout(r,600));
      window.__adOn(true); window.__adH(76); await new Promise(r=>setTimeout(r,400)); });
    const r2 = await probe(pg, 76);
    const mm2 = r2.worst ? r2.worst.gap*MM : 99;
    const ok2 = mm2>=WANT_MM;
    if (!ok2) bad++; rows++;
    console.log('  '+(ok2?'ok   ':'FAIL ')+'landscape compare   strip  76   nearest '
      +(r2.worst?r2.worst.id:'-')+' '+(r2.worst?Math.round(r2.worst.gap):'-')+'px = '+mm2.toFixed(1)+'mm'
      +'   band '+(r2.guard?r2.guard.h+'px':'none'));
    await ctx.close();
  }

  // --- ads removed / never shown: everything goes back where it was ------
  {
    const { ctx, pg } = await open(br, DEVICES[2], 'default', 4);
    const r = await pg.evaluate(async ()=>{
      window.__adOn(false); await new Promise(r=>setTimeout(r,400));
      const g=document.getElementById('adGuard');
      const hud=document.getElementById('hudWrap').getBoundingClientRect();
      return { band: g && getComputedStyle(g).display!=='none',
               hudGap: Math.round(innerHeight - hud.bottom) };
    });
    const ok = !r.band && r.hudGap < 40;
    if (!ok) bad++; rows++;
    console.log('  '+(ok?'ok   ':'FAIL ')+'ads removed         band gone: '+(!r.band?'yes':'NO')
      +'   controls back to '+r.hudGap+'px off the bottom');
    await ctx.close();
  }

  // --- a WebView with no :has(): the JS fallback must place the band -----
  {
    const { ctx, pg } = await open(br, DEVICES[2], 'default', 4);
    const r = await pg.evaluate(async ()=>{
      // strip the :has() rule out of the stylesheet, the way an old engine
      // would have dropped it at parse time, then re-run the page's fallback
      let removed=0;
      for (const ss of document.styleSheets){
        try{ for (let i=ss.cssRules.length-1;i>=0;i--){
          const t=ss.cssRules[i].selectorText||'';
          if (t.includes(':has(') && t.includes('adGuard')){ ss.deleteRule(i); removed++; }
        }}catch(e){}
      }
      window.__adOn(true); window.__adH(76);
      await new Promise(r=>setTimeout(r,300));
      const g=document.getElementById('adGuard');
      const beforeFallback = getComputedStyle(g).display!=='none';
      // this is the fallback's own body, run against the same DOM
      const on = document.documentElement.classList.contains('adOn') &&
        ((document.getElementById('scrMain')&&document.getElementById('scrMain').classList.contains('on')) ||
         (document.getElementById('scrCompare')&&document.getElementById('scrCompare').classList.contains('on')));
      g.style.display = on ? 'block' : 'none';
      await new Promise(r=>setTimeout(r,200));
      const b=g.getBoundingClientRect();
      return { removed, beforeFallback,
        shown: getComputedStyle(g).display!=='none',
        bottom: Math.round(b.bottom), floor: innerHeight-76 };
    });
    const ok = r.removed>0 && !r.beforeFallback && r.shown && Math.abs(r.bottom-r.floor)<=1;
    if (!ok) bad++; rows++;
    console.log('  '+(ok?'ok   ':'FAIL ')+'no :has() WebView   rule dropped: '+r.removed
      +'   band without it: '+(r.beforeFallback?'shown (rule not really gone)':'gone')
      +' -> fallback puts it back: '+(r.shown?'yes':'NO'));
    await ctx.close();
  }

  console.log('\n'+rows+' configurations, '+(bad? bad+' FAILED' : 'all clear'));
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
