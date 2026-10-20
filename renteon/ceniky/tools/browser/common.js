// Společné pro sběr konkurence v prohlížeči (20.10.2026). Výstup window[KEY] = {tag:2, sup:[], res:[[L,p,du,cw,comp]], done,total,err,running}
window.__mk=function(KEY){
 const pad=n=>String(n).padStart(2,'0'), add=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x;};
 const iso=d=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
 const jobs=[]; const T0=new Date(); T0.setHours(0,0,0,0);
 for(let d=add(T0,1); d<=add(T0,151); d=add(d,1)){const w=d.getDay(); for(const du of (w===5?[3,4,7,10,14,21]:w===1?[3,7,14]:[])) jobs.push([iso(d),du]);}
 jobs.push(['2026-12-23',5],['2026-12-28',5]);
 const X=window[KEY]={tag:2,sup:[],res:[],done:0,total:0,err:[],running:true,jobs,noRetry:[]};
 X.sid=n=>{let i=X.sup.indexOf(n); if(i<0){X.sup.push(n); i=X.sup.length-1;} return i;};
 X.grp=s=>{ if(!s||s.length<3) return null; if(s[1]=='V') return 'VANA'; const l=s[0];
   if('PUG'.includes(l)) return 'PREM'; if('ECIFS'.includes(l)) return l; return null; };
 // offers: [{sup, sipp, auto, price}] -> push compressed record
 X.add=(L,p,du,offers)=>{ const cw={}, pools={};
   for(const o of offers){ if(!o.sipp||!(o.price>0)) continue; const s=o.sipp.toUpperCase();
     if(/carwiz/i.test(o.sup)){ if(!(s in cw)||o.price<cw[s]) cw[s]=Math.round(o.price*100)/100; continue; }
     if(!o.auto) continue; const g=X.grp(s); if(!g) continue; (pools[g]=pools[g]||[]).push([o.price,o.sup,s]); }
   const comp={}; for(const g in pools){ const a=pools[g].sort((x,y)=>x[0]-y[0]); const seen=new Set(), out=[];
     for(const x of a){ if(seen.has(x[1])) continue; seen.add(x[1]); out.push([Math.round(x[0]*100)/100,X.sid(x[1]),x[2]]); if(out.length>=6) break; } comp[g]=out; }
   X.res.push([L,p,du,cw,comp]); };
 X.run=async(locs,fetchOne,par,pause)=>{ const q=[]; for(const L of locs) for(const j of jobs) q.push([L,...j]); X.total=q.length; let i=0;
   const W=async()=>{ while(i<q.length && !X.stop){ const [L,p,du]=q[i++]; let ok=false;
     for(let t=0;t<3 && !ok;t++){ try{ const offers=await fetchOne(L,p,du); if(offers===null){X.stop='blocked';break;}
         if(offers.some(o=>/carwiz/i.test(o.sup))||t==2||X.noRetry.includes(L)){ X.add(L,p,du,offers); ok=true; } }catch(e){ if(t==2) X.err.push([L,p,du,String(e&&e.message||e).slice(0,80)]); }
       await new Promise(r=>setTimeout(r,pause)); }
     X.done++; } };
   await Promise.all(Array.from({length:par},W)); X.running=false; };
 X.dump=async(part,size)=>{ const txt=JSON.stringify({tag:2,sup:X.sup,res:X.res});
   const cs=new Blob([txt]).stream().pipeThrough(new CompressionStream('gzip')); const buf=new Uint8Array(await new Response(cs).arrayBuffer());
   let b=''; for(let k=0;k<buf.length;k+=8192) b+=String.fromCharCode.apply(null,buf.subarray(k,k+8192)); const b64=btoa(b);
   size=size||150000; const n=Math.ceil(b64.length/size); return `${KEY}P${part}/${n}#`+b64.slice((part-1)*size,part*size)+'#END'; };
 return X; };
'ok'
