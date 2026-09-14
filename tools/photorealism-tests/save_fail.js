// What happens when the encode fails - which is what a phone short of memory
// does with a 12 megapixel canvas. Before: no prompt, no message, no file.
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    // stand in for the Android bridge, and record what it is handed
    window.__saved=[];
    window.RealismCam={
      saveImage:(n,m,b)=>window.__saved.push({how:'pics',n,len:b.length}),
      saveImageDl:(n,m,b)=>window.__saved.push({how:'dl',n,len:b.length}),
      saveImageAsk:(n,m,b)=>window.__saved.push({how:'ask',n,len:b.length}),
    };
  });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof compositeCv==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  await pg.evaluate(async ()=>{
    const W=4032,H=3024; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,H);
    gr.addColorStop(0,'#f8e0c0'); gr.addColorStop(1,'#201008'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(x=>c.toBlob(x,'image/jpeg',.95));
    await addRef(new File([b],'p.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(x=>setTimeout(x,50)); }
    $('unit').value='cm'; $('widthIn').value='40'; $('heightIn').value='30'; $('fmtGo').click();
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(x=>setTimeout(x,50)); }
    GRID_ON=true; GRID_COL='auto';
  });
  await pg.waitForTimeout(8000);
  const run = async (label, sabotage) => {
    const r = await pg.evaluate(async (sab)=>{
      window.__saved=[];
      let toasted=[];
      const ot=window.toast; window.toast=function(t,...a){ toasted.push(String(t)); return ot.apply(this,arguments); };
      const orig=HTMLCanvasElement.prototype.toDataURL;
      if (sab) HTMLCanvasElement.prototype.toDataURL=function(...a){
        // fail on anything big, the way a phone short of memory does
        if (this.width*this.height > sab) throw new Error('out of memory');
        return orig.apply(this,a);
      };
      let prompted=false;
      const p = $('expBtn').onclick();
      // answer the "where to save" question when it appears
      // the real prompt is #dlwModal with #dlwPics / #dlwDl / #dlwPick
      for (let i=0;i<160;i++){
        const m=document.getElementById('dlwModal');
        if (m && m.style.display==='flex'){ prompted=true; document.getElementById('dlwPics').onclick(); break; }
        await new Promise(x=>setTimeout(x,50));
      }
      await p.catch(()=>{});
      await new Promise(x=>setTimeout(x,600));
      HTMLCanvasElement.prototype.toDataURL=orig;
      window.toast=ot;
      return { prompted, saved:window.__saved.slice(), toasted };
    }, sabotage);
    const saved = r.saved.length ? (Math.round(r.saved[0].len/1e6*10)/10)+'MB via '+r.saved[0].how : 'nothing';
    console.log('  '+label.padEnd(34)+'prompted: '+String(r.prompted).padEnd(7)
      +'handed off: '+saved.padEnd(20)+(r.toasted.length?('said: '+r.toasted.join(' / ')):''));
  };
  await run('normal',                     0);

  await run('encode fails over 3MP',      3e6);

  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
