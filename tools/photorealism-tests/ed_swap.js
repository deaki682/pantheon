// The preview buffer now outlives the window. It must NEVER be served for a
// different reference, or for the same one after its picture changed.
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
  // two references, unmistakably different: one dark, one light
  const ids = await pg.evaluate(async ()=>{
    const mk=async (shade,name)=>{
      const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
      const g=c.getContext('2d'); g.fillStyle=shade; g.fillRect(0,0,W,H);
      g.fillStyle='#808080'; g.fillRect(0,0,W,40);
      const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
      await addRef(new File([b],name,{type:'image/jpeg'}), false);
      for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
      return galActive;
    };
    const a=await mk('#141414','dark.jpg');
    const b=await mk('#ededed','light.jpg');
    return {a,b};
  });
  const openAndRead = async () => pg.evaluate(async ()=>{
    $('unit').value='cm'; $('widthIn').value='30';
    await edOpenFor('tone');
    for (let i=0;i<200;i++){ if (ED&&ED.on&&ED.pre) break; await new Promise(r=>setTimeout(r,25)); }
    const p=ED.pre, q=p.getContext('2d',{willReadFrequently:true});
    const v=q.getImageData(Math.round(p.width/2), Math.round(p.height*0.6),1,1).data[0];
    edClose(false);
    return v;
  });
  const openRef = async (id) => pg.evaluate(async (gid)=>{
    photo=null;
    const rec=await galGet(gid);
    openPhoto(rec.blob, gid);            // the real open path
    for (let i=0;i<600;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,25)); }
    return photo ? photo.width+'x'+photo.height : 'none';
  }, id);
  let bad=0;
  await openRef(ids.b); const light1 = await openAndRead();
  await openRef(ids.a); const dark1  = await openAndRead();
  await openRef(ids.b); const light2 = await openAndRead();
  await openRef(ids.a); const dark2  = await openAndRead();
  console.log('  light reference, first open:  '+light1);
  console.log('  dark reference,  first open:  '+dark1);
  console.log('  back to light:                '+light2);
  console.log('  back to dark:                 '+dark2);
  const ok1 = light1>180 && light2>180, ok2 = dark1<80 && dark2<80;
  if(!ok1||!ok2) bad++;
  console.log('  each reference shows its own picture: '
    +(ok1&&ok2 ? 'ok' : 'FAIL a cached preview leaked between references'));
  // and the same reference after its picture changed
  await openRef(ids.b);
  const before = await pg.evaluate(async ()=>{
    await edOpenFor('tone');
    for (let i=0;i<200;i++){ if (ED&&ED.on&&ED.pre) break; await new Promise(r=>setTimeout(r,25)); }
    ED.R.exp=-40; edSync(); edRender();
    await new Promise(r=>setTimeout(r,200));
    $('edDone').click();
    await new Promise(r=>setTimeout(r,2500));
    return true;
  });
  // After an edit the editor is SUPPOSED to show the pristine picture again,
  // with the saved adjustment carried in ED.R and applied at render - that is
  // what stops a second edit compounding on the first. So check the rendered
  // canvas and the stored setting, not the preview buffer.
  const after = await pg.evaluate(async ()=>{
    const shot=()=>{ const c=document.createElement('canvas'); c.width=c.height=8;
      const q=c.getContext('2d',{willReadFrequently:true});
      q.drawImage(photo,0,0,8,8); return q.getImageData(4,5,1,1).data[0]; };
    const photoNow=shot();
    await edOpenFor('tone');
    for (let i=0;i<200;i++){ if (ED&&ED.on&&ED.pre) break; await new Promise(r=>setTimeout(r,25)); }
    const p=ED.pre, q=p.getContext('2d',{willReadFrequently:true});
    const pre=q.getImageData(Math.round(p.width/2), Math.round(p.height*0.6),1,1).data[0];
    edRender();
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    const cv=$('edCv'), cq=cv.getContext('2d',{willReadFrequently:true});
    const shown=cq.getImageData(Math.round(cv.width/2), Math.round(cv.height/2),1,1).data[0];
    const exp=ED.R.exp;
    edClose(false);
    return {photoNow, pre, shown, exp};
  });
  const bakedIn  = after.photoNow < light1-15;      // Done darkened the picture
  const pristine = after.pre > light1-15;           // the buffer is the ORIGINAL
  const carried  = after.exp === -40;               // the setting came back
  const rendered = after.shown < after.pre-10;      // and is applied on screen
  if(!(bakedIn&&pristine&&carried&&rendered)) bad++;
  console.log('  Done darkened the picture:                 '+after.photoNow
    +'  '+(bakedIn?'ok':'FAIL'));
  console.log('  reopening starts from the ORIGINAL buffer: '+after.pre
    +'  '+(pristine?'ok not compounded':'FAIL it started from the edited one'));
  console.log('  the saved adjustment came back: exp='+after.exp
    +'  '+(carried?'ok':'FAIL'));
  console.log('  and is applied on screen:                  '+after.shown
    +'  '+(rendered?'ok':'FAIL the adjustment was not rendered'));
  console.log('  '+(bad?('FAIL '+bad+' problems'):'the cache never served a wrong picture'));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
