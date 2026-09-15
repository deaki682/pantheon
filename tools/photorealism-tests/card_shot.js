// A picture of the video card on the drawing screen. The card itself is a
// NATIVE Android view - the browser never sees it - so this draws a stand-in
// from the exact numbers buildCorner() computes for this screen width, at the
// exact anchor adCornerParams() gives it. Everything around it is the real
// page. It is a measurement drawing, not a live creative.
const { chromium } = require('playwright-core');
const fs=require('fs');
const OUT=process.argv[2]||'.', TAG=process.argv[3]||'now';
const W=Number(process.argv[4]||411), H=Number(process.argv[5]||891);
// An iPhone with a Dynamic Island: the shell constrains BOTH the web view and
// the card to the safe-area guide, so neither can be drawn under the island -
// but the browser reports env(safe-area-inset-*) as 0, so the harness stands
// in for it. SAFE_TOP is the island phone's portrait inset, SAFE_BOT the home
// indicator's, and the island itself is drawn over the top to scale.
const ISLAND = process.argv[6] === 'island';
const CMP = process.argv.includes('compare');
const SAFE_TOP = ISLAND ? 59 : 0, SAFE_BOT = ISLAND ? 34 : 0;

// --- the same arithmetic as MainActivity.buildCorner --------------------
const BANNER = process.argv[7] === 'banner';   // the resting state
const tab = Math.min(W,H) >= 600;
const gut = tab ? 12 : 8, padR = 8, FLANK = 48, BANNER_H = 48;
const playerH = tab ? 160 : 120, playerMax = tab ? 284 : 213;
const textWant = tab ? 230 : 118;
const flank = 8 + (tab?76:44);
// top-right corner: only the LEFT column has to be cleared
const budget = W - (flank + FLANK) - 8;
const playerW = Math.min(Math.max(tab ? budget - gut - padR - textWant : 120, 120), playerMax);
const textW = Math.min(Math.max(budget - playerW - gut - padR, 40), textWant);
const LAND = W > H;   // sideways the card takes the top-LEFT corner and STANDS UP
const stack = LAND;
const boxW = stack ? playerW + 16 : playerW + gut + textW + padR;
const boxH = BANNER ? BANNER_H : (stack ? playerH + 62 : playerH);

(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:W,height:H}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  // the two chrome buttons are a COLUMN - the gear in the corner, Download
  // beneath it - so the stand-in has to shift them by the safe area without
  // flattening them onto one another
  if (ISLAND) await pg.addStyleTag({content:
    '#setCorner,#circWrap{top:'+(8+SAFE_TOP)+'px!important}'
    +'#expCorner,#dlWrap{top:'+(84+SAFE_TOP)+'px!important}'
    +'#hudWrap,#detCorner,#gridCorner,#underCorner,#camCorner{'
    +'bottom:'+(8+SAFE_BOT)+'px!important}'});
  await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    // a real photograph's worth of tone, so the grid reads over it
    const Wi=4032,Hi=3024; const c=document.createElement('canvas'); c.width=Wi;c.height=Hi;
    const g=c.getContext('2d');
    const gr=g.createRadialGradient(Wi*0.36,Hi*0.34,Wi*0.05,Wi*0.5,Hi*0.5,Wi*0.72);
    gr.addColorStop(0,'#f6f2ec'); gr.addColorStop(0.45,'#9a8f85');
    gr.addColorStop(1,'#14100d'); g.fillStyle=gr; g.fillRect(0,0,Wi,Hi);
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<30000;i++){ g.fillStyle='rgba(255,255,255,.35)';
      g.fillRect(rnd()*Wi,rnd()*Hi,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
    show('scrFormat'); await new Promise(r=>setTimeout(r,400));
    $('fmtGo').onclick();
    for (let i=0;i<400;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    await new Promise(r=>setTimeout(r,700));
    if (typeof __adCorner==='function') __adCorner(true);
  });
  if (CMP) await pg.evaluate(async ()=>{
    show('scrCompare');
    $('circWrap').style.display='flex';
    $('dlWrap').style.display='block';
    $('mirRow').style.display=''; $('cmpRow').style.display='';
    $('circClr').style.display='';
    await new Promise(r=>setTimeout(r,700));
  });
  // the stand-in, at the measured geometry, anchored the way the shell anchors it
  await pg.evaluate(([boxW,boxH,playerW,playerH,textW,gut,padR,stack,SAFE_TOP,BANNER,LAND])=>{
    const d=document.createElement('div');
    d.style.cssText='position:fixed;z-index:40;top:'+(8+SAFE_TOP)+'px;'
      +(LAND?'left:8px;':'right:8px;')
      +'width:'+boxW+'px;height:'+boxH+'px;'
      +'background:#1e1e1e;border:1px solid #555;border-radius:14px;'
      +'box-shadow:0 6px 18px rgba(0,0,0,.55);overflow:hidden;display:flex;'
      +'flex-direction:'+(stack?'column':'row')+';';
    const player =
      '<div style="width:'+(stack?boxW:playerW)+'px;height:'+(stack?Math.min(playerH,boxH):boxH)+'px;'
      +'flex:none;position:relative;'
      +'overflow:hidden">'
      +'<div style="width:'+playerW+'px;height:'+playerH+'px;position:absolute;'
      +'left:0;top:50%;transform:translateY(-50%);'
      +'background:linear-gradient(135deg,#2f3d52,#15202e);display:flex;'
      +'align-items:center;justify-content:center">'
      +'<div style="width:0;height:0;border-left:22px solid rgba(255,255,255,.92);'
      +'border-top:14px solid transparent;border-bottom:14px solid transparent;'
      +'margin-left:5px"></div>'
      +'<span style="position:absolute;right:5px;bottom:4px;font:10px system-ui;'
      +'color:#cfcfcf;background:rgba(0,0,0,.45);padding:1px 4px;border-radius:3px">0:15</span>'
      +'</div></div>';
    const badge = '<span style="font:9px system-ui;color:#e8833a;border:1px solid #e8833a;'
      +'border-radius:3px;padding:0 3px;align-self:flex-start;flex:none">Ad</span>';
    const words = 'A headline from the auction';
    d.innerHTML = player
        + '<div style="padding:'+(stack?'5px 8px 6px 8px':'0 '+padR+'px 0 '+gut+'px')+';'
        + 'display:flex;flex-direction:column;'
        + 'justify-content:center;width:'+(stack?(boxW-16):textW)+'px">'+badge
        + '<span style="font:11px system-ui;color:#e8e6e1;margin-top:4px;'
        + 'line-height:1.25;display:-webkit-box;-webkit-line-clamp:'+(BANNER?1:3)+';'
        + '-webkit-box-orient:vertical;overflow:hidden">'+words
        + ', three lines at most</span></div>';
    d.innerHTML += '<div style="position:absolute;right:5px;top:5px;width:22px;'
      +'height:22px;border-radius:11px;background:rgba(25,25,25,.9);color:#b9b5ae;'
      +'font:12px system-ui;display:flex;align-items:center;justify-content:center">\u2715</div>';
    document.body.appendChild(d);
    if (SAFE_TOP){
      // the island itself, to scale: ~125x36pt, 11pt down, centred
      const isl=document.createElement('div');
      isl.style.cssText='position:fixed;z-index:60;top:11px;left:50%;'
        +'transform:translateX(-50%);width:125px;height:36px;border-radius:18px;'
        +'background:#000';
      document.body.appendChild(isl);
      const bar=document.createElement('div');
      bar.style.cssText='position:fixed;z-index:60;left:50%;bottom:8px;'
        +'transform:translateX(-50%);width:140px;height:5px;border-radius:3px;'
        +'background:rgba(255,255,255,.75)';
      document.body.appendChild(bar);
    }
  }, [boxW,boxH,playerW,playerH,textW,gut,padR,stack,SAFE_TOP,BANNER,LAND]);
  await pg.waitForTimeout(250);
  const f=OUT+'/card_'+W+'x'+H+'_'+TAG+'.png';
  fs.writeFileSync(f, await pg.screenshot());
  const gapDp = Math.round(W - 8 - boxW - flank);
  console.log(W+'x'+H+'  card '+boxW+'x'+boxH+'  player '+playerW+'x'+playerH
    +'  text '+textW+(BANNER?'  [banner]':'  [bloomed]')
    +'  clear of the button column '+gapDp+'dp ('+(gapDp/6.3).toFixed(1)+'mm)');
  console.log('  -> '+f);
  await br.close();
})();
