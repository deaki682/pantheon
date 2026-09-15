// Pictures of everything that changed in v487. The ad is a NATIVE view - the
// browser never sees it - so it is drawn here from the exact numbers
// buildCorner()/adCornerParams() compute for this screen. Everything else is
// the real page.
const { chromium } = require('playwright-core');
const fs=require('fs');
const OUT=process.argv[2]||'/tmp/shots';
const PORT=process.argv[3]||'8899';
fs.mkdirSync(OUT,{recursive:true});

// ---- the shells' own arithmetic, mirrored -----------------------------
function card(W,H){
  const tab=Math.min(W,H)>=600, land=W>H;
  const gut=tab?12:8, padR=8, FLANK=48;
  const playerH=tab?160:120, playerMax=tab?284:213, textWant=tab?230:106;
  const TALLW=160, TALLPH=190, TALLHDR=46;
  if (land){   // unchanged: the standing card down the free left edge
    return {mode:'tall', boxW:TALLW, boxH:TALLPH+TALLHDR,
            playerW:TALLW-16, playerH:TALLPH, textW:TALLW-16, hdr:TALLHDR, gut, padR};
  }
  // FLUSH: wall to wall, no flanking column to clear
  const budget=W-padR;
  const playerW=Math.min(Math.max(budget-gut-padR-textWant,120),playerMax);
  const textW=Math.max(budget-playerW-gut-padR,40);
  return {mode:'flush', boxW:W, boxH:playerH, rest:64,
          playerW, playerH, textW, gut, padR};
}
function paint(c, bloom){
  const h = c.mode==='flush' ? (bloom ? c.boxH : c.rest) : c.boxH;
  const flush = c.mode==='flush';
  // the CLIP is the band's height and the player keeps its full 120 inside
  // it, centred - so a short band shows the middle of the creative
  const player =
    '<div style="width:'+c.playerW+'px;height:'+(flush?h:c.playerH)+'px;'
    +(flush?'':'margin:0 8px;')+'flex:none;position:relative;overflow:hidden">'
    +'<div style="position:absolute;left:0;width:'+c.playerW+'px;height:'+c.playerH+'px;'
    +'top:50%;transform:translateY(-50%);background:linear-gradient(135deg,#2f3d52,#15202e);'
    +'display:flex;align-items:center;justify-content:center">'
    +'<div style="width:0;height:0;border-left:22px solid rgba(255,255,255,.92);'
    +'border-top:14px solid transparent;border-bottom:14px solid transparent;margin-left:5px"></div>'
    +'<span style="position:absolute;right:5px;bottom:4px;font:10px system-ui;color:#cfcfcf;'
    +'background:rgba(0,0,0,.45);padding:1px 4px;border-radius:3px">0:15</span></div></div>';
  const badge='<span style="font:9px system-ui;color:#e8833a;border:1px solid #e8833a;'
    +'border-radius:3px;padding:0 3px;align-self:flex-start;flex:none">Ad</span>';
  const words='A headline from the auction';
  const text = c.mode==='tall'
    ? '<div style="padding:0 8px;height:'+c.hdr+'px;display:flex;align-items:center;gap:5px;'
      +'width:'+c.boxW+'px;flex:none">'+badge
      +'<span style="font:11px system-ui;color:#e8e6e1;line-height:1.2;display:-webkit-box;'
      +'-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">'+words+'</span></div>'
    : '<div style="padding:0 '+c.padR+'px 0 '+c.gut+'px;display:flex;flex-direction:column;'
      +'justify-content:center;width:'+c.textW+'px;'
      +(flush?'height:'+h+'px;':'')+'">'+badge
      +'<span style="font:11px system-ui;color:#e8e6e1;margin-top:4px;line-height:1.25;'
      +'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">'
      +words+', two lines at most</span></div>';
  const box = flush
    ? 'position:fixed;z-index:40;top:0;left:0;right:0;height:'+h+'px;border-radius:0;'
      +'border-bottom:1px solid #555;'
    : 'position:fixed;z-index:40;top:8px;left:8px;width:'+c.boxW+'px;height:'+h+'px;'
      +'border-radius:14px;border:1px solid #555;box-shadow:0 6px 18px rgba(0,0,0,.55);';
  return '<div id="adFake" style="'+box+'background:#1e1e1e;overflow:hidden;display:flex;'
    +'flex-direction:'+(c.mode==='tall'?'column':'row')+'">'
    +(c.mode==='tall' ? text+player : player+text)+'</div>';
}

const SEED = async ()=>{
  const Wi=4032,Hi=3024; const c=document.createElement('canvas'); c.width=Wi;c.height=Hi;
  const g=c.getContext('2d');
  const gr=g.createRadialGradient(Wi*0.36,Hi*0.34,Wi*0.05,Wi*0.5,Hi*0.5,Wi*0.72);
  gr.addColorStop(0,'#f6f2ec'); gr.addColorStop(0.45,'#9a8f85'); gr.addColorStop(1,'#14100d');
  g.fillStyle=gr; g.fillRect(0,0,Wi,Hi);
  let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
  for (let i=0;i<30000;i++){ g.fillStyle='rgba(255,255,255,.35)'; g.fillRect(rnd()*Wi,rnd()*Hi,2,2); }
  const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
  await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
  for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
  $('unit').value='cm'; $('widthIn').value='30';
  show('scrFormat'); await new Promise(r=>setTimeout(r,400));
  $('fmtGo').onclick();
  for (let i=0;i<400;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  await new Promise(r=>setTimeout(r,800));
};

(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const shot = async (name, W, H, body) => {
    const ctx = await br.newContext({ viewport:{width:W,height:H},
      deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
      localStorage.setItem('holdMain','1'); localStorage.setItem('holdCmp','1'); });
    const pg = await ctx.newPage();
    await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await body(pg, W, H);
    await pg.screenshot({path:OUT+'/'+name+'.png'});
    console.log('  '+name+'.png');
    await ctx.close();
  };
  const withAd = async (pg,W,H,bloom)=>{
    const c=card(W,H);
    await pg.evaluate(([html,top])=>{
      document.documentElement.style.setProperty('--adtop', top+'px');
      if (typeof __adCorner==='function') __adCorner(true);
      document.documentElement.style.setProperty('--adtop', top+'px');
      document.body.insertAdjacentHTML('beforeend', html);
    }, [paint(c,bloom), c.mode==='flush' ? (bloom?c.boxH:c.rest) : 0]);
    await pg.waitForTimeout(250);
  };
  const toCompare = async (pg)=>{
    await pg.evaluate(async ()=>{
      show('scrCompare');
      CMP.img = refCanvas(); CMP.mode='flip';
      cmpSize(); cmpButtons(); cmpRender();
      await new Promise(r=>setTimeout(r,600));
    });
  };

  console.log('drawing screen');
  await shot('01-drawing-portrait', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false); });
  await shot('02-drawing-portrait-video', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,true); });
  await shot('03-drawing-landscape', 852, 393, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false); });

  console.log('the floating menus');
  await shot('04-menu-detail', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>$('detBtn').click()); await pg.waitForTimeout(300); });
  await shot('05-menu-grid', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>$('gridBtn').click()); await pg.waitForTimeout(300); });
  await shot('06-menu-under', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>{ $('underCorner').style.display='block'; $('underBtn').click(); });
    await pg.waitForTimeout(300); });
  await shot('07-menu-tools', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>$('hudToggle').click()); await pg.waitForTimeout(400); });
  console.log('the readout that replaced the gear');
  await shot('16-true-to-life', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>ttlPop()); await pg.waitForTimeout(450); });
  await shot('17-mark-tally', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false);
    await pg.evaluate(()=>{ DONETOOL=true; markBadge(true); }); await pg.waitForTimeout(450); });

  console.log('comparison screen');
  await shot('08-compare-portrait', 393, 852, async (pg,W,H)=>{ await pg.evaluate(SEED); await toCompare(pg); await withAd(pg,W,H,false); });
  await shot('09-compare-landscape', 852, 393, async (pg,W,H)=>{ await pg.evaluate(SEED); await toCompare(pg); await withAd(pg,W,H,false); });

  console.log('the editor');
  await shot('10-editor-portrait', 393, 852, async (pg)=>{ await pg.evaluate(SEED);
    await pg.evaluate(async ()=>{ edOpenFor('crop'); await new Promise(r=>setTimeout(r,900)); }); });
  await shot('11-editor-landscape', 852, 393, async (pg)=>{ await pg.evaluate(SEED);
    await pg.evaluate(async ()=>{ edOpenFor('crop'); await new Promise(r=>setTimeout(r,900)); }); });
  await shot('12-editor-tone', 393, 852, async (pg)=>{ await pg.evaluate(SEED);
    await pg.evaluate(async ()=>{ edOpenFor('tone'); await new Promise(r=>setTimeout(r,900)); }); });

  console.log('tablet');
  await shot('13-drawing-tablet-portrait', 800, 1280, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false); });
  await shot('14-drawing-tablet-landscape', 1280, 800, async (pg,W,H)=>{ await pg.evaluate(SEED); await withAd(pg,W,H,false); });

  console.log('home');
  await shot('15-home', 393, 852, async (pg)=>{ await pg.evaluate(SEED);
    await pg.evaluate(async ()=>{ show('scrUpload'); await new Promise(r=>setTimeout(r,500)); }); });
  await br.close();
})();
