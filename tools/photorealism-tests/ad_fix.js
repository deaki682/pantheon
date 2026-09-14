const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof adPx==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  await pg.evaluate(async ()=>{
    const r=(await galAll()).find(x=>x.blob); openPhoto(r.blob,r.id);
    for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')||document.querySelector('#scrMain.on')) break; await new Promise(r=>setTimeout(r,50)); }
    if (document.querySelector('#scrFormat.on')){ $('unit').value='cm'; $('widthIn').value='30'; $('fmtGo').click(); }
    for (let i=0;i<3000;i++){ if (document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
  });
  for (const h of [76,104,132]){
    const r = await pg.evaluate(async (h)=>{
      window.__adOn(true); if (window.__adH) window.__adH(h);
      await new Promise(r=>setTimeout(r,450));
      const floor=innerHeight-h, out=[];
      for (const id of ['hudWrap','detCorner','gridCorner','underCorner','camCorner']){
        const el=document.getElementById(id); if (!el) continue;
        const b=el.getBoundingClientRect();
        if (b.height && b.bottom>floor+0.5) out.push(id+' +'+Math.round(b.bottom-floor));
      }
      return { floor, under:out };
    }, h);
    console.log('strip '+String(h).padStart(3)+'px  buttons under the ad: '+(r.under.length?r.under.join(', '):'none'),
      r.under.length?'FAIL':'ok');
  }
  const z = await pg.evaluate(async ()=>{ window.__adOn(true); window.__adH(0);
    await new Promise(r=>setTimeout(r,250)); return adPx(); });
  console.log('measured 0 reads back as', z, z===0?'ok':'FAIL');
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
