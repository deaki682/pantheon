const fs=require('fs'),zlib=require('zlib');
function readPNG(f){const b=fs.readFileSync(f);let p=8,w=0,h=0,idat=[],ct=6;
 while(p<b.length){const len=b.readUInt32BE(p),t=b.toString('ascii',p+4,p+8);
  if(t==='IHDR'){w=b.readUInt32BE(p+8);h=b.readUInt32BE(p+12);ct=b[p+17];}
  if(t==='IDAT')idat.push(b.slice(p+8,p+8+len));p+=12+len;}
 const raw=zlib.inflateSync(Buffer.concat(idat)),ch=ct===6?4:(ct===2?3:1);
 const out=Buffer.alloc(w*h*ch),stride=w*ch;let o=0,ro=0;
 for(let y=0;y<h;y++){const ft=raw[ro++],line=raw.slice(ro,ro+stride);ro+=stride;
  for(let x=0;x<stride;x++){const a=x>=ch?out[o+x-ch]:0,bb=y>0?out[o-stride+x]:0,
   c=(x>=ch&&y>0)?out[o-stride+x-ch]:0;let v=line[x];
   if(ft===1)v+=a;else if(ft===2)v+=bb;else if(ft===3)v+=(a+bb)>>1;
   else if(ft===4){const pa=Math.abs(bb-c),pb=Math.abs(a-c),pc=Math.abs(a+bb-2*c);
    v+=(pa<=pb&&pa<=pc)?a:(pb<=pc?bb:c);}out[o+x]=v&255;}o+=stride;}
 return {w,h,ch,d:out};}
let tb=null;const crc=b=>{if(!tb){tb=[];for(let n=0;n<256;n++){let c=n;
 for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;tb[n]=c>>>0;}}
 let c=0xffffffff;for(const x of b)c=tb[(c^x)&255]^(c>>>8);return (c^0xffffffff)>>>0;};
function writePNG(f,w,h,rgba){const stride=w*4,raw=Buffer.alloc((stride+1)*h);
 for(let y=0;y<h;y++){raw[y*(stride+1)]=0;rgba.copy(raw,y*(stride+1)+1,y*stride,(y+1)*stride);}
 const idat=zlib.deflateSync(raw);
 const chunk=(t,d)=>{const b=Buffer.alloc(8+d.length+4);b.writeUInt32BE(d.length,0);
  b.write(t,4);d.copy(b,8);b.writeUInt32BE(crc(Buffer.concat([Buffer.from(t),d])),8+d.length);return b;};
 const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(w,0);ihdr.writeUInt32BE(h,4);ihdr[8]=8;ihdr[9]=6;
 fs.writeFileSync(f,Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),
  chunk('IHDR',ihdr),chunk('IDAT',idat),chunk('IEND',Buffer.alloc(0))]));}
const [fa,fb,out,zs]=process.argv.slice(2);
const z=+(zs||1);
const A=readPNG(fa),B=readPNG(fb);
const gap=16, W=A.w*z*2+gap, H=A.h*z;
const buf=Buffer.alloc(W*H*4,255);
const put=(x,y,r,g,b)=>{const o=(y*W+x)*4;buf[o]=r;buf[o+1]=g;buf[o+2]=b;buf[o+3]=255;};
for(let y=0;y<A.h;y++)for(let x=0;x<A.w;x++){
 const ia=(y*A.w+x)*A.ch, ib=(y*B.w+x)*B.ch;
 for(let dy=0;dy<z;dy++)for(let dx=0;dx<z;dx++){
  put(x*z+dx,y*z+dy,A.d[ia],A.d[ia+1],A.d[ia+2]);
  put(A.w*z+gap+x*z+dx,y*z+dy,B.d[ib],B.d[ib+1],B.d[ib+2]);}}
writePNG(out,W,H,buf);
console.log(out+'  '+W+'x'+H+'   left='+fa+'  right='+fb);
