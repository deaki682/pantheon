// Alternatives to pushing the drawing screen's controls 48px up off the ad.
// Each is applied as CSS over the shipped page and photographed the same way.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', OUT=process.argv[3]||'.';
const ADH=76;
const strip=(h)=>{
  const d=document.createElement('div'); d.id='__adFake';
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
const OPTS = [
  ['0-shipped-48px', '', true],
  ['1-old-8px',      'html.adOn{--adgap:8px}', true],
  ['2-toolbar',
    'html.adOn{--adgap:0px}'
   +'#__bar{position:fixed;left:0;right:0;z-index:4;background:#191919;'
   +'border-top:1px solid #3a3a3a;box-shadow:0 -6px 14px rgba(0,0,0,.45);height:72px;'
   +'bottom:calc(var(--adh,76px) + env(safe-area-inset-bottom))}'
   +'html.adOn #hudWrap,html.adOn #detCorner,html.adOn #gridCorner,'
   +'html.adOn #underCorner,html.adOn #camCorner{'
   +'bottom:calc(var(--adh,76px) + 14px + env(safe-area-inset-bottom));z-index:5}', true],
  ['3-side-rail',
    'html.adOn #hudWrap{left:auto;right:10px;transform:none;bottom:auto;top:44%}'
   +'html.adOn #detCorner{left:auto;right:10px;transform:none;bottom:auto;top:56%}'
   +'html.adOn #gridCorner{left:auto;right:10px;transform:none;bottom:auto;top:68%}'
   +'html.adOn #camCorner{left:auto;right:10px;transform:none;bottom:auto;top:80%}'
   +'html.adOn #underCorner{left:auto;right:10px;transform:none;bottom:auto;top:32%}', true],
  ['4-no-strip-here', '', false],
];
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const [name, css, adOn] of OPTS){
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
    await pg.evaluate(async ([css, adOn, h, mk, name])=>{
      if (css){ const st=document.createElement('style'); st.textContent=css; document.head.appendChild(st); }
      if (name.startsWith('2')){ const b=document.createElement('div'); b.id='__bar'; document.body.appendChild(b); }
      window.__adOn(!!adOn); if (adOn) window.__adH(h);
      if (adOn) eval('('+mk+')')(h);
      else {
        // the corner card the landscape drawing screen already uses instead
        const c=document.createElement('div');
        c.style.cssText='position:fixed;right:10px;top:64px;width:118px;height:118px;z-index:6;'
         +'background:#1f1d1a;border:1px solid #3a352c;border-radius:14px;'
         +'font:11px system-ui;color:#ccc;padding:8px;box-sizing:border-box';
        c.innerHTML='<div style="width:100%;height:56px;border-radius:9px;background:#33302b"></div>'
         +'<div style="margin-top:5px;font-weight:600;font-size:11px">Sponsored</div>'
         +'<div style="color:#c9a227;font-size:10px;margin-top:2px">Install &rsaquo;</div>'
         +'<div style="position:absolute;left:6px;top:2px;border:1px solid #c9a227;color:#c9a227;'
         +'font-size:8px;border-radius:3px;padding:0 3px">Ad</div>';
        document.body.appendChild(c);
      }
      await new Promise(r=>setTimeout(r,700));
    }, [css, adOn, ADH, strip.toString(), name]);
    await pg.waitForTimeout(600);
    await pg.screenshot({ path: OUT+'/hud_'+name+'.png' });
    console.log('shot '+name);
    await ctx.close();
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
