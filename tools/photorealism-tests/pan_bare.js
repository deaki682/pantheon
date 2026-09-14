// The band lets the grid RIDE a transform instead of re-baking. If the gap
// maths is wrong by a sign the trailing edge goes bare - grid missing over
// part of the paper - and only mid-drag, where a still screenshot never
// looks. Drag, and after every single move check the grid still reaches
// wherever the paper is.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  let bad=0;
  for (const [dx,dy,name] of [[-22,-10,'up-left'],[22,10,'down-right'],[-26,6,'left'],[4,-26,'up']]){
    const r = await pg.evaluate(async ([dx,dy])=>{
      GRID_STYLE='sq'; GRID_ON=true; GRID_COL='auto';
      const b=vpBox(); const {w,h}=worldSize();
      const fit=Math.min(b.width/w,b.height/h);
      view.s=fit*3; view.x=(b.width-w*view.s)/2; view.y=(b.height-h*view.s)/2;
      GRID_SIG=null; applyView(); drawGrid();
      await new Promise(r=>setTimeout(r,500));
      const cv=document.getElementById('gridCv');
      const send=(type,x,y)=>{
        const e=new PointerEvent(type,{pointerId:1,pointerType:'touch',isPrimary:true,
          clientX:x,clientY:y,buttons:type==='pointerup'?0:1,bubbles:true,cancelable:true});
        (document.elementFromPoint(x,y)||cv).dispatchEvent(e);
      };
      let x=205,y=450; const bare=[];
      send('pointerdown',x,y);
      for (let i=1;i<=25;i++){
        x+=dx; y+=dy;
        send('pointermove',x,y);
        await new Promise(r=>requestAnimationFrame(()=>r()));
        // where does the transformed band actually land, in viewport px?
        const P=(GRID_DRAWN&&GRID_DRAWN.p)||0;
        const t=cv.style.transform;
        const m=t? t.match(/translate\\(([-\\d.]+)px,\\s*([-\\d.]+)px\\)\\s*scale\\(([-\\d.]+)\\)/) : null;
        const tx=m?+m[1]:0, ty=m?+m[2]:0, k=m?+m[3]:1;
        const cw=parseFloat(cv.style.width)||0, chh=parseFloat(cv.style.height)||0;
        const L=-P+tx, T=-P+ty, R=L+k*cw, B=T+k*chh;
        // the paper's own rect right now
        const {w,h}=worldSize();
        const pl=view.x, pt=view.y, pr=view.x+w*view.s, pb=view.y+h*view.s;
        const vb=vpBox();
        // the part of the paper that is on screen must be inside the band
        const nl=Math.max(0,pl), nt=Math.max(0,pt), nr=Math.min(vb.width,pr), nb=Math.min(vb.height,pb);
        if (nr>nl && nb>nt){
          const miss=Math.max(L-nl, T-nt, nr-R, nb-B);
          if (miss > 1) bare.push({ i, miss:Math.round(miss) });
        }
      }
      send('pointerup',x,y);
      await new Promise(r=>setTimeout(r,250));
      return { bare, pad:(GRID_DRAWN&&GRID_DRAWN.p)||0 };
    }, [dx,dy]);
    if (r.bare.length) bad++;
    console.log('  drag '+name.padEnd(11)+'band '+r.pad+'px   bare frames: '
      +(r.bare.length ? r.bare.length+'/25  worst '+Math.max(...r.bare.map(b=>b.miss))+'px  FAIL' : 'none  ok'));
  }
  console.log(bad? bad+' direction(s) went bare' : 'the grid never leaves a gap');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
