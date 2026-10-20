// Rentalcars.com (www.rentalcars.com, záložka search-results) – pickUpLocation IATA PRG/OSR/BTS, cena vehicle.price.amount (EUR), jen AUTOMATIC jako konkurence
(()=>{ const X=__mk('__RC');
 const f=async(L,p,du)=>{ const a=new Date(p+'T10:00:00'); const dof=new Date(Date.UTC(a.getFullYear(),a.getMonth(),a.getDate()+du)).toISOString().slice(0,10)+'T10:00:00';
  const sc={driversAge:35,dropOffDateTime:dof,dropOffLocation:L,dropOffLocationType:'IATA',pickUpDateTime:p+'T10:00:00',pickUpLocation:L,pickUpLocationType:'IATA'};
  const r=await fetch('/api/search-results?searchCriteria='+encodeURIComponent(JSON.stringify(sc))+'&filterCriteria=%7B%7D&serviceFeatures=%5B%22INCLUDE_NUMBER_OF_SUITCASES%22%5D');
  if(r.status==403||r.status==429) return null; const j=await r.json();
  return (j.matches||[]).map(m=>{ const dp=j.depots[m.route.pickUpDepotId]; const sp=dp&&j.suppliers[dp.supplierId];
    return {sup:sp?sp.name:'?', sipp:m.vehicle.carClass, auto:m.vehicle.transmission=='AUTOMATIC', price:m.vehicle.price.currency=='EUR'?m.vehicle.price.amount:null}; }); };
 X.run(['PRG','OSR','BTS'],f,3,500); return 'started '+X.jobs.length; })()
