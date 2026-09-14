// Does pressing Done actually apply the edit? edClose() nulls ED.srcImg
// synchronously, and the apply reads it 30ms later.
const { chromium } = require('playwright-core');
const PORT = process.argv[2]||'8899';
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2.625, isMobile:true, hasTouch:true });
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
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.92));
    await addRef(new File([b],'phone.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
  });
  const sample = () => pg.evaluate(()=>{
    const c=document.createElement('canvas'); c.width=8; c.height=8;
    const g=c.getContext('2d',{willReadFrequently:true});
    g.drawImage(photo,0,0,8,8);
    return {dims:photo.width+'x'+photo.height,
            px:[...g.getImageData(0,0,8,8).data].filter((_,i)=>i%4===0).join(',')};
  });
  const before = await sample();
  // the real path: tap Edit, move a slider, tap Done
  await pg.evaluate(()=>$('fmtEdit').click());
  await pg.waitForFunction(()=>ED&&ED.on&&ED.pre,null,{timeout:20000});
  // a GENTLE edit: a blown-out result would also read as "changed"
  await pg.evaluate(()=>{ ED.R.exp=18; edSync(); edRender(); });
  await pg.waitForTimeout(300);
  await pg.evaluate(()=>$('edDone').click());
  await pg.waitForTimeout(2500);
  const after = await sample();
  const screen = await pg.evaluate(()=>document.querySelector('.screen.on')?.id);
  const A=before.px.split(',').map(Number), B=after.px.split(',').map(Number);
  const moved=A.filter((v,i)=>v!==B[i]).length;
  const sat=B.filter(v=>v===255||v===0).length;
  console.log('  before  '+before.dims+'  '+before.px.slice(0,44));
  console.log('  after   '+after.dims+'  '+after.px.slice(0,44));
  console.log('  screen after Done: '+screen);
  console.log('  samples that moved: '+moved+' of '+A.length+'   saturated: '+sat);
  console.log('  '+(moved===0 ? 'FAIL the tone edit was discarded - photo is unchanged'
    : sat>A.length*0.6 ? 'FAIL the result is blown out, not a gentle lift'
    : 'ok the tone edit was applied'));
  // and the crop path, which changes the dimensions
  await pg.evaluate(()=>$('fmtCrop').click());
  await pg.waitForFunction(()=>ED&&ED.on&&ED.pre,null,{timeout:20000});
  await pg.evaluate(()=>{ Object.assign(ED.R,{cx:0.2,cy:0.1,cw:0.5,ch:0.6}); edRender(); });
  await pg.waitForTimeout(300);
  await pg.evaluate(()=>$('edDone').click());
  await pg.waitForTimeout(2500);
  const cropped = await pg.evaluate(()=>photo.width+'x'+photo.height);
  console.log('  after crop: '+cropped+'  '
    +(cropped===after.dims ? 'FAIL the crop was discarded' : 'ok the crop was applied'));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
