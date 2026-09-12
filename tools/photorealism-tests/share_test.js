// the four fixes, end to end
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ try{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); }catch(e){} });
  const page = await ctx.newPage();
  const errs=[]; page.on('pageerror',e=>errs.push(String(e)));
  // stand in for the shell's parked bytes
  await page.route('**/__cap/shared1', async route => {
    const png = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAAXklEQVR4nO3QMQEAAAjDMMC/52ECvlRA0zbJzQIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgJ8FDFoAAeJ8kMkAAAAASUVORK5CYII=','base64');
    route.fulfill({ status:200, contentType:'image/png', body:png });
  });
  await page.goto('http://127.0.0.1:8899/index.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>typeof window.__shared==='function');

  // A. a shared image asks B&W or colour, then becomes a reference
  await page.evaluate(()=>window.__shared('/__cap/shared1','image/png','from-chrome.png'));
  await page.waitForFunction(()=>getComputedStyle($('modeModal')).display!=='none',null,{timeout:5000});
  console.log('share -> mode chooser opens: ok');
  await page.evaluate(()=>$('modeC').click());
  await page.waitForFunction(()=>photo&&photo.width,null,{timeout:15000});
  const a = await page.evaluate(async()=>{
    const rs=await galAll(); const r=rs.find(x=>x.name==='from-chrome.png');
    return { stored:!!r, screen:[...document.querySelectorAll('.screen.on')].map(e=>e.id).join(',') };
  });
  console.log('share -> stored as a reference:', a.stored ? 'ok' : 'FAIL', a.screen);

  // B. small-image note fires, and a large one stays quiet
  const b = await page.evaluate(async()=>{
    const mk=async(w,h)=>{ const c=document.createElement('canvas'); c.width=w;c.height=h;
      const g=c.getContext('2d'); g.fillStyle='#777'; g.fillRect(0,0,w,h);
      return new File([await new Promise(r=>c.toBlob(r,'image/jpeg',.8))],w+'.jpg',{type:'image/jpeg'}); };
    await addRef(await mk(736,981), false);
    for(let i=0;i<200;i++){ if(photo&&photo.width===736) break; await new Promise(r=>setTimeout(r,50)); }
    $('widthIn').value='30'; $('unit').value='cm'; fmtPreview();
    const small=$('resNote').classList.contains('on');
    await addRef(await mk(3000,4000), false);
    for(let i=0;i<200;i++){ if(photo&&photo.width===3000) break; await new Promise(r=>setTimeout(r,50)); }
    $('widthIn').value='30'; $('unit').value='cm'; fmtPreview();
    return { small, big:$('resNote').classList.contains('on'), txt:$('resNote').textContent.slice(0,40) };
  });
  console.log('small note on / big note off:', b.small && !b.big ? 'ok' : 'FAIL', JSON.stringify(b));

  // C. a failed save is reported, not swallowed
  const c = await page.evaluate(async()=>{
    const real=window.galAdd; window.galAdd=async()=>{ GAL_ERR='QuotaExceededError'; return null; };
    let said=''; const rt=window.toast; window.toast=(m)=>{ said=String(m); };
    const cv=document.createElement('canvas'); cv.width=cv.height=80;
    cv.getContext('2d').fillStyle='#555'; cv.getContext('2d').fillRect(0,0,80,80);
    const f=new File([await new Promise(r=>cv.toBlob(r,'image/jpeg',.8))],'q.jpg',{type:'image/jpeg'});
    await addRef(f,false);
    window.galAdd=real; window.toast=rt;
    return said;
  });
  console.log('failed save reported:', /storage is full/.test(c) ? 'ok' : 'FAIL', '|', c.slice(0,70));
  console.log('page errors', errs.length, errs.slice(0,2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
