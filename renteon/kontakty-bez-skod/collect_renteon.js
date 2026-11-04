// Spustit v konzoli přihlášeného Renteonu (CZ rxauto.s3.renteon.com / SK cwslovakia.s6.renteon.com).
// Běží na pozadí ve window.__CX; průběh: __CX.status / __CX.detStatus / __CX.abStatus.
(() => {
const h = angular.element(document.body).injector().get('$http');
const C = window.__CX = {b:[],d:[],tf:[],det:{},ab:{},status:'run',detStatus:'wait',abStatus:'wait'};
const pages = async (base, arr) => { for (let i=1;;i++) { const r = await h.get(base+'&pageSize=200&pageIndex='+i); arr.push(...r.data); if (r.headers('x-has-next-page')!=='true') break; } };
const pool = async (ids, n, fn) => { let i=0; await Promise.all(Array.from({length:n}, async () => { while (i<ids.length) { const id=ids[i++]; for (let t=0;t<3;t++) { try { await fn(id); break; } catch(e) {} } } })); };
(async () => {
  await pages('api/booking/getSimpleSearchList?IsActive=true&sortDirection=DESC&sortProperty=Id', C.b);
  await pages('api/damage/getSimpleList?isActive=true&sortDirection=DESC&sortProperty=Id', C.d);
  await pages('api/trafficFine?IsActive=true&sortDirection=DESC&sortProperty=Id', C.tf);
  C.status='done';
  // uzavřené smlouvy -> detail (služby škoda: ServiceTypeId 16 "Poškození", 5 "Zpracování poškození")
  const ids = C.b.filter(x=>x.BookingTypeCode==='C'&&x.IsClosed&&!x.IsCancelled).map(x=>x.Id);
  C.detStatus='run';
  await pool(ids, 6, async id => { const r=(await h.get('api/booking/'+id)).data; let dmg=0;
    (r.Services||[]).forEach(s=>{ if (s.IsSelected&&(s.ServiceTypeId===16||s.ServiceTypeId===5)) (s.ServicePrices||[]).forEach(p=>dmg+=(p.AmountTotal||0)); });
    C.det[id]={n:r.Number,cid:r.ClientId,cn:r.ClientName,em:r.ClientEmail,ph:r.ClientPhone,dr:(r.Booking_Drivers||[]).map(d=>[d.AddressBookId,d.Email,d.Phone]),dmg,dd:r.DamageAmount}; });
  C.detStatus='done';
  // adresář (e-mail, telefon, zaměstnanec/agentura/anonymizace)
  const abIds=[...new Set(Object.values(C.det).flatMap(d=>[d.cid,...d.dr.map(x=>x[0])]).filter(Boolean))];
  C.abStatus='run';
  await pool(abIds, 6, async id => { const a=(await h.get('api/addressBook/'+id)).data;
    C.ab[id]={fn:a.FullName,em:a.Email,ph:a.Phone||(a.AddressBookPhones||[]).map(p=>p.Number).filter(Boolean)[0]||null,emp:a.IsEmployee,agc:a.IsAgency,anon:a.IsAnonymized,noSurvey:a.SurveyDoNotEmail,bl:a.IsOnBlackList}; });
  C.abStatus='done';
})();
})();
