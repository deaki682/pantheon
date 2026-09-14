const fs=require('fs'), zlib=require('zlib');
// minimal PNG reader (RGBA, 8-bit, non-interlaced) - enough for our own shots
function readPNG(f){
  const b=fs.readFileSync(f); let p=8, w=0,h=0, idat=[], ct=6;
  while(p<b.length){ const len=b.readUInt32BE(p); const t=b.toString('ascii',p+4,p+8);
    if(t==='IHDR'){ w=b.readUInt32BE(p+8); h=b.readUInt32BE(p+12); ct=b[p+17]; }
    if(t==='IDAT') idat.push(b.slice(p+8,p+8+len));
    p+=12+len; }
  const raw=zlib.inflateSync(Buffer.concat(idat));
  const ch = ct===6?4:(ct===2?3:1);
  const out=Buffer.alloc(w*h*ch); const stride=w*ch;
  let o=0, ro=0;
  for(let y=0;y<h;y++){
    const ft=raw[ro++]; const line=raw.slice(ro,ro+stride); ro+=stride;
    for(let x=0;x<stride;x++){
      const a=x>=ch?out[o+x-ch]:0, bb=y>0?out[o-stride+x]:0, c=(x>=ch&&y>0)?out[o-stride+x-ch]:0;
      let v=line[x];
      if(ft===1)v+=a; else if(ft===2)v+=bb; else if(ft===3)v+=(a+bb)>>1;
      else if(ft===4){const pa=Math.abs(bb-c),pb=Math.abs(a-c),pc=Math.abs(a+bb-2*c);
        v+= (pa<=pb&&pa<=pc)?a:(pb<=pc?bb:c);}
      out[o+x]=v&255;
    }
    o+=stride;
  }
  return {w,h,ch,d:out};
}
const files=fs.readdirSync('.').filter(f=>f.startsWith('look_base_')).sort();
console.log('  case                                 maxdiff   pixels>8   mean');
for(const f of files){
  const g=f.replace('look_base_','look_now_');
  if(!fs.existsSync(g)){ console.log('  MISSING '+g); continue; }
  const A=readPNG(f), B=readPNG(g);
  if(A.w!==B.w||A.h!==B.h){ console.log('  SIZE MISMATCH '+f); continue; }
  let max=0, over=0, sum=0, n=0;
  for(let i=0;i<A.d.length;i+=A.ch){
    for(let k=0;k<3;k++){ const d=Math.abs(A.d[i+k]-B.d[i+k]);
      if(d>max)max=d; if(d>8)over++; sum+=d; n++; }
  }
  const name=f.replace('look_base_','').replace('.png','');
  console.log('  '+name.padEnd(36)+String(max).padStart(6)
    +String(over).padStart(11)+'   '+(sum/n).toFixed(2));
}
