const { chromium } = require('playwright-core');
(async () => {
  const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await br.newContext({ viewport:{width:390,height:844}, deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg = await ctx.newPage();
  pg.on('pageerror', e => console.log('PAGEERROR', e.message));
  await pg.addInitScript(() => {
    for (const k of ['tourMain','tourMainC','tourTools','tourFmt','tourCmp']) localStorage.setItem(k,'done');
    localStorage.setItem('intro1','1'); localStorage.setItem('lang','en');
    for (const k of ['coachGhost','coachCmp','coachFlip']) localStorage.setItem(k,'1');
  });
  await pg.goto('http://localhost:8899/index.html', { waitUntil:'domcontentloaded' });
  await pg.waitForFunction(() => typeof cmpSetPhoto === 'function' && typeof galAdd === 'function');
  await pg.waitForTimeout(1500);

  const R = await pg.evaluate(async () => {
    const out = {};
    const isGrey = (cv) => {
      const g = cv.getContext('2d', {willReadFrequently:true});
      const d = g.getImageData(0,0,Math.min(40,cv.width),Math.min(40,cv.height)).data;
      for (let i=0;i<d.length;i+=4)
        if (Math.abs(d[i]-d[i+1])>6 || Math.abs(d[i+1]-d[i+2])>6) return false;
      return true;
    };
    // a vividly coloured reference and a vividly coloured "drawing photo"
    const mk = async (fill) => { const c=document.createElement('canvas');
      c.width=600; c.height=400; const g=c.getContext('2d');
      g.fillStyle=fill; g.fillRect(0,0,600,400);
      return await new Promise(r=>c.toBlob(r,'image/jpeg',0.95)); };
    const refBlob = await mk('#d81b60');

    const id = await galAdd({ ts:Date.now(), name:'colour ref',
      thumb: await thumbOf(refBlob, true), blob: refBlob });
    localStorage.setItem('mode|'+id, 'c');          // a COLOUR project
    out.isColorSaysYes = isColor(id);

    galActive = id;
    REFMODE = isColor(id) ? 'c' : 'bw';
    out.refModeAtOpen = REFMODE;

    // now the capture path the app uses for a picked/native photo
    const shot = await mk('#1e88e5');
    await cmpSetPhoto(shot);
    out.refModeAfterSetPhoto = REFMODE;
    out.rawIsGrey = CMP.raw ? isGrey(CMP.raw) : 'no raw';

    // and what actually gets stored
    CKEY = 'TEST|c';
    cmpSaveNow();
    await new Promise(r=>setTimeout(r,150));
    const saved = await dbGet('cmp|TEST|c');
    if (saved && saved.blob) {
      const im = await blobImage(saved.blob);
      const c2 = document.createElement('canvas');
      c2.width=im.width; c2.height=im.height;
      c2.getContext('2d').drawImage(im,0,0);
      out.storedIsGrey = isGrey(c2);
    } else out.storedIsGrey = 'nothing saved';

    // and what the flip view paints
    try { CMP.mode='flip'; CMP.showing='photo'; cmpRender();
      const cv = document.getElementById('cmpCv');
      out.renderedIsGrey = cv && cv.width ? isGrey(cv) : 'no canvas';
    } catch(e) { out.renderedIsGrey = 'threw: ' + e.message; }
    out.bodyHasColorRef = document.body.classList.contains('colorRef');
    return out;
  });
  console.log(JSON.stringify(R, null, 2));
  await br.close();
})().catch(e=>{console.error(e);process.exit(1)});
