// The drawing screen wears the strip at the TOP now, its top row carries
// nothing tappable, and the bottom controls are back where they were.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
const MM=25.4/160;
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  let bad=0; const ok=(c,m)=>{ if(!c) bad++; console.log('  '+(c?'ok   ':'FAIL ')+m); };
  for (const h of [76,104,132]){
    const r = await pg.evaluate(async (h)=>{
      // what the shell does for the portrait drawing screen
      document.documentElement.classList.add('adTop');
      window.__adOn(true); window.__adH(h);
      await new Promise(r=>setTimeout(r,450));
      const out={ h };
      // nothing tappable in the top band
      const band=h+8;
      const sel='button,a,select,input,[onclick],[role=button]';
      out.topHits=[];
      for (const el of document.querySelectorAll(sel)){
        const st=getComputedStyle(el);
        if (st.display==='none'||st.visibility==='hidden'||st.pointerEvents==='none') continue;
        const sc=el.closest('.screen'); if (sc && !sc.classList.contains('on')) continue;
        const md=el.closest('[id$="Modal"]'); if (md && getComputedStyle(md).display==='none') continue;
        const b=el.getBoundingClientRect();
        if (!b.width||!b.height) continue;
        if (b.top < band) out.topHits.push((el.id||el.tagName)+'@'+Math.round(b.top));
      }
      // the paper starts below the strip
      const vp=document.getElementById('viewport').getBoundingClientRect();
      out.paperTop=Math.round(vp.top);
      // and the controls are back down
      const hud=document.getElementById('hudWrap').getBoundingClientRect();
      out.hudGap=Math.round(innerHeight-hud.bottom);
      // the dead band followed the ad up
      const g=document.getElementById('adGuard');
      const gs=g?getComputedStyle(g):null, gr=g?g.getBoundingClientRect():null;
      out.guard = g && gs.display!=='none' ? {top:Math.round(gr.top),h:Math.round(gr.height)} : null;
      out.back = getComputedStyle(document.getElementById('backBtn')).display;
      out.exp  = getComputedStyle(document.getElementById('expCorner')).display;
      return out;
    }, h);
    ok(r.topHits.length===0, 'strip '+h+': nothing tappable in the top band'
      +(r.topHits.length?' ('+r.topHits.join(', ')+')':''));
    ok(r.paperTop>=h, 'strip '+h+': the paper starts at '+r.paperTop+', below the strip');
    ok(r.hudGap<=12, 'strip '+h+': controls back down, '+r.hudGap+'px off the bottom');
    ok(!!r.guard && r.guard.top>=h-1, 'strip '+h+': dead band sits under the ad at '+(r.guard?r.guard.top:'-'));
    if (h===76){
      ok(r.back==='none', 'the back button is gone from the drawing screen');
      ok(r.exp==='none', 'the download button is gone from the drawing screen');
    }
  }
  // the top row is bare with NO ad too - a viewer who bought the removal
  // must not keep the buttons that were taken away
  const noAd = await pg.evaluate(async ()=>{
    document.documentElement.classList.remove('adTop');
    window.__adOn(false); window.__adH(0);
    await new Promise(r=>setTimeout(r,450));
    const vis=id=>{ const el=document.getElementById(id);
      const cs=getComputedStyle(el);
      return cs.display!=='none' && cs.visibility!=='hidden' && cs.pointerEvents!=='none'; };
    return { gear: vis('setCorner'), dl: vis('expCorner'), back: vis('backBtn'),
             hudGap: Math.round(innerHeight-document.getElementById('hudWrap').getBoundingClientRect().bottom) };
  });
  ok(!noAd.gear && !noAd.dl && !noAd.back,
     'with ads removed the top row is still bare (gear '+noAd.gear+', download '+noAd.dl+', back '+noAd.back+')');
  ok(noAd.hudGap<=12, 'and the controls stay at '+noAd.hudGap+'px off the bottom');
  await pg.evaluate(async ()=>{ document.documentElement.classList.add('adTop');
    window.__adOn(true); window.__adH(76); await new Promise(r=>setTimeout(r,400)); });

  // and the badge survives, with nothing to press
  const badge = await pg.evaluate(async ()=>{
    DONE=[1,2,3]; markBadge(true);
    await new Promise(r=>setTimeout(r,350));
    const b=document.getElementById('setBtn').getBoundingClientRect();
    const cs=getComputedStyle(document.getElementById('setCorner'));
    return { txt:document.getElementById('markTxt').textContent,
             pointer:cs.pointerEvents, top:Math.round(b.top), w:Math.round(b.width) };
  });
  ok(/\d+\/\d+/.test(badge.txt), 'the completed-squares tally survives: "'+badge.txt+'"');
  ok(badge.pointer==='none', 'and it is a label, not a button');
  ok(badge.top>=76, 'sitting under the card at '+badge.top);
  // every OTHER screen keeps the strip at the bottom
  const other = await pg.evaluate(async ()=>{
    show('scrCompare'); await new Promise(r=>setTimeout(r,500));
    document.documentElement.classList.remove('adTop');
    window.__adOn(true); window.__adH(76);
    await new Promise(r=>setTimeout(r,400));
    const f=document.getElementById('cmpFlip').getBoundingClientRect();
    return { gap: Math.round((innerHeight-76)-f.bottom) };
  });
  ok(other.gap*MM>=6, 'the compare screen keeps its bottom strip and its clearance ('
    +other.gap+'px = '+(other.gap*MM).toFixed(1)+'mm)');
  if (errs.length) console.log('  page errors: '+errs.slice(0,3).join(' | '));
  console.log(bad? '\n'+bad+' problem(s)' : '\nthe drawing screen is clear at the top');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
