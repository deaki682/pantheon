// Mid-gesture the grid canvas rides a transform of its last bake instead of
// re-rasterizing. That transform has to put the lattice exactly where the
// paper is - during a PINCH as well as a drag. pan_bare only ever dragged,
// where the scale is 1 and an error in the scale term cannot show.
//
// The canvas is laid out at -P (the overscan band) with transform-origin
// 0 0, so a world point baked at element-local u lands at -P + tx + k*u.
// For that to equal the true view.x + wx*view.s, tx must carry P*(1-k).
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof applyView==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null; for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });
  const rows = await pg.evaluate(async ()=>{
    const out=[];
    const b=vpBox(); const {w,h}=worldSize();
    const fit=Math.min(b.width/w,b.height/h);
    const cv=document.getElementById('gridCv');
    // a pinch: settle, then change the scale WITHOUT lifting
    for (const z of [1.25, 1.6, 2.4, 0.85, 3.2]){
      view.s=fit*1.5; view.x=(b.width-w*view.s)/2; view.y=(b.height-h*view.s)/2;
      GESTURE.active=false; GRID_SIG=null; applyView(); drawGrid();
      await new Promise(r=>setTimeout(r,250));
      const base={x:view.x,y:view.y,s:view.s};
      GESTURE.active=true;
      // pinch about the viewport centre, the way a two-finger zoom does
      const cx=b.width/2, cy=b.height/2;
      const ns=base.s*z;
      view.s=ns;
      view.x=cx-(cx-base.x)*(ns/base.s);
      view.y=cy-(cy-base.y)*(ns/base.s);
      applyView();
      await new Promise(r=>setTimeout(r,80));
      const t=cv.style.transform;
      const m=t? t.match(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/) : null;
      const rode = !!m;
      let errX=0, errY=0, bare=0;
      if (rode){
        const tx=+m[1], ty=+m[2], k=+m[3];
        const P=(GRID_DRAWN&&GRID_DRAWN.p)||0;
        // where the ride puts the world origin, against where it truly is
        const u0x=GRID_DRAWN.x+P, u0y=GRID_DRAWN.y+P;
        errX = (-P + tx + k*u0x) - view.x;
        errY = (-P + ty + k*u0y) - view.y;
        // and zooming OUT shrinks the band: whatever of the paper is on
        // screen still has to be inside it, or the lattice stops short
        const cw=parseFloat(cv.style.width)||0, chh=parseFloat(cv.style.height)||0;
        const L=-P+tx, T=-P+ty, R=L+k*cw, B=T+k*chh;
        const pl=view.x, pt=view.y, pr=view.x+w*view.s, pb=view.y+h*view.s;
        const nl=Math.max(0,pl), nt=Math.max(0,pt),
              nr=Math.min(b.width,pr), nb=Math.min(b.height,pb);
        if (nr>nl && nb>nt) bare=Math.max(0, Math.round(Math.max(L-nl, T-nt, nr-R, nb-B)));
      }
      GESTURE.active=false;
      out.push({ z, rode, errX:+errX.toFixed(1), errY:+errY.toFixed(1), bare,
                 pad:(GRID_DRAWN&&GRID_DRAWN.p)||0 });
    }
    return out;
  });
  let bad=0;
  for (const r of rows){
    const ok = !r.rode || (Math.abs(r.errX)<=0.6 && Math.abs(r.errY)<=0.6 && r.bare<=1);
    if (!ok) bad++;
    console.log('  pinch x'+String(r.z).padEnd(5)+' band '+String(r.pad).padStart(3)+'px   '
      +(r.rode?'rode the transform':'re-baked        ')
      +'   off by '+String(r.errX).padStart(6)+', '+String(r.errY).padStart(6)
      +'   bare '+String(r.bare||0).padStart(3)+'px   '+(ok?'ok':'FAIL'));
  }
  console.log(bad? '\n'+bad+' zoom(s) misplace the grid' : '\nthe grid tracks the zoom');
  await br.close();
  process.exit(bad?1:0);
})().catch(e=>{console.error(e);process.exit(1)});
