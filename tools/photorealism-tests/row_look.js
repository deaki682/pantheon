// The drawing screen's top row is back / Download / gear, left to right,
// in both orientations (landscape puts Download at the TOP-LEFT and runs
// the three down the left edge). No strip on this screen at all.
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
               vw:innerWidth };
    });
    console.log(dev.n+'  back '+Math.round(r.back.x)+','+Math.round(r.back.y)+
                '   download '+Math.round(r.dl.x)+','+Math.round(r.dl.y)+
                '   gear '+Math.round(r.gear.x)+','+Math.round(r.gear.y));
    ok(r.back.vis, dev.n+': the back arrow is there');
    ok(r.dl.vis,   dev.n+': the download button is there');
    ok(r.gear.vis, dev.n+': the gear is there');
    ok(r.gearSvg!=='none', dev.n+': the gear is an icon again, not a bare label');
    ok(r.gearBg!=='rgba(0, 0, 0, 0)', dev.n+': the gear wears its button chrome');
    if (dev.land){
      // down the left edge: download top, gear middle, back bottom
      ok(r.dl.y < r.gear.y && r.gear.y < r.back.y, dev.n+': download top, gear middle, back bottom');
      ok(Math.abs(r.dl.x-r.back.x)<12 && Math.abs(r.dl.x-r.gear.x)<12, dev.n+': all three on the left edge');
      ok(r.dl.y < 40, dev.n+': download is in the TOP-left corner');
    } else {
      ok(r.back.x < r.dl.x && r.dl.x < r.gear.x, dev.n+': back, download, gear - in that order');
      const mid = Math.abs((r.dl.x + r.dl.w/2) - r.vw/2);
      ok(mid < 3, dev.n+': download is centred in the top row (off by '+mid.toFixed(1)+'px)');
      const rowY = Math.max(Math.abs(r.back.y-r.dl.y), Math.abs(r.gear.y-r.dl.y));
      ok(rowY < 6, dev.n+': all three sit on one row');
    }
    // the transformation: while the card is up the button yields
    const yielded = await pg.evaluate(async ()=>{
      __adCorner(true); await new Promise(r=>setTimeout(r,450));
      const s=getComputedStyle($('expCorner'));
      const out = { op:+s.opacity, pe:s.pointerEvents };
      __adCorner(false); await new Promise(r=>setTimeout(r,450));
      const s2=getComputedStyle($('expCorner'));
      return { ...out, backOp:+s2.opacity };
    });
    ok(yielded.op<0.05 && yielded.pe==='none', dev.n+': the button yields to the video card');
    ok(yielded.backOp>0.95, dev.n+': and comes back when the card retracts');
    ok(errs.length===0, dev.n+': no page errors'+(errs.length?' -> '+errs[0]:''));
    fs.writeFileSync(OUT+'/row_'+dev.n+'_'+TAG+'.png', await pg.screenshot());
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ntop row OK');
  process.exit(bad?1:0);
})();
