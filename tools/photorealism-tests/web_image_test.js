// what happens to images people DOWNLOAD: transparent PNG, small web jpeg, webp
const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2 });
  await ctx.addInitScript(()=>{ try{ localStorage.setItem('intro1','1'); localStorage.setItem('tour','done'); }catch(e){} });
  const page = await ctx.newPage();
  const errs=[]; page.on('pageerror',e=>errs.push(String(e)));
  await page.goto('http://127.0.0.1:8899/index.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>typeof addRef==='function');

  // 1. a transparent PNG (a cutout, very common as a downloaded reference)
  const png = await page.evaluate(async () => {
    const c=document.createElement('canvas'); c.width=c.height=600;
    const g=c.getContext('2d');
    g.fillStyle='#e8c39e'; g.beginPath(); g.arc(300,300,200,0,7); g.fill();  // subject
    // everything outside the circle stays TRANSPARENT
    const blob=await new Promise(r=>c.toBlob(r,'image/png'));
    const f=new File([blob],'cutout.png',{type:'image/png'});
    await addRef(f,true);
    for(let i=0;i<200;i++){ if(photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    const g2=photo.getContext('2d'); const d=g2.getImageData(5,5,1,1).data;   // a corner: was transparent
    const mid=g2.getImageData(photo.width>>1,photo.height>>1,1,1).data;       // the subject
    return { corner:[d[0],d[1],d[2],d[3]], subject:[mid[0],mid[1],mid[2]], w:photo.width };
  });
  console.log('transparent PNG -> corner rgba', png.corner, 'subject', png.subject);
  console.log('  verdict:', png.corner[0]<30 && png.corner[3]>200 ? 'BLACK BACKGROUND (bad)'
    : png.corner[3]<30 ? 'still transparent (becomes black on jpeg save)' : 'filled ok');

  // 2. a small web-sized image: what drawing size does it propose, is there any warning
  const small = await page.evaluate(async () => {
    const c=document.createElement('canvas'); c.width=736; c.height=981;   // classic pinterest
    const g=c.getContext('2d'); g.fillStyle='#888'; g.fillRect(0,0,736,981);
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.8));
    await addRef(new File([blob],'pin.jpg',{type:'image/jpeg'}), false);
    for(let i=0;i<200;i++){ if(photo&&photo.width===736) break; await new Promise(r=>setTimeout(r,50)); }
    return { w:photo.width, h:photo.height,
      warned: !!document.querySelector('.toast, #toast')?.textContent || false,
      screen:[...document.querySelectorAll('.screen.on')].map(e=>e.id).join(',') };
  });
  console.log('736px web image ->', JSON.stringify(small));
  // cook it at 30cm and see the upscale factor
  const up = await page.evaluate(async () => {
    $('widthIn').value='30'; $('unit').value='cm';
    $('fmtGo').click();
    for(let i=0;i<600;i++){ if(document.querySelector('#scrMain.on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,100)); }
    return { world:[WORLD.w,WORLD.h], upscale:+(WORLD.w/736).toFixed(2) };
  });
  console.log('cooked world', up.world, 'upscale x' + up.upscale, up.upscale>1.5?'(soft/blurry)':'');
  console.log('page errors', errs.length, errs.slice(0,2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
