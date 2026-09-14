// The editor now cuts from `photo` when the reference carries no stored edit.
// The danger is compounding: open, edit, open again, and the second session
// must still start from the PRISTINE picture, not the edited one.
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
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d'); const gr=g.createLinearGradient(0,0,W,0);
    gr.addColorStop(0,'#202020'); gr.addColorStop(1,'#d8d8d8'); g.fillStyle=gr; g.fillRect(0,0,W,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
    await addRef(new File([b],'ramp.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
  });
  const samp = () => pg.evaluate(()=>{
    const c=document.createElement('canvas'); c.width=c.height=8;
    const q=c.getContext('2d',{willReadFrequently:true});
    q.drawImage(photo,0,0,8,8);
    return [...q.getImageData(0,0,8,8).data].filter((_,i)=>i%4===0);
  });
  const editOnce = async (exp) => {
    await pg.evaluate(()=>$('fmtEdit').click());
    await pg.waitForFunction(()=>ED&&ED.on&&ED.pre,null,{timeout:20000});
    const reused = await pg.evaluate(()=>ED.orig===photo);
    await pg.evaluate(e=>{ ED.R.exp=e; edSync(); edRender(); }, exp);
    await pg.waitForTimeout(250);
    await pg.evaluate(()=>$('edDone').click());
    await pg.waitForTimeout(2500);
    return reused;
  };
  const pristine = await samp();
  const r1 = await editOnce(20);
  const after1 = await samp();
  const r2 = await editOnce(20);          // SAME edit again, from a fresh open
  const after2 = await samp();
  console.log('  first open reused the decoded photo:  '+(r1?'yes':'no (decoded)'));
  console.log('  second open reused the decoded photo: '+(r2?'yes':'no (decoded)')
    +'   <- must be no: a stored edit means photo is not pristine');
  console.log('  pristine  '+pristine.slice(0,8).join(','));
  console.log('  after +20 '+after1.slice(0,8).join(','));
  console.log('  again +20 '+after2.slice(0,8).join(','));
  const moved = pristine.some((v,i)=>v!==after1[i]);
  const same  = after1.every((v,i)=>v===after2[i]);
  console.log('  the edit did something:            '+(moved?'ok':'FAIL nothing changed'));
  console.log('  applying +20 twice == +20 once:    '
    +(same?'ok not compounded':'FAIL the second edit stacked on the first'));
  // and a reset back to neutral must restore the pristine picture
  await pg.evaluate(()=>$('fmtEdit').click());
  await pg.waitForFunction(()=>ED&&ED.on&&ED.pre,null,{timeout:20000});
  await pg.evaluate(()=>{ $('edReset').click(); });
  await pg.waitForTimeout(250);
  await pg.evaluate(()=>$('edDone').click());
  await pg.waitForTimeout(2500);
  const reset = await samp();
  const restored = pristine.every((v,i)=>Math.abs(v-reset[i])<=2);
  console.log('  reset  '+reset.slice(0,8).join(','));
  console.log('  reset restores the original:       '+(restored?'ok':'FAIL reset did not come back'));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
