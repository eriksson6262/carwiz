// DiscoverCars (www.discovercars.com) – PRG 1620, BTS 1719, OSR 1700, ceny v EUR (&currency=EUR)
(()=>{ const X=__mk('__DC'); const LID={PRG:1620,BTS:1719,OSR:1700};
 const f=async(L,p,du)=>{ const a=new Date(p+'T10:00:00'), b=new Date(a); b.setDate(b.getDate()+du); const ds=d=>d.toISOString().slice(0,10)+'T10:00:00';
  const q={PickupLocationId:LID[L],DropOffLocationId:LID[L],PickupDateTime:p+'T10:00:00',DropOffDateTime:new Date(Date.UTC(a.getFullYear(),a.getMonth(),a.getDate()+du)).toISOString().slice(0,10)+'T10:00:00',ResidenceCountry:'CZ',DriverAge:35,Hash:''};
  const r=await fetch(`/api/v2/search/${crypto.randomUUID()}?sq=${btoa(JSON.stringify(q))}&searchVersion=2&currency=EUR`);
  if(r.status==403||r.status==429) return null; const j=await r.json();
  return ((j.data&&j.data.offers)||[]).map(o=>({sup:o.supplier.name,sipp:o.vehicle.sipp,auto:!!(o.vehicle.specifications&&o.vehicle.specifications.isAutomaticTransmission),price:o.price.raw})); };
 X.run(['PRG','OSR','BTS'],f,5,300); return 'started '+X.jobs.length; })()
