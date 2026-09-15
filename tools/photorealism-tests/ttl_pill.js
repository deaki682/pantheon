// The "True to Life" message takes the WHOLE pill: the top half grows to the
// pill's full height and closes its rounding, Download stands down under it,
// and it lingers long enough to be read. The tally during marking must NOT
// do this - that state lasts a whole session and Download has to stay.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  for (const dev of [{n:'portrait', w:411, h:891, land:false},
                     {n:'landscape', w:891, h:411, land:true}]){
    const ctx = await br.newContext({ viewport:{width:dev.w,height:dev.h}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
    await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
      for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
    const pg = await ctx.newPage();
    const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
    await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
    await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
    await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
    await pg.evaluate(async ()=>{
      const c=document.createElement('canvas'); c.width=2400;c.height=1800;
      const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,2400,1800);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
      await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      show('scrFormat'); await new Promise(r=>setTimeout(r,300));
      $('fmtGo').onclick();
      for (let i=0;i<500;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,400));
    });
    const r = await pg.evaluate(async ()=>{
      const m=el=>{ const q=el.getBoundingClientRect();
        return {w:Math.round(q.width),h:Math.round(q.height),
                op:+getComputedStyle(el).opacity,
                rad:getComputedStyle(el).borderRadius}; };
      const rest={gear:m($('setBtn')), dlWrap:m($('expCorner'))};
      DONETOOL=false; ttlPop();
      await new Promise(r=>setTimeout(r,450));       // past the morph
      // how many LINES the message stacks into: its height over its own
      // line box, which is what "a word to a line" actually means
      const tx=$('setBtn').querySelector('.ttlTxt');
      const cs=getComputedStyle(tx);
      const lines=Math.round(tx.getBoundingClientRect().height/parseFloat(cs.lineHeight));
      const up={gear:m($('setBtn')), dlWrap:m($('expCorner')),
                txt:tx.textContent.trim(), lines,
                txtW:Math.round(tx.getBoundingClientRect().width)};
      await new Promise(r=>setTimeout(r,700));        // 1150ms in
      const stillUp=document.body.classList.contains('ttlOn');
      await new Promise(r=>setTimeout(r,650));        // 1800ms in, past 1400
      const gone=!document.body.classList.contains('ttlOn');
      await new Promise(r=>setTimeout(r,400));
      const back={gear:m($('setBtn')), dlWrap:m($('expCorner'))};
      // the marking tally keeps the pill whole
      const total=Math.max(1, GRID_COLS*GRID_ROWS);
      markBadge(true);
      await new Promise(r=>setTimeout(r,400));
      const marking={gear:m($('setBtn')), dlWrap:m($('expCorner'))};
      markBadge(false);
      return { rest, up, stillUp, gone, back, marking, total };
    });
    console.log(dev.n+'  gear '+r.rest.gear.w+'x'+r.rest.gear.h+' at rest -> '
      +r.up.gear.w+'x'+r.up.gear.h+' with the message ("'+r.up.txt+'")'
      +'   download opacity '+r.rest.dlWrap.op+' -> '+r.up.dlWrap.op);
    // the stack is an UPRIGHT thing: sideways the screen has width to spare
    // and no height, so the words stay on one line there
    if (!dev.land){
      ok(r.up.lines === 3, dev.n+': the message stacks a word to a line ('
         +r.up.lines+' lines, '+r.up.txtW+'px wide)');
      ok(r.up.gear.w <= r.rest.gear.w + 2,
         dev.n+': and never reaches past the pill\'s own width ('
         +r.up.gear.w+'px over a '+r.rest.gear.w+'px half)');
    } else {
      ok(r.up.lines === 1, dev.n+': the words stay side by side ('
         +r.up.lines+' line, '+r.up.txtW+'px wide)');
      ok(r.up.gear.w >= r.rest.gear.w * 2,
         dev.n+': and the pill grows along the bottom to hold them ('
         +r.up.gear.w+'px over a '+(r.rest.gear.w*2)+'px pill)');
    }
    if (dev.n==='portrait')
      ok(Math.abs(r.up.gear.h - r.rest.gear.h*2) <= 2,
         dev.n+': and it takes the WHOLE pill\'s height ('+r.up.gear.h+' vs 2x'+r.rest.gear.h+')');
    else
      ok(r.up.gear.h === r.rest.gear.h,
         dev.n+': lying down it keeps the pill\'s own height ('
         +r.up.gear.w+'x'+r.up.gear.h+')');
    ok(r.up.dlWrap.op < 0.05, dev.n+': Download stands down under it ('+r.up.dlWrap.op+')');
    ok(!/0px/.test(r.up.gear.rad), dev.n+': the pill closes its rounding back up ('+r.up.gear.rad+')');
    ok(r.stillUp, dev.n+': it is still up at 1.15s - long enough to read');
    ok(r.gone,    dev.n+': and gone by 1.8s');
    ok(r.back.gear.h === r.rest.gear.h && r.back.dlWrap.op > 0.95,
       dev.n+': the pill comes back whole afterwards');
    ok(r.marking.dlWrap.op > 0.95,
       dev.n+': the marking tally does NOT take Download away ('+r.marking.dlWrap.op+')');
    ok(errs.length===0, dev.n+': no page errors'+(errs.length?' -> '+errs[0]:''));
    await ctx.close();
  }
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\nthe message takes the pill OK');
  process.exit(bad?1:0);
})();
