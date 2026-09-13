const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:8899/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof resNoteSync==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  const recs = await pg.evaluate(async ()=>(await galAll()).map(r=>({id:r.id,name:r.name,seed:!!r.seed})));
  console.log('bundled references:', recs.map(r=>r.name||('#'+r.id)).join(', '));
  for (const rec of recs){
    const r = await pg.evaluate(async (id)=>{
      const rr=(await galAll()).find(x=>x.id===id);
      openPhoto(rr.blob, rr.id);
      for (let i=0;i<400;i++){ if (document.querySelector('#scrFormat.on')) break; await new Promise(r=>setTimeout(r,50)); }
      await new Promise(r=>setTimeout(r,300));
      const out=[];
      for (const [w,u] of [[null,null],[30,'cm'],[40,'cm'],[12,'in']]){
        if (w){ $('unit').value=u; $('widthIn').value=String(w); }
        fmtPreview();
        const cr=cropRect();
        out.push({ size:(w?w+u:'default '+$('widthIn').value+$('unit').value),
          photo:[photo.width,photo.height], crop:[cr.w,cr.h],
          ppi:Math.round(cr.w/physWIn()),
          note:$('resNote').classList.contains('on') ? $('resNote').textContent.slice(0,24) : '' });
      }
      show('scrUpload'); await new Promise(r=>setTimeout(r,150));
      return out;
    }, rec.id);
    console.log('\n'+(rec.name||('#'+rec.id))+'  photo '+r[0].photo.join('x'));
    for (const o of r) console.log('   at '+String(o.size).padEnd(12)+' crop '+String(o.crop.join('x')).padEnd(10)
      +' = '+String(o.ppi).padStart(4)+' ppi  '+(o.note?('FLAGGED: "'+o.note+'..."'):'silent'));
  }
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
