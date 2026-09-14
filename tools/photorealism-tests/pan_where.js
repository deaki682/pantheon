// The drag costs ~200-480ms a move. Which part? Turn one thing off at a
// time and re-measure the same drag.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof drawGrid==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    let r=null;
    for (let i=0;i<400;i++){ r=(await galAll()).find(x=>x.blob); if (r) break; await new Promise(r2=>setTimeout(r2,100)); }
    openPhoto(r.blob,r.id);
    for (let i=0;i<600;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
  });

  const CASES = [
    ['everything on',        {}],
    ['grid OFF entirely',    {gridOn:false}],
    ['punch off (red grid)', {col:'#ff3b30'}],
    ['no edge labels',       {noLabs:true}],
    ['no error circles',     {noCircs:true}],
    ['no done squares',      {noDone:true}],
  ];
  for (const [name, opt] of CASES){
    const r = await pg.evaluate(async ([opt])=>{
      GRID_STYLE='sq'; GRID_ON=opt.gridOn===false?false:true;
      GRID_COL=opt.col||'auto'; GRID_LAB=!opt.noLabs;
      const savedCircs=CIRCS, savedDone=DONE;
      if (opt.noCircs) CIRCS=[];
      if (opt.noDone) DONE=[];
      const b=vpBox(); const {w,h}=worldSize();
      const fit=Math.min(b.width/w, b.height/h);
      view.s=fit*2; view.x=(b.width-w*view.s)/2; view.y=(b.height-h*view.s)/2;
      GRID_SIG=null; applyView(); drawGrid();
      await new Promise(r=>setTimeout(r,500));
      const cv=document.getElementById('gridCv');
      const flush=()=>{ try{ cv.getContext('2d').getImageData(0,0,1,1); }catch(e){} };
      const send=(type,x,y)=>{
        const e=new PointerEvent(type,{pointerId:1,pointerType:'touch',isPrimary:true,
          clientX:x,clientY:y,buttons:type==='pointerup'?0:1,bubbles:true,cancelable:true});
        (document.elementFromPoint(x,y)||cv).dispatchEvent(e);
      };
      let x=330,y=700; const cost=[];
      send('pointerdown',x,y);
      for (let i=1;i<=20;i++){
        x-=18; y-=9;
        const t0=performance.now();
        send('pointermove',x,y); flush();
        cost.push(performance.now()-t0);
        await new Promise(r=>requestAnimationFrame(()=>r()));
      }
      send('pointerup',x,y);
      await new Promise(r=>setTimeout(r,250));
      CIRCS=savedCircs; DONE=savedDone; GRID_COL='auto'; GRID_ON=true; GRID_LAB=false;
      cost.sort((a,b)=>a-b);
      return { med:+(cost[Math.floor(cost.length/2)]||0).toFixed(1),
               circs:savedCircs.length, done:savedDone.length };
    }, [opt]);
    console.log('  '+name.padEnd(24)+String(r.med).padStart(7)+'ms per move'
      + (name==='everything on' ? '   ('+r.circs+' circles, '+r.done+' done squares)' : ''));
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
