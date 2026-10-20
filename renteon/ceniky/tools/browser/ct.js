// CarTrawler (cars.easyjet.com clientID 512111 / cars.wizzair.com 602653) – PRG 487, OSR 4072, BTS 4724; použití: window.__CTID=512111; window.__CTKEY='__CT'
(()=>{ const X=__mk(window.__CTKEY); X.noRetry=['BTS']; const LC={PRG:'487',OSR:'4072',BTS:'4724'};
 const f=async(L,p,du)=>{ const a=new Date(p+'T10:00:00'); const dof=new Date(Date.UTC(a.getFullYear(),a.getMonth(),a.getDate()+du)).toISOString().slice(0,10)+'T10:00:00';
  const loc={"@CodeContext":"CARTRAWLER","@LocationCode":LC[L]};
  const msg={"@xmlns":"http://www.opentravel.org/OTA/2003/05","@Version":"1.005","@Target":"Production","@PrimaryLangID":"EN",
   "POS":{"Source":[{"@ISOCurrency":"EUR","RequestorID":{"@Type":"16","@ID":String(window.__CTID),"@ID_Context":"CARTRAWLER"}}]},
   "VehAvailRQCore":{"@Status":"Available","VehRentalCore":{"@PickUpDateTime":p+'T10:00:00',"@ReturnDateTime":dof,"PickUpLocation":loc,"ReturnLocation":loc},"DriverType":{"@Age":35}},
   "VehAvailRQInfo":{"Customer":{"Primary":{"CitizenCountryName":{"@Code":"CZ"}}}}};
  const r=await fetch('https://otageo.cartrawler.com/cartrawlerota/json?msg='+encodeURIComponent(JSON.stringify(msg))+'&type=OTA_VehAvailRateRQ');
  if(r.status==403||r.status==429) return null; const j=await r.json(); const out=[];
  for(const v of ((j.VehAvailRSCore||{}).VehVendorAvails||[])) for(const a of (v.VehAvails||[])){ const c=a.VehAvailCore; if(c.TotalCharge['@CurrencyCode']!='EUR') continue;
    out.push({sup:v.Vendor['@CompanyShortName'],sipp:c.Vehicle['@Code'],auto:c.Vehicle['@TransmissionType']=='Automatic',price:+c.TotalCharge['@RateTotalAmount']}); }
  return out; };
 X.run(['PRG','OSR','BTS'],f,3,300); return 'started '+X.jobs.length; })()
