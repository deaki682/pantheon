// The comparison screen, in the drawing screen's shape: the red error circle
// in the top-LEFT corner with Download directly beneath it, and the whole
// top-RIGHT left to the ad banner. Sideways the tools stand down the RIGHT
// edge with their panel opening inward, the see-through slider on end to
// their left and the mirror button left of that - all of it centred, so the
// top-right corner stays the banner's. No back arrow either way, and back
// steps to the drawing screen.
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
      await new Promise(r=>setTimeout(r,600));
    });
    const r = await pg.evaluate(()=>{
      const b=el=>{const q=el.getBoundingClientRect();
        return {x:Math.round(q.x),y:Math.round(q.y),w:Math.round(q.width),h:Math.round(q.height),
                r:Math.round(q.right),b:Math.round(q.bottom),
                vis:getComputedStyle(el).display!=='none' && q.width>1};};
      const crop = getComputedStyle($('cmpReCrop')).display!=='none'
                   ? $('cmpReCrop') : $('cmpCrop');
      return { back:b($('backBtn')), circ:b($('circBtn')), dl:b($('dlBtn')),
               row:b($('cmpRow')), mir:b($('mirBtn')), sl:b($('alphaSl')),
               crop:b(crop), flip:b($('cmpFlip')), lv:b($('lvBtn')),
               pad:getComputedStyle($('scrCompare')).paddingBottom,
               order:[...$('cmpRow').querySelectorAll('button')]
                 .filter(b=>getComputedStyle(b).display!=='none')
                 .map(b=>({b,o:+getComputedStyle(b).order||0,y:b.getBoundingClientRect().top}))
                 .sort((a,c)=>a.o-c.o || a.y-c.y).map(x=>x.b.id),
               dir:getComputedStyle($('cmpRow')).flexDirection,
               vw:innerWidth, vh:innerHeight };
    });
    console.log(dev.n+'  circle '+r.circ.x+','+r.circ.y+
                '   download '+r.dl.x+','+r.dl.y+
                '   tools '+r.row.x+','+r.row.y+' ('+r.dir+')   padding-bottom '+r.pad);
    ok(!r.back.vis, dev.n+': no back arrow on the comparison screen');
    ok(r.pad==='0px', dev.n+': it reserves nothing for a strip');
    if (!dev.land){
      ok(r.circ.x < 40 && r.dl.x < 40, dev.n+': mark and Download are on the LEFT edge');
      ok(Math.abs(r.circ.x - r.dl.x) < 2, dev.n+': and they line up in a column');
      ok(r.circ.y < 40, dev.n+': the mark holds the top-left corner');
      ok(Math.abs(r.dl.y - (r.circ.y + r.circ.h)) < 1.5,
         dev.n+': Download is FUSED to the mark\'s lower edge ('
         +(r.dl.y-(r.circ.y+r.circ.h))+'px apart)');
      ok(Math.abs(r.dl.w - r.dl.h) < 1.5 && Math.abs(r.circ.w - r.circ.h) < 1.5,
         dev.n+': each half is a SQUARE, so the pill is 2:1 ('
         +r.circ.w+'x'+r.circ.h+')');
      ok(r.vh - r.row.b <= 10, dev.n+': the bottom row is 8px off the edge');
      // the middle line: crop at one end, mirror at the other, slider between
      ok(r.crop.r <= r.sl.x + 2, dev.n+': crop sits LEFT of the slider');
      ok(r.mir.x >= r.sl.r - 2, dev.n+': and the mirror RIGHT of it');
      ok(Math.abs((r.crop.y+r.crop.h/2)-(r.sl.y+r.sl.h/2)) < 14 &&
         Math.abs((r.mir.y+r.mir.h/2)-(r.sl.y+r.sl.h/2)) < 14,
         dev.n+': all three on one line');
      ok(r.mir.b <= r.row.y + 2, dev.n+': and that line is ABOVE the four buttons');
      // ...each end over the outermost of the four
      ok(Math.abs(r.crop.x - r.flip.x) < 24,
         dev.n+': crop is over Flip ('+r.crop.x+' vs '+r.flip.x+')');
      ok(Math.abs(r.mir.r - r.lv.r) < 24,
         dev.n+': the mirror is over Adjust ('+r.mir.r+' vs '+r.lv.r+')');
    } else {
      // sideways: the pill lies down IN the bottom-left corner, mark first -
      // the drawing screen's order
      ok(r.vh - (r.dl.y + r.dl.h) <= 12 && r.vh - (r.circ.y + r.circ.h) <= 12,
         dev.n+': both halves are along the BOTTOM');
      ok(r.circ.x < 40, dev.n+': the mark takes the bottom-left corner');
      ok(Math.abs(r.dl.x - (r.circ.x + r.circ.w)) < 1.5,
         dev.n+': Download is FUSED to its right edge ('
         +(r.dl.x-(r.circ.x+r.circ.w))+'px apart)');
      ok(r.circ.y > 120, dev.n+': the top-left corner is left to the card');
      // the tools spread over the WHOLE right edge, in working order
      ok(r.dir==='column', dev.n+': the tools stand in a column');
      ok(r.vw - r.row.r <= 12, dev.n+': the tools hug the right edge');
      ok(r.row.y <= 12 && r.vh - r.row.b <= 12,
         dev.n+': and are spread over its full height ('+r.row.y+' to '+r.row.b+' of '+r.vh+')');
      ok(r.order.join(' ')==='cmpGridBtn cmpSplit cmpFlip lvBtn',
         dev.n+': grid, compare, flip, adjust - top to bottom ('+r.order.join(' ')+')');
      // the slider lies FLAT along the bottom, a third as long, mirror above
      ok(r.sl.w > r.sl.h, dev.n+': the see-through slider lies flat');
      ok(r.sl.w < r.vw*0.42, dev.n+': and is about a third as long ('
         +Math.round(100*r.sl.w/r.vw)+'% of the width)');
      ok(r.vh - r.sl.b < 40, dev.n+': along the bottom');
      ok(r.mir.x >= r.sl.r - 2, dev.n+': with the mirror button to its RIGHT ('
         +r.sl.r+' -> '+r.mir.x+')');
      ok(r.crop.r <= r.sl.x + 2, dev.n+': and CROP to its left ('
         +r.crop.r+' -> '+r.sl.x+')');
      ok(Math.abs((r.mir.y+r.mir.h/2) - (r.sl.y+r.sl.h/2)) < 12,
         dev.n+': on the same line');
      ok(r.sl.x > r.dl.r && r.mir.r < r.row.x, dev.n+': clear of both the pill and the tools');
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
