const fs=require('fs'), vm=require('vm');
const s=fs.readFileSync('/home/user/pantheon/draw/index.html','utf8');
const re=/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g;
let m,i=0,bad=0;
while((m=re.exec(s))){ i++; const src=m[1]; if (!src.trim()) continue;
  try{ new vm.Script(src,{filename:'block'+i}); }
  catch(e){ bad++; console.error('block '+i+': '+e.message); } }
console.log(bad? 'FAIL':'OK', i+' blocks'); process.exit(bad?1:0);
