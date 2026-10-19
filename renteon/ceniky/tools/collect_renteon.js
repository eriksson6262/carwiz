(()=>{
const CFG=__CFG; // {c:'CZ',pl:1051,poa:1828,offices:[[25,null],[26,26]]}
const h=angular.element(document.body).injector().get('$http');
const pad=n=>String(n).padStart(2,'0');
const add=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x;};
const iso=d=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
const rd=d=>`${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}.`;
const jobs=[]; for(let d=new Date(2026,9,20); d<=new Date(2027,2,20); d=add(d,1)){const w=d.getDay(); for(const du of (w===5?[3,4,7,10,14,21]:w===1?[3,7,14]:[])) jobs.push([iso(d),du]);}
jobs.push(['2026-12-23',5],['2026-12-28',5]);
const X=window.__RX={c:CFG.c,PL:[],RA:[],RULES:[],FA:{},err:[],done:0,running:true};
(async()=>{
 try{
  const sv=(await h.get('api/service/getSimpleList/',{params:{isActive:true,pricelistId:CFG.pl}})).data;
  const svs=(sv.Items||sv).filter(s=>!('ServiceTypeId' in s)||s.ServiceTypeId==1);
  for(const s of svs){
    const sipp=s.Translation&&s.Translation.NameShort; if(!sipp) continue;
    let d=null; try{ d=(await h.get('api/pricelist/listprices/',{params:{officeId:-1,pricelistId:CFG.pl,serviceId:s.Id,from:'01.01.2026.',to:'31.12.2028.'}})).data;}catch(e){X.err.push(['pl',sipp,String(e.status)]);}
    if(!d||!d.Offices) continue;
    for(const o of d.Offices){ const oid=o.Id??null;
      for(const t of (o.Termins||[])){ const D={}; for(const du of (t.Durations||[])){ const k=du.To?`${du.From}-${du.To}`:`${du.From}-`; D[k]=du.Price?du.Price.Amount:null; }
        X.PL.push({S:sipp,Oid:oid,F:t.DateFrom,T:t.DateTo,D}); } }
  }
  const ru=(await h.get('api/pricingRule/getSimpleList',{params:{isActive:true,pageSize:200}})).data;
  X.RULES=(ru.Items||ru).map(r=>{const o={}; for(const k in r){ if(Array.isArray(r[k])||k=='RowVersion') continue; o[k]=r[k];} return o;});
  const today=new Date(); const ov=`${pad(today.getDate())}.${pad(today.getMonth()+1)}.${today.getFullYear()}. 00:00`;
  for(const [off] of CFG.offices){
    const fa=(await h.get('api/carControl/fleetAvailability',{params:{calculateByBillingCarCategory:false,contentPattern:'Available/Total',includePlannedFleet:false,interval:1440,intervalsNumber:180,officeIds:off,overviewFrom:ov,postponeAvailabilityMinutes:60,useConnectedOffices:false}})).data;
    const m={}; for(const g of (fa.CarCategoryGroups||[])) for(const c of (g.CarCategories||[])){ const nm=c.Name||c.CarCategoryName||c.SIPP; m[nm]={d0:rd(today),T:(c.Records||[]).map(r=>r.Total),B:(c.Records||[]).map(r=>r.BookedCount)}; }
    X.FA[String(off)]=m;
  }
  const q=[]; for(const [off] of CFG.offices) for(const j of jobs) q.push([off,...j]);
  X.total=q.length; let i=0;
  const W=async()=>{ while(i<q.length){ const [off,p,du]=q[i++]; const a=new Date(p+'T12:00:00'), b=add(a,du);
     try{ const r=(await h.post('api/availability/search/?pageSize=200',{BookingTypeId:'2',AvailableOnly:false,OfficeOutId:off,OfficeInId:off,DateTimeOut:rd(a)+' 10:00',DateTimeIn:rd(b)+' 10:00',PricelistIds:[CFG.poa]})).data;
       const m={}; for(const c of (r.AvailabilityCarCategories||[])) if(c.SIPP&&c.Amount!=null) m[c.SIPP]=[c.Amount,c.FleetUtilization];
       X.RA.push({o:off,p,du,m}); }catch(e){X.err.push(['ra',off,p,du,String(e.status)]);}
     X.done++; } };
  await Promise.all([W(),W(),W(),W()]);
 }catch(e){X.err.push(['fatal',String(e&&e.message||e)]);}
 X.running=false;
})();
return 'started';})()
