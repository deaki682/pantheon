// Screenshots of the ad-adjacent placements, v441 beside v442. The strip
// itself is a STAND-IN: the real card is a native Android view the browser
// never sees, so a grey box of the same measured height stands where it sits.
// Everything above that line is the real page.
const { chromium } = require('playwright-core');
const fs = require('fs');
const OUT = process.argv[2] || '.';
const ADH = 76;

async function prep(br, port){
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+port+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  return { ctx, pg };
}
// the stand-in card, drawn to the measured height so the geometry is honest
const strip = (h)=>{
  const d=document.createElement('div');
  d.id='__adFake';
  d.style.cssText='position:fixed;left:0;right:0;bottom:0;height:'+h+'px;z-index:3;'
    +'background:#1b1b1b;border-top:1px solid #3a3a3a;display:flex;align-items:center;'
    +'gap:10px;padding:0 12px;box-sizing:border-box;font:13px system-ui;color:#ddd';
  d.innerHTML='<div style="width:52px;height:52px;border-radius:10px;background:#33302b"></div>'
    +'<div style="flex:1"><div style="font-weight:600">Sponsored headline</div>'
    +'<div style="opacity:.6;font-size:11px">the native card the shell draws here</div></div>'
    +'<div style="background:#c9a227;color:#141414;font-weight:700;border-radius:8px;padding:7px 12px">Install</div>'
    +'<div style="position:absolute;left:12px;top:4px;border:1px solid #c9a227;color:#c9a227;'
    +'font-size:9px;border-radius:3px;padding:0 4px">Ad</div>';
  document.body.appendChild(d);
};

(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const [tag, port] of [['v441', '8895'], ['v442', '8899']]){
    const { ctx, pg } = await prep(br, port);
    // --- the drawing screen, which is what the notice is about ------------
    await pg.evaluate(async ()=>{
      const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
      for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
      if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
      for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    });
    await pg.evaluate(async ([h, mk])=>{
      window.__adOn(true); window.__adH(h);
      eval('('+mk+')')(h);
      await new Promise(r=>setTimeout(r,600));
    }, [ADH, strip.toString()]);
    await pg.waitForTimeout(700);
    await pg.screenshot({ path: OUT+'/ad_draw_'+tag+'.png' });

    // --- the same shot with the measurements drawn on it -----------------
    const m = await pg.evaluate((h)=>{
      const floor=innerHeight-h;
      const mark=(top,bot,col,txt)=>{
        const d=document.createElement('div');
        d.style.cssText='position:fixed;left:0;right:0;top:'+top+'px;height:'+(bot-top)+'px;'
          +'z-index:90;background:'+col+';pointer-events:none;'
          +'font:11px/1.2 system-ui;color:#fff;display:flex;align-items:center;justify-content:center;'
          +'text-shadow:0 1px 2px #000';
        d.textContent=txt; document.body.appendChild(d);
      };
      const hud=document.getElementById('hudWrap').getBoundingClientRect();
      const gap=floor-hud.bottom;
      mark(hud.bottom, floor, 'rgba(40,200,120,0.28)',
        Math.round(gap)+'px = '+(gap*25.4/160).toFixed(1)+'mm clear');
      const g=document.getElementById('adGuard');
      if (g && getComputedStyle(g).display!=='none'){
        const b=g.getBoundingClientRect();
        mark(b.top, b.bottom, 'rgba(255,90,60,0.32)', 'dead band - no pan, no tap');
      }
      return { gap:Math.round(gap) };
    }, ADH);
    await pg.screenshot({ path: OUT+'/ad_draw_marked_'+tag+'.png' });
    console.log(tag+'  drawing screen: nearest control '+m.gap+'px = '+(m.gap*25.4/160).toFixed(1)+'mm from the ad');

    // --- where Remove Ads lives ------------------------------------------
    const p2 = await ctx.newPage();
    await p2.goto('http://localhost:'+port+'/index.html',{waitUntil:'domcontentloaded'});
    await p2.waitForFunction(()=>typeof adPx==='function',null,{timeout:25000});
    await p2.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
    const where = await p2.evaluate(async ([h, mk])=>{
      window.__adOn(true); window.__adH(h);
      const n=document.getElementById('noAdsTxt');
      n.style.display='';                       // the shell offers the purchase
      const g=document.getElementById('gearPanel');
      const inSettings = !!(g && g.contains(n));
      if (inSettings){ document.getElementById('gearModal').style.display='flex'; }
      eval('('+mk+')')(h);
      await new Promise(r=>setTimeout(r,500));
      const b=n.getBoundingClientRect();
      return { inSettings, gap: Math.round((innerHeight-h)-b.bottom) };
    }, [ADH, strip.toString()]);
    await p2.waitForTimeout(400);
    await p2.screenshot({ path: OUT+'/ad_noads_'+tag+'.png' });
    console.log(tag+'  Remove Ads: '+(where.inSettings?'in Settings':'on the home screen edge')
      +', '+where.gap+'px = '+(where.gap*25.4/160).toFixed(1)+'mm from the ad');
    await ctx.close();
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
