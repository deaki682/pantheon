// A portrait phone photo is usually a LANDSCAPE jpeg plus an EXIF rotation.
// <img> applies it; createImageBitmap does not unless told to. If the editor
// preview disagreed with the picture, everything downstream would be wrong.
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
  const out = await pg.evaluate(async ()=>{
    // a landscape image whose LEFT half is black and right half white, so a
    // wrong rotation is unmistakable
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    g.fillStyle='#000'; g.fillRect(0,0,W/2,H);
    g.fillStyle='#fff'; g.fillRect(W/2,0,W/2,H);
    const plain=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));
    // splice an EXIF APP1 with Orientation=6 (rotate 90 CW) after SOI
    const bytes=new Uint8Array(await plain.arrayBuffer());
    const be=(n)=>[ (n>>8)&255, n&255 ];
    const be4=(n)=>[ (n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255 ];
    const tiff=[0x4D,0x4D,0x00,0x2A, ...be4(8),        // MM, 42, IFD0 at 8
      ...be(1),                                         // one entry
      ...be(0x0112), ...be(3), ...be4(1), ...be(6), 0,0,// Orientation = 6
      ...be4(0)];                                       // no next IFD
    const app1=[0xFF,0xE1, ...be(2+6+tiff.length),
      0x45,0x78,0x69,0x66,0x00,0x00, ...tiff];
    const outB=new Uint8Array(bytes.length+app1.length);
    outB.set(bytes.slice(0,2),0);
    outB.set(app1,2);
    outB.set(bytes.slice(2), 2+app1.length);
    const blob=new Blob([outB],{type:'image/jpeg'});
    await addRef(new File([blob],'portrait.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
    $('fmtEdit').click();
    for (let i=0;i<400;i++){ if (ED&&ED.on&&ED.pre) break; await new Promise(r=>setTimeout(r,50)); }
    const p=ED.pre, pg2=p.getContext('2d',{willReadFrequently:true});
    const at=(fx,fy)=>pg2.getImageData(Math.round(p.width*fx), Math.round(p.height*fy),1,1).data[0];
    return { photo:photo.width+'x'+photo.height,
             pre:p.width+'x'+p.height,
             usedBitmap: !!ED.srcSmall,
             bm: ED.srcSmall ? ED.srcSmall.width+'x'+ED.srcSmall.height : '-',
             topLeft:at(0.25,0.25), topRight:at(0.75,0.25),
             botLeft:at(0.25,0.75), botRight:at(0.75,0.75) };
  });
  console.log('  photo (via <img>): '+out.photo+'    preview: '+out.pre
    +'    off-thread bitmap: '+(out.usedBitmap?out.bm:'not used'));
  console.log('  preview quadrants  TL '+out.topLeft+'  TR '+out.topRight
    +'   BL '+out.botLeft+'  BR '+out.botRight);
  const portrait = +out.pre.split('x')[0] < +out.pre.split('x')[1];   // NUMBERS: '960'<'1280' is false
  // orientation 6 turns the left-black/right-white landscape into top-black
  const rotated = out.topLeft<60 && out.topRight<60 && out.botLeft>190 && out.botRight>190;
  console.log('  preview is portrait: '+(portrait?'ok':'FAIL it stayed landscape'));
  console.log('  EXIF rotation applied to the preview: '
    +(rotated?'ok (black on top, as <img> renders it)':'FAIL the preview disagrees with the photo'));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
