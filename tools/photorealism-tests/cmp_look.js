// The comparison screen. Portrait: the red error circle takes the LEFT
// corner the back arrow used to hold, Download keeps the right, the gap
// between them is what the video card opens into, and the bottom row is
// back down at 8px. Landscape: the tools stand down the RIGHT edge with
// their panel opening inward, the see-through slider stands on end to
// their left with the mirror button left of that, and the LEFT edge runs
// card / circle / Download from top to bottom. No back arrow either way,
// and back steps to the drawing screen.
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
      // into the flip view, with the panels the layout has to place
      show('scrCompare');
      $('circWrap').style.display='flex';
      $('dlWrap').style.display='block';
      $('mirRow').style.display='';
      $('cmpRow').style.display='';
      $('circClr').style.display='';
      await new Promise(r=>setTimeout(r,600));
    });
    const r = await pg.evaluate(()=>{
      const b=el=>{const q=el.getBoundingClientRect();
        return {x:Math.round(q.x),y:Math.round(q.y),w:Math.round(q.width),h:Math.round(q.height),
                r:Math.round(q.right),b:Math.round(q.bottom),
                vis:getComputedStyle(el).display!=='none' && q.width>1};};
      return { back:b($('backBtn')), circ:b($('circBtn')), dl:b($('dlBtn')),
               row:b($('cmpRow')), mir:b($('mirBtn')), sl:b($('alphaSl')),
               pad:getComputedStyle($('scrCompare')).paddingBottom,
               dir:getComputedStyle($('cmpRow')).flexDirection,
               vw:innerWidth, vh:innerHeight };
    });
    console.log(dev.n+'  circle '+r.circ.x+','+r.circ.y+
                '   download '+r.dl.x+','+r.dl.y+
                '   tools '+r.row.x+','+r.row.y+' ('+r.dir+')   padding-bottom '+r.pad);
    ok(!r.back.vis, dev.n+': no back arrow on the comparison screen');
    ok(r.pad==='0px', dev.n+': it reserves nothing for a strip');
    if (!dev.land){
      ok(r.circ.x < 40, dev.n+': the red circle holds the left corner');
      ok(r.vw - r.dl.r < 40, dev.n+': Download keeps the right');
      const gap = r.dl.x - r.circ.r;
      ok(gap > 120, dev.n+': a '+gap+'px gap is left for the card');
      ok(Math.abs(r.circ.y - r.dl.y) < 6, dev.n+': both sit on one row');
      ok(r.vh - r.row.b <= 10, dev.n+': the bottom row is 8px off the edge ('
         +(r.vh-r.row.b)+'px)');
    } else {
      ok(r.dir==='column', dev.n+': the tools stand in a column');
      ok(r.vw - r.row.r <= 12, dev.n+': the tools hug the right edge ('
         +(r.vw-r.row.r)+'px)');
      ok(r.sl.r < r.row.x, dev.n+': the see-through slider is LEFT of the tools');
      ok(r.mir.r <= r.sl.x + 2, dev.n+': the mirror button is LEFT of the slider');
      ok(r.sl.h > r.sl.w, dev.n+': the slider stands on end ('+r.sl.w+'x'+r.sl.h+')');
      ok(r.circ.x < 40, dev.n+': the circle is on the LEFT edge');
      ok(Math.abs((r.circ.y + r.circ.h/2) - r.vh/2) < 30,
         dev.n+': the circle is the middle option on that edge');
      ok(r.dl.x < 40 && r.vh - r.dl.b <= 12,
         dev.n+': Download is at the BOTTOM-left');
      ok(r.dl.y > r.circ.y, dev.n+': circle above Download');
      // the top-left corner, where the card goes, is left free
      ok(r.circ.y > 100, dev.n+': the top-left corner is clear for the card');
    }
    // back steps to the drawing screen, arrow or no arrow
    const stepped = await pg.evaluate(async ()=>{
      const v=__backStep(); await new Promise(r=>setTimeout(r,400));
      return { v, on:(document.querySelector('.screen.on')||{}).id };
    });
    ok(stepped.on==='scrMain', dev.n+': back steps to the drawing screen (landed on '+stepped.on+')');
    ok(errs.length===0, dev.n+': no page errors'+(errs.length?' -> '+errs[0]:''));
    await pg.evaluate(()=>show('scrCompare'));
    await pg.waitForTimeout(350);
    fs.writeFileSync(OUT+'/cmp_'+dev.n+'_'+TAG+'.png', await pg.screenshot());
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\ncomparison screen OK');
  process.exit(bad?1:0);
})();
