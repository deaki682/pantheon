// IndexedDB's real quota semantics: the REQUEST succeeds and hands back a key,
// then the TRANSACTION aborts. Simulated exactly, so the helpers' handling is
// what is under test.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof galAdd==='function',null,{timeout:25000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:25000});
  console.log(await pg.evaluate(async ()=>{
    // arm: every write request reports success, then its transaction aborts
    const realAdd=IDBObjectStore.prototype.add, realPut=IDBObjectStore.prototype.put;
    const arm=(fn)=>function(...a){
      const req=fn.apply(this,a); const tx=this.transaction;
      setTimeout(()=>{ try{ tx.abort(); }catch(e){} }, 0);
      Object.defineProperty(tx,'error',{value:{name:'QuotaExceededError'},configurable:true});
      return req;
    };
    IDBObjectStore.prototype.add=arm(realAdd); IDBObjectStore.prototype.put=arm(realPut);
    const c=document.createElement('canvas'); c.width=c.height=200;
    c.getContext('2d').fillStyle='#888'; c.getContext('2d').fillRect(0,0,200,200);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));
    const out={};
    const n0=(await galAll()).length;
    out.galAddReturned = await galAdd({ ts:Date.now(), name:'q.jpg', thumb:'', blob });
    out.errAfterAdd = GAL_ERR;
    out.galPutReturned = await galPut({ id:987654, ts:Date.now(), name:'p', blob }, true);
    let said=''; const rt=window.toast; window.toast=(m)=>{ said=String(m); };
    await addRef(new File([blob],'front.jpg',{type:'image/jpeg'}), false);
    window.toast=rt;
    out.addRefToast=said.slice(0,72);
    IDBObjectStore.prototype.add=realAdd; IDBObjectStore.prototype.put=realPut;
    const recs=await galAll();
    out.storedAnything = recs.some(r=>['q.jpg','front.jpg','p'].includes(r.name));
    out.countUnchanged = recs.length===n0;
    return out;
  }));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
