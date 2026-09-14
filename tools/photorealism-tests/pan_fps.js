// A sustained drag on the gridded reference, measured the way a finger
// experiences it: frames actually painted, the gap between them, and how
// many of those frames re-rasterized the whole grid instead of riding the
// transform the code already has.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
const ZOOMS = [1, 2, 4];
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });   // a mid phone
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null;
    for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break;
      await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });

  for (const style of ['sq','diag','dots']){
    for (const z of ZOOMS){
      const r = await pg.evaluate(async ([style,z])=>{
        GRID_STYLE=style; GRID_ON=true;
        const b=vpBox(); const {w,h}=worldSize();
        const fit=Math.min(b.width/w, b.height/h);
        view.s=fit*z; view.x=(b.width-w*view.s)/2; view.y=(b.height-h*view.s)/2;
        GRID_SIG=null; applyView(); drawGrid();
        await new Promise(r=>setTimeout(r,600));

        let bakes=0;
        const realDraw=window.drawGrid;
        window.drawGrid=function(){ bakes++; return realDraw.apply(this,arguments); };

        const cv=document.getElementById('gridCv');
        const flush=()=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
        const send=(type,x,y)=>{
          const e=new PointerEvent(type,{pointerId:1,pointerType:'touch',isPrimary:true,
            clientX:x,clientY:y,buttons:type==='pointerup'?0:1,bubbles:true,cancelable:true});
          (document.elementFromPoint(x,y)||cv).dispatchEvent(e);
        };
        // a finger crossing the screen in about half a second: ~20px a frame,
        // which is an ordinary drag, not a flick
        const STEP=20, moves=30;
        let x=330, y=700;
        const cost=[];
        send('pointerdown',x,y);
        for (let i=1;i<=moves;i++){
          x-=STEP*0.9; y-=STEP*0.44;
          const t0=performance.now();
          send('pointermove', x, y);
          flush();                       // make the raster happen NOW, not later
          cost.push(performance.now()-t0);
          await new Promise(r=>requestAnimationFrame(()=>r()));
        }
        send('pointerup', x, y);
        await new Promise(r=>setTimeout(r,300));
        window.drawGrid=realDraw;

        cost.sort((a,b)=>a-b);
        const med=cost[Math.floor(cost.length/2)]||0;
        const p95=cost[Math.floor(cost.length*0.95)]||0;
        return { bakes, moves, med:+med.toFixed(1), p95:+p95.toFixed(1),
          over16: cost.filter(c=>c>16.7).length,
          fps: med? +(1000/Math.max(med,1)).toFixed(0) : 0 };
      }, [style, z]);
      console.log(style.padEnd(5)+' '+String(z)+'x fit   '
        +'rebakes '+String(r.bakes).padStart(3)+'/'+r.moves
        +'   per move '+String(r.med).padStart(6)+'ms (p95 '+String(r.p95).padStart(6)+')'
        +'   '+String(r.fps).padStart(4)+' fps'
        +'   over 16.7ms: '+r.over16+'/'+r.moves);
    }
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
