// The composite now writes straight into the picture in one pass. Every
// layer combination, every detail level, both modes: the pixels must be
// exactly what they were.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899', TAG=process.argv[3]||'now', OUT=process.argv[4]||'.';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#fff'); gr.addColorStop(1,'#111'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    let sd=20260915; const rnd=()=>{ sd=(sd*1103515245+12345)&0x7fffffff; return sd/0x7fffffff; };
    for (let i=0;i<40000;i++){ g.fillStyle='rgba(255,255,255,.4)'; g.fillRect(rnd()*W,rnd()*H,2,2); }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click();
    for (let i=0;i<4000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,80)); }
    await new Promise(r=>setTimeout(r,7000));      // let the detail levels cook
  });
  const fs=require('fs');
  const combos=[];
  for (const dk of [0,1]) for (const lt of [0,1]) for (const hl of [0,1]) combos.push([dk,lt,hl]);
  for (const det of ['ultra','hyper','fine']){
    for (const [dk,lt,hl] of combos){
      const png = await pg.evaluate(async ([dk,lt,hl,det])=>{
        LAYERS.dk=!!dk; LAYERS.lt=!!lt; LAYERS.hl=!!hl;
        DETAIL=det; COMP.sig=null;
        const cv=compositeCv();
        await new Promise(r=>setTimeout(r,120));
        return cv.toDataURL('image/png');
      }, [dk,lt,hl,det]);
      fs.writeFileSync(OUT+'/lay_'+det+'_'+dk+lt+hl+'_'+TAG+'.png',
        Buffer.from(png.split(',')[1],'base64'));
    }
  }
  if (errs.length) console.log('page errors:', errs.slice(0,3));
  console.log(TAG+': '+(combos.length*3)+' composites');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
