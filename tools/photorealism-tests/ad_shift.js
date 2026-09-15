// The layout must not move when a creative arrives or fails to. The shell
// says __adOn(slot) the moment ads are enabled, then __adH(px) once it has
// measured a strip - and it measures 0 while the slot is empty. Replay that
// exact sequence and watch whether anything jumps.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const WATCH = ['hudWrap','detCorner','gridCorner','camCorner'];
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
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
  const snap = async (label, fn) => {
    const r = await pg.evaluate(async ([label,fn,WATCH])=>{
      eval(fn); await new Promise(r=>setTimeout(r,450));
      const o={label, adh:getComputedStyle(document.documentElement).getPropertyValue('--adh').trim()||'(unset)'};
      for (const id of WATCH){ const el=document.getElementById(id);
        if (!el) continue; const st=getComputedStyle(el);
        o[id] = (st.display==='none') ? null : Math.round(el.getBoundingClientRect().bottom); }
      const sc=document.getElementById('scrUpload');
      o.homePad = Math.round(parseFloat(getComputedStyle(sc).paddingBottom)||0);
      return o;
    }, [label, fn, WATCH]);
    return r;
  };
  // the real order of events on a cold start with ads enabled
  const steps = [
    ['ads enabled, slot still empty', "window.__adOn(true); if(window.__adH) window.__adH(0);"],
    ['first creative fills (76px)',   "window.__adH(76);"],
    ['a refresh comes back empty',    "window.__adH(0);"],
    ['and fills again',               "window.__adH(76);"],
  ];
  const rows=[];
  for (const [l,f] of steps) rows.push(await snap(l,f));
  let worst=0;
  for (const r of rows){
    console.log('  '+r.label.padEnd(32)+'--adh '+String(r.adh).padStart(6)
      +'   hud bottom '+String(r.hudWrap).padStart(4)
      +'   home padding '+String(r.homePad).padStart(4));
  }
  for (const id of WATCH){
    const vals=rows.map(r=>r[id]).filter(v=>v!=null);
    if (!vals.length) continue;
    const d=Math.max(...vals)-Math.min(...vals);
    worst=Math.max(worst,d);
    if (d) console.log('    '+id+' moved '+d+'px across the four states');
  }
  const padD = Math.max(...rows.map(r=>r.homePad)) - Math.min(...rows.map(r=>r.homePad));
  worst=Math.max(worst,padD);
  if (padD) console.log('    home screen padding moved '+padD+'px');
  // a phone on a large system font: the strip is taller, and the reserve
  // must follow it rather than snapping back to the 76px guess
  const big = [
    await snap('large font, strip 132',  "window.__adH(132);"),
    await snap('  then an empty refresh', "window.__adH(0);"),
  ];
  for (const r of big)
    console.log('  '+r.label.padEnd(32)+'--adh '+String(r.adh).padStart(6)
      +'   hud bottom '+String(r.hudWrap).padStart(4));
  const bigD = Math.abs(big[0].hudWrap - big[1].hudWrap);
  if (bigD) { worst=Math.max(worst,bigD); console.log('    FAIL: moved '+bigD+'px'); }

  // and a viewer who BOUGHT the removal gets the space back - the whole
  // reservation goes with adOn, not with the measurement
  const off = await snap('ads removed', "window.__adOn(false); window.__adH(0);");
  console.log('  '+off.label.padEnd(32)+'--adh '+String(off.adh).padStart(6)
    +'   hud bottom '+String(off.hudWrap).padStart(4)
    +'   home padding '+String(off.homePad).padStart(4));
  const gave = off.hudWrap > rows[1].hudWrap + 40 && off.homePad < 20;
  if (!gave){ worst=Math.max(worst,1); console.log('    FAIL: the space was not given back'); }
  else console.log('    the strip\'s room is returned  ok');

  console.log(worst===0 ? '\nnothing moves - ok' : '\nWORST SHIFT: '+worst+'px  FAIL');
  await br.close();
  process.exit(worst?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
