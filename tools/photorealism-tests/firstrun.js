// First-run walkthrough with NO stored state: splash, intro pages, every tour
// bubble and coach mark, into a project and back. Reports errors, bubbles that
// leave the viewport, bubbles covering their own lit target, and dead ends.
const { chromium } = require('playwright-core');
// Screenshots land in $FIRSTRUN_OUT, else <os tmpdir>/photorealism-firstrun/.
const fs=require('fs'), os=require('os'), path=require('path');
const OUT=(process.env.FIRSTRUN_OUT || path.join(os.tmpdir(),'photorealism-firstrun')).replace(/\/?$/,'/');
fs.mkdirSync(OUT,{recursive:true});
const ALL=[{tag:'phoneP',w:390,h:844},{tag:'phoneL',w:844,h:390},{tag:'tabL',w:1280,h:800}];
const VIEWS=process.argv[2] ? ALL.filter(v=>v.tag===process.argv[2]) : ALL;
function inter(a,b){ const x=Math.max(0,Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)); const y=Math.max(0,Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)); return x*y; }
async function state(pg){
  return pg.evaluate(()=>{
    const vis=id=>{ const e=document.getElementById(id); if(!e) return false; const cs=getComputedStyle(e); return cs.display!=='none' && cs.visibility!=='hidden' && e.getBoundingClientRect().width>0; };
    const r=id=>{ const b=document.getElementById(id).getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height}; };
    const lit=document.querySelector('.tipLit');
    return { on:[...document.querySelectorAll('.screen.on')].map(e=>e.id).join(','),
      splash: vis('introSplash'), intro: vis('introModal'), introTxt: vis('introModal') ? document.getElementById('introTxt').textContent.slice(0,50) : '',
      bubble: vis('tourBubble'), txt: vis('tourBubble') ? document.getElementById('tourTxt').textContent.slice(0,60) : '',
      bub: vis('tourBubble') ? r('tourBubble') : null, x: vis('tourX') && getComputedStyle(document.getElementById('tourX')).display!=='none',
      lit: lit ? lit.id : null, litR: lit ? (()=>{const b=lit.getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height};})() : null,
      coach: vis('coach'), vw:innerWidth, vh:innerHeight,
      ready: (()=>{ try{return !!GRID_READY}catch(e){return false} })() };
  });
}
async function run(br, v){
  const issues=[], log=[];
  const ctx=await br.newContext({ viewport:{width:v.w,height:v.h}, reducedMotion:'no-preference', deviceScaleFactor:2, isMobile:true, hasTouch:true });
  const pg=await ctx.newPage();
  pg.on('pageerror', e=>issues.push(`PAGEERROR ${e.message}`));
  pg.on('console', m=>{ if (m.type()==='error' && !/ERR_CONNECTION|Failed to load|net::/.test(m.text())) issues.push(`CONSOLE ${m.text().slice(0,160)}`); });
  await pg.goto('http://localhost:8899/index.html');
  await pg.waitForTimeout(600); await pg.screenshot({path:`${OUT}${v.tag}-00-splash.png`});
  await pg.waitForTimeout(3200); await pg.screenshot({path:`${OUT}${v.tag}-01-after-splash.png`});
  let step=0, entered=false, exited=false, guard=0;
  while (guard++<60){
    const s=await state(pg);
    if (s.splash){ await pg.waitForTimeout(800); continue; }
    if (s.intro){
      log.push(`intro: "${s.introTxt}"`);
      await pg.screenshot({path:`${OUT}${v.tag}-${String(++step).padStart(2,'0')}-intro.png`});
      const pr=await pg.evaluate(()=>{ const p=document.getElementById('introPanel').getBoundingClientRect(); return {x:p.x,y:p.y,w:p.width,h:p.height}; });
      if (pr.y<0||pr.x<0||pr.y+pr.h>s.vh+1||pr.x+pr.w>s.vw+1) issues.push(`intro panel off-screen (${Math.round(pr.w)}x${Math.round(pr.h)} in ${s.vw}x${s.vh})`);
      await pg.locator('#introBtn').click(); await pg.waitForTimeout(500); continue;
    }
    if (s.coach){ log.push('coach mark'); await pg.screenshot({path:`${OUT}${v.tag}-${String(++step).padStart(2,'0')}-coach.png`}); await pg.mouse.click(Math.round(s.vw/2), Math.round(s.vh/2)); await pg.waitForTimeout(600); continue; }
    if (s.bubble){
      log.push(`tip${s.lit?' -> '+s.lit:''}: "${s.txt}"`);
      await pg.screenshot({path:`${OUT}${v.tag}-${String(++step).padStart(2,'0')}-tip-${s.lit||'info'}.png`});
      const b=s.bub;
      if (b.x<-1||b.y<-1||b.x+b.w>s.vw+1||b.y+b.h>s.vh+1) issues.push(`bubble off-screen for "${s.txt.slice(0,30)}" (${Math.round(b.x)},${Math.round(b.y)} ${Math.round(b.w)}x${Math.round(b.h)})`);
      if (s.litR && inter(b,s.litR)>4) issues.push(`bubble covers its target ${s.lit} bub=${JSON.stringify(b)} lit=${JSON.stringify(s.litR)} vw=${s.vw}x${s.vh}`);
      const chrome=await pg.evaluate(()=>['backBtn','setBtn','expBtn','hudToggle','detBtn','gridBtn','underBtn','compareBtn'].map(id=>{const e=document.getElementById(id); if(!e||!e.offsetParent) return null; const r=e.getBoundingClientRect(); return {id,x:r.x,y:r.y,w:r.width,h:r.height};}).filter(Boolean));
      for (const c of chrome){ if (c.id!==s.lit && inter(b,c)>4) issues.push(`bubble for "${s.txt.slice(0,25)}" covers ${c.id}`); }
      if (s.lit){
        const el=pg.locator('#'+s.lit);
        if (!(await el.isVisible())) { issues.push(`lit target ${s.lit} not visible`); break; }
        await el.click(); await pg.waitForTimeout(900);
      } else if (s.x){ await pg.locator('#tourX').click(); await pg.waitForTimeout(600); }
      else { issues.push(`bubble with no target and no close: "${s.txt}"`); break; }
      continue;
    }
    // no overlay: drive the flow
    if (s.on==='scrUpload' && !entered){ await pg.locator('.gitem').first().click(); await pg.waitForTimeout(1500); entered=true; continue; }
    if (s.on==='scrFormat'){ await pg.locator('#fmtGo').click(); for (let i=0;i<40;i++){ await pg.waitForTimeout(2000); if ((await state(pg)).ready) break; } await pg.waitForTimeout(800); continue; }
    if (s.on==='scrMain' && !exited){
      // a tour step can wait for a menu to CLOSE (the detail tip follows the
      // layers menu closing): close whatever is open, then re-check
      const open=await pg.evaluate(()=>({ hud:!!document.getElementById('hud').offsetParent, det:!!document.getElementById('detMenu').offsetParent }));
      if (open.hud){ log.push('(close layers)'); await pg.locator('#hudToggle').click(); await pg.waitForTimeout(900); continue; }
      if (open.det){ log.push('(close detail)'); await pg.locator('#detBtn').click(); await pg.waitForTimeout(900); continue; }
      await pg.waitForTimeout(2500);
      if ((await state(pg)).bubble) continue;
      await pg.screenshot({path:`${OUT}${v.tag}-${String(++step).padStart(2,'0')}-draw-idle.png`});
      await pg.locator('#compareBtn').click().catch(()=>{}); await pg.waitForTimeout(1500);
      const c=await state(pg); if (c.on==='scrCompare'){ await pg.screenshot({path:`${OUT}${v.tag}-${String(++step).padStart(2,'0')}-compare.png`}); if (c.bubble||c.coach) continue; await pg.locator('#backBtn').click(); await pg.waitForTimeout(1200); }
      exited=true; continue;
    }
    if (s.on==='scrCompare'){ await pg.locator('#backBtn').click(); await pg.waitForTimeout(1200); continue; }
    break;
  }
  const flags=await pg.evaluate(()=>['intro1','tourMain','tourTools','tourFmt','tourCmp','coachGhost'].map(k=>k+'='+(localStorage.getItem(k)||'-')).join(' '));
  await ctx.close();
  console.log(`== ${v.tag}: ${issues.length?issues.length+' issues':'OK'} | ${log.length} overlays | ${flags}`);
  for (const l of log) console.log('   '+l);
  for (const i of issues) console.log('   !! '+i);
}
(async()=>{ const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'}); for (const v of VIEWS) await run(br,v); await br.close(); })().catch(e=>{console.error(e);process.exit(1)});
