// edBuildPre now hands back the preview canvas itself when nothing is turned.
// Every orientation must still work, and must still come out of Done.
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
    // left half black, right half white: orientation is unmistakable
    const W=2400,H=1800; const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    g.fillStyle='#000'; g.fillRect(0,0,W/2,H);
    g.fillStyle='#fff'; g.fillRect(W/2,0,W/2,H);
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.97));
    await addRef(new File([b],'halves.jpg',{type:'image/jpeg'}), false);
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    $('unit').value='cm'; $('widthIn').value='30';
  });
  let bad=0;
  const quads = async () => pg.evaluate(()=>{
    const p=ED.pre, q=p.getContext('2d',{willReadFrequently:true});
    const at=(fx,fy)=>q.getImageData(Math.round(p.width*fx),Math.round(p.height*fy),1,1).data[0];
    return {dims:p.width+'x'+p.height, tl:at(.25,.25), tr:at(.75,.25),
            bl:at(.25,.75), br:at(.75,.75),
            aliased: p===ED.pre};
  });
  await pg.evaluate(()=>$('fmtEdit').click());
  await pg.waitForFunction(()=>ED&&ED.on&&ED.pre,null,{timeout:20000});
  const dark=v=>v<60, light=v=>v>190;
  const cases = [
    ['no turn',      {rot:0,fh:false,fv:false,ang:0}, q=>dark(q.tl)&&dark(q.bl)&&light(q.tr)&&light(q.br)],
    ['rotate 90',    {rot:1,fh:false,fv:false,ang:0}, q=>dark(q.tl)&&dark(q.tr)&&light(q.bl)&&light(q.br)],
    ['rotate 180',   {rot:2,fh:false,fv:false,ang:0}, q=>light(q.tl)&&light(q.bl)&&dark(q.tr)&&dark(q.br)],
    ['rotate 270',   {rot:3,fh:false,fv:false,ang:0}, q=>light(q.tl)&&light(q.tr)&&dark(q.bl)&&dark(q.br)],
    ['flip across',  {rot:0,fh:true,fv:false,ang:0},  q=>light(q.tl)&&light(q.bl)&&dark(q.tr)&&dark(q.br)],
    ['flip down',    {rot:0,fh:false,fv:true,ang:0},  q=>dark(q.tl)&&dark(q.bl)&&light(q.tr)&&light(q.br)],
    ['back to none', {rot:0,fh:false,fv:false,ang:0}, q=>dark(q.tl)&&dark(q.bl)&&light(q.tr)&&light(q.br)],
  ];
  for (const [name,R,ok] of cases){
    await pg.evaluate(R2=>{ Object.assign(ED.R,R2); edBuildPre(); edRender(); }, R);
    await pg.waitForTimeout(220);
    const q=await quads();
    const good=ok(q);
    if(!good) bad++;
    console.log('  '+name.padEnd(14)+q.dims.padEnd(11)
      +'TL '+String(q.tl).padStart(3)+'  TR '+String(q.tr).padStart(3)
      +'  BL '+String(q.bl).padStart(3)+'  BR '+String(q.br).padStart(3)
      +'   '+(good?'ok':'FAIL wrong orientation'));
  }
  // straighten must still produce a different picture. Four quadrant CENTRES
  // cannot see a 5.5 degree tilt on a half-black image - they sit far from
  // the only edge that moves. Signature the whole preview instead.
  const sig = () => pg.evaluate(()=>{
    const p=ED.pre, q=p.getContext('2d',{willReadFrequently:true});
    const d=q.getImageData(0,0,p.width,p.height).data;
    let h=0, n=0;
    for (let i=0;i<d.length;i+=4*29){ h=(h*31 + d[i])|0; n++; }
    return h+'/'+n;
  });
  await pg.evaluate(()=>{ Object.assign(ED.R,{rot:0,fh:false,fv:false,ang:55}); edBuildPre(); edRender(); });
  await pg.waitForTimeout(250);
  const tilted=await sig();
  await pg.evaluate(()=>{ ED.R.ang=0; edBuildPre(); edRender(); });
  await pg.waitForTimeout(250);
  const flat=await sig();
  const straightened = tilted!==flat;
  if(!straightened) bad++;
  console.log('  straighten    '+(straightened?'ok changes the preview':'FAIL straighten did nothing'));
  // and a turn must survive Done
  await pg.evaluate(()=>{ ED.R.rot=1; edBuildPre(); edRender(); });
  await pg.waitForTimeout(220);
  const beforeDims=await pg.evaluate(()=>photo.width+'x'+photo.height);
  await pg.evaluate(()=>$('edDone').click());
  await pg.waitForTimeout(2500);
  const afterDims=await pg.evaluate(()=>photo.width+'x'+photo.height);
  const swapped = beforeDims.split('x')[0]===afterDims.split('x')[1]
               && beforeDims.split('x')[1]===afterDims.split('x')[0];
  if(!swapped) bad++;
  console.log('  Done with a quarter turn: '+beforeDims+' -> '+afterDims+'  '
    +(swapped?'ok the turn was applied':'FAIL the turn did not survive Done'));
  console.log('  '+(bad?('FAIL '+bad+' problems'):'all orientations ok'));
  if (errs.length) console.log('  page errors:', errs.slice(0,3));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
