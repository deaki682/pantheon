// The drawing screen's two controls are ONE pill down the LEFT edge - gear on
// the top half, Download on the bottom, sharing an edge, and sideways gear on
// the left half with Download on the right - and it leaves the whole
// top-RIGHT to the ad, which rests there as a thin banner and blooms to the
// video height now and then. Neither screen carries a back arrow or a strip,
// so their other controls sit 8px off the edge.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', TAG=process.argv[3]||'now', OUT=process.argv[4]||'.';
const fs=require('fs');
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const dev of [
      {n:'phoneP', w:411, h:891,  land:false},
      {n:'phoneL', w:891, h:411,  land:true},
      {n:'small',  w:320, h:640,  land:false},
      {n:'tabP',   w:800, h:1280, land:false},
      {n:'tabL',   w:1280,h:800,  land:true}]){
    const ctx = await br.newContext({ viewport:{width:dev.w,height:dev.h}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await pg.evaluate(async ()=>{
      const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
      gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
      await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      show('scrFormat'); await new Promise(r=>setTimeout(r,400));
      $('fmtGo').onclick();
      for (let i=0;i<400;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,600));
    });
    const r = await pg.evaluate(()=>{
      const b=el=>{const q=el.getBoundingClientRect();return {x:q.x,y:q.y,w:q.width,h:q.height,
        vis:getComputedStyle(el).display!=='none' && +getComputedStyle(el).opacity>0.02 && q.width>1};};
      return { back:b($('backBtn')), dl:b($('expBtn')), gear:b($('setBtn')),
               gearSvg:getComputedStyle($('setBtn').querySelector('svg')).display,
               gearBg:getComputedStyle($('setBtn')).backgroundColor,
               pad:getComputedStyle($('scrMain')).paddingBottom,
               hud:Math.round($('hudWrap').getBoundingClientRect().bottom),
               hudR:Math.round($('hudWrap').getBoundingClientRect().right),
               vw:innerWidth, vh:innerHeight };
    });
    console.log(dev.n+'  download '+Math.round(r.dl.x)+','+Math.round(r.dl.y)+
                '   gear '+Math.round(r.gear.x)+','+Math.round(r.gear.y)+
                '   scrMain padding-bottom '+r.pad);
    ok(!r.back.vis, dev.n+': no back arrow on the drawing screen');
    ok(r.dl.vis,   dev.n+': the download button is there');
    ok(r.gear.vis, dev.n+': the gear is there');
    ok(r.gearSvg!=='none', dev.n+': the gear is an icon, not a bare label');
    ok(r.gearBg!=='rgba(0, 0, 0, 0)', dev.n+': the gear wears its button chrome');
    ok(r.pad==='0px', dev.n+': the drawing screen reserves nothing for a strip');
    // portrait keeps the tools along the bottom, landscape down the right
    // edge - either way they sit 8px off it, with no strip to stand clear of
    if (!dev.land)
      ok(r.vh - r.hud <= 10, dev.n+': the tools are 8px off the bottom edge ('
         +(r.vh-r.hud)+'px)');
    else
      ok(r.vw - r.hudR <= 10, dev.n+': the tools are 8px off the right edge ('
         +(r.vw-r.hudR)+'px)');
    if (!dev.land){
      // upright: a column in the top-left, the card top-RIGHT
      ok(r.gear.x < 40 && r.dl.x < 40, dev.n+': both controls are on the LEFT edge');
      ok(Math.abs(r.gear.x - r.dl.x) < 2, dev.n+': and they line up in a column');
      ok(r.gear.y < 40, dev.n+': the gear holds the top-left corner');
      ok(Math.abs(r.dl.y - (r.gear.y + r.gear.h)) < 1.5,
         dev.n+': Download is FUSED to the gear\'s lower edge ('
         +Math.round(r.dl.y-(r.gear.y+r.gear.h))+'px apart)');
      ok(Math.abs(r.dl.w - r.gear.w) < 1.5, dev.n+': one pill, so both halves are the same width');
      ok(r.vw - (r.gear.x + r.gear.w) > 200, dev.n+': the top-RIGHT is clear for the card');
    } else {
      // sideways: the card stands up in the top-LEFT, so the pair sit side by
      // side in the BOTTOM-left, out from under it
      ok(r.vh - (r.gear.y + r.gear.h) <= 12 && r.vh - (r.dl.y + r.dl.h) <= 12,
         dev.n+': both controls are along the BOTTOM');
      ok(Math.abs(r.gear.y - r.dl.y) < 2, dev.n+': and side by side on one line');
      ok(r.gear.x < 40, dev.n+': the gear takes the bottom-left corner');
      ok(Math.abs(r.dl.x - (r.gear.x + r.gear.w)) < 1.5,
         dev.n+': Download is FUSED to the gear\'s right edge ('
         +Math.round(r.dl.x-(r.gear.x+r.gear.w))+'px apart)');
      ok(Math.abs(r.dl.h - r.gear.h) < 1.5, dev.n+': one pill, so both halves are the same height');
      ok(r.gear.y > 120, dev.n+': the top-left corner is left to the card');
    }
    // the card opens in the gap and covers neither button, so nothing on the
    // page has to move for it
    const held = await pg.evaluate(async ()=>{
      const box=()=>{ const a=$('expCorner').getBoundingClientRect(),
                            b=$('setCorner').getBoundingClientRect();
        return [a.x,a.y,b.x,b.y].map(Math.round).join(','); };
      const before=box();
      __adCorner(true); await new Promise(r=>setTimeout(r,450));
      const during=box();
      __adCorner(false); await new Promise(r=>setTimeout(r,450));
      return { before, during, after:box(),
               op:+getComputedStyle($('expCorner')).opacity };
    });
    ok(held.before===held.during && held.during===held.after,
       dev.n+': neither button moves when the card opens');
    ok(held.op>0.95, dev.n+': and the download button stays visible');
    ok(errs.length===0, dev.n+': no page errors'+(errs.length?' -> '+errs[0]:''));
    fs.writeFileSync(OUT+'/row_'+dev.n+'_'+TAG+'.png', await pg.screenshot());
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ntop row OK');
  process.exit(bad?1:0);
})();
