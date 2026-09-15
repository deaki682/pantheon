// RED FRINGES ON DARK STROKES. Colour mode re-exposes each pixel by the ratio
// of the cooked value to the photo's own - k = v/ph, on all three channels.
// Where ph is tiny and v is not, k is huge, and the channels down there are
// not the stroke's own colour: JPEG stores chroma at half resolution, so a
// black lash carries its neighbour's warm cast. The bias multiplies, red
// reaches 255 first, and the lash paints scarlet.
//
// The test picture is that situation on purpose: thin near-black strokes on
// warm skin, saved as a JPEG so the chroma really is subsampled. What is
// counted is how many pixels the composite paints VIVIDLY RED that are not
// red in the photograph.
const { chromium } = require('playwright-core');
const PORT=process.argv[2]||'8899';
let bad=0; const ok=(c,m)=>{ console.log((c?'  ok   ':'  FAIL ')+m); if(!c) bad++; };
(async () => {
  const br = await chromium.launch(require('./browser.js'));
  const ctx = await br.newContext({ viewport:{width:411,height:891}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  await ctx.addInitScript(()=>{ localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done'); });
  const pg = await ctx.newPage();
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('http://localhost:'+PORT+'/index.html',{waitUntil:'domcontentloaded'});
  await pg.waitForFunction(()=>typeof fmtPreview==='function',null,{timeout:30000});
  await pg.waitForFunction(()=>!document.getElementById('introSplash').classList.contains('on'),null,{timeout:30000});
  const r = await pg.evaluate(async ()=>{
    const W=1600,H=1200;
    const c=document.createElement('canvas'); c.width=W;c.height=H;
    const g=c.getContext('2d');
    g.fillStyle='#c98f77'; g.fillRect(0,0,W,H);          // warm skin
    // thin near-black lashes over it, the shape that fringes
    g.strokeStyle='#0d0c0c'; g.lineCap='round';
    for (let i=0;i<70;i++){
      g.lineWidth = 2 + (i%3);
      g.beginPath();
      const x=40+i*22, y=200+(i%7)*40;
      g.moveTo(x,y); g.quadraticCurveTo(x+18,y+120, x+6,y+300);
      g.stroke();
    }
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));   // 4:2:0 chroma
    await addRef(new File([b],'lash.jpg',{type:'image/jpeg'}), true);   // COLOUR
    for (let i=0;i<400;i++){ if (photo&&photo.width) break; await new Promise(r=>setTimeout(r,50)); }
    show('scrFormat'); await new Promise(r=>setTimeout(r,400));
    $('fmtGo').onclick();
    for (let i=0;i<600;i++){ if ($('scrMain').classList.contains('on')&&GRID_READY) break; await new Promise(r=>setTimeout(r,50)); }
    await new Promise(r=>setTimeout(r,900));
    // THE STATE THAT FRINGES: a detail level below Ultra. At Ultra the cooked
    // value reconstructs the photo's own exactly, so k is 1 and the colour is
    // untouched - nothing to amplify. A coarser plane BLURS, so a black lash
    // is pulled up toward the skin around it while the photo's own value
    // stays black: k reaches 18 on this picture, and 18x a JPEG's borrowed
    // warm cast is a scarlet lash. (This is the level the report came from.)
    LAYERS_C.dk=LAYERS_C.mid=LAYERS_C.lt=LAYERS_C.br=true;
    DETAIL='fine'; ensureDetail('fine');
    for (let i=0;i<300;i++){ if (DET.key===fkey() && DET.lv.fine) break;
      await new Promise(r=>setTimeout(r,50)); }
    COMP.sig=null;
    const cv=compositeColorCv();
    const gg=cv.getContext('2d',{willReadFrequently:true});
    const d=gg.getImageData(0,0,cv.width,cv.height).data;
    // the SOURCE, at the same size, to compare against
    const s=document.createElement('canvas'); s.width=cv.width; s.height=cv.height;
    const sg=s.getContext('2d',{willReadFrequently:true});
    sg.drawImage(state.img,0,0,s.width,s.height);
    const sd=sg.getImageData(0,0,s.width,s.height).data;
    // "vividly red" = red well clear of both other channels. Count only the
    // pixels where the PHOTOGRAPH is not red but the composite is.
    let fringe=0, worst=0, n=0;
    for (let i=0;i<d.length;i+=4){
      n++;
      const dr=d[i], dg=d[i+1], db=d[i+2];
      const sr=sd[i], sg2=sd[i+1], sb=sd[i+2];
      const dLead = dr - Math.max(dg,db);
      const sLead = sr - Math.max(sg2,sb);
      if (dLead>60 && dLead-sLead>45){ fringe++; if (dLead>worst) worst=dLead; }
    }
    return { fringe, worst, n, mode:REFMODE, lvl:DET_SHOWN };
  });
  const ppm = Math.round(1e6*r.fringe/r.n);
  console.log('colour mode '+r.mode+' at detail '+r.lvl
              +'   fringe pixels '+r.fringe+' of '+r.n
              +'  ('+ppm+' ppm)   worst red lead '+r.worst);
  ok(r.mode==='c', 'the picture really is in colour mode');
  ok(r.lvl==='fine', 'at the detail level that lifts the shadows ('+r.lvl+')');
  ok(ppm < 200, 'dark strokes are not painted red ('+ppm+' ppm over the photo)');
  ok(errs.length===0, 'no page errors'+(errs.length?' -> '+errs[0]:''));
  await br.close();
  console.log(bad? '\n'+bad+' FAILED' : '\nno red fringing OK');
  process.exit(bad?1:0);
})();
