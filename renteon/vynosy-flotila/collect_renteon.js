// Sběr dat pro přehled výnosů a flotily – spouštět v záložce Renteonu (CZ rxauto.s3 / SK cwslovakia.s6),
// v kontextu stránky (javascript_tool). Nic nezapisuje. Výstupy jsou agregované (bez osobních údajů).
const $http = angular.element(document.body).injector().get('$http');
const p2 = n => String(n).padStart(2, '0');

// 1) Výnosy po měsících a pobočkách (podle data vyúčtování), bez DPH
async function revenue(fromY = 2025, toY = 2026, toM = 12) {
  const out = [];
  for (let y = fromY; y <= toY; y++) for (let m = 1; m <= 12; m++) {
    if (y === toY && m > toM) break;
    const last = new Date(y, m, 0).getDate();
    const r = await $http.get('api/report/GetRealizationByOffice', { params: { DateOfPaymentFrom: `01.${p2(m)}.${y}.`, DateOfPaymentTo: `${last}.${p2(m)}.${y}.` } });
    for (const o of r.data) if (!o.IsTotal) out.push({ mesic: `${y}-${p2(m)}`, pobocka: o.OfficeCode, mena: o.Currency,
      vynos: Math.round(o.TotalAmountNet), najem: Math.round(o.RentAmountNet), pojisteni: Math.round(o.InsuranceAmountNet),
      poplatky: Math.round(o.FeeAmountNet), skody: Math.round(o.DamagesAmountNet), smluv: o.NumberOfContracts, dni: o.Days });
  }
  return out;
}

// 2) Ø počet vozidel po měsících (flotila 7 = Pronájem vozového parku; HG/CC vynechat)
async function fleet(startY = 2025, endY = 2026, endM = 10, carFleetIds = [7]) {
  const r = await $http.post('api/report/getFleetStateByOfficeInPeriod', { startMonth: 1, startYear: startY, endMonth: endM, endYear: endY, carFleetIds });
  return r.data.map(o => [o.Code, o.MonthlyData.map(m => [m.YearMonth, m.AverageCarCount])]);
}

// 3) Pokuty: položky dokladů ServiceTypeId 14 (pokuty/mýtné/parkování) + zpracování
//    CZ: název „Zpracování Dopravního přestupku/pokuty“ (typ 3), SK: „Jemné spracovanie dopravy“ (typ 19).
//    Pobočka = z čísla rezervace (24-PRG-…), doklad bez smlouvy = pobočka dokladu. Datum = datum dokladu.
//    ~10 tis. dokladů CZ ≈ 2 min při 8 paralelních. Běží na pozadí ve window.__FJ.
async function fines(officeIds, from = '01.01.2025.', to = '31.10.2026.') {
  const docs = [];
  for (const off of officeIds) {
    const r = await $http.get('api/financeDocument/getSimpleList', { params: { FinanceDocumentTypeIds: [2, 3, 9, 10, 12], IncludeGroupInvoices: true, IsActive: true, IsCancelled: false,
      OfficeIds: off, DateTimeFinanceDocumentDateFrom: from, DateTimeFinanceDocumentDateTo: to, pageSize: 20000, sortDirection: 'ASC', sortProperty: 'Id' } });
    docs.push(...(r.data.Items || r.data));
  }
  const J = window.__FJ = { total: docs.length, done: 0, err: [], agg: {} }; let i = 0;
  const isProc = n => /(zpracov.*(přestup|pokut))|spracovanie dopravy/i.test(n || '');
  const work = async () => { while (i < docs.length) { const d = docs[i++];
    for (let a = 0; a < 3; a++) { try {
      const x = await $http.get('api/financeDocument/' + d.Id);
      const ym = d.FinanceDocumentDate.slice(6, 10) + '-' + d.FinanceDocumentDate.slice(3, 5);
      const off = (d.BookingNumber || '').match(/-(PRG|OSR|BTS)-/)?.[1] || d.OfficeCode;
      for (const it of x.data.FinanceDocumentItems || []) {
        const k = it.ServiceTypeId === 14 ? 'pokuty' : isProc(it.Translation?.Name) ? 'zprac' : null; if (!k) continue;
        const key = off + '|' + ym; J.agg[key] = J.agg[key] || { pokuty: 0, zprac: 0, n: 0 };
        J.agg[key][k] += it.AmountNetWithDiscountTotalDomestic || 0; if (k === 'pokuty') J.agg[key].n++;
      }
      break; } catch (e) { if (a === 2) J.err.push(d.Id); } }
    J.done++; } };
  J.start = Date.now(); Promise.all([1, 2, 3, 4, 5, 6, 7, 8].map(work)).then(() => { J.finished = Date.now(); });
  return docs.length;
}
// CZ: fines([25, 26])   SK: fines([128])   průběh: window.__FJ.done / total, výsledek: window.__FJ.agg
