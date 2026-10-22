// Kanály rezervací – sběr dat z Renteonu (CZ rxauto.s3 / SK cwslovakia.s6).
// Spouštět v přihlášené záložce Renteonu (javascript_tool, kontext stránky). Nic nezapisuje.
// Zdroj: Přehledy → Odbyt → Podrobný přehled rezervace (api/Report/getDetailedBookingOverview, xlsx).
// Excel se parsuje přímo ve stránce (SheetJS) a ven jde jen anonymizovaný řádek na smlouvu:
// žádná jména, čísla smluv, SPZ, poznámky ani platební údaje.
//
// Použití:
//   await RXCH.load();                      // SheetJS
//   RXCH.run('2025-10', '2026-10');         // na pozadí, průběh: window.__CH.done / total
//   RXCH.csv(0, 800)                        // CSV po kusech (hlavička v prvním kusu)
//
// Měsíc = podle DateOut (výdej auta). Rezervace se stahují zvlášť aktivní a zrušené.

window.RXCH = (() => {
  const $http = angular.element(document.body).injector().get('$http');
  const p2 = n => String(n).padStart(2, '0');
  const xl = d => (d == null || d === '' ? null : new Date(Math.round((d - 25569) * 86400000))); // Excel serial → Date (UTC)
  const iso = d => (d ? d.toISOString().slice(0, 10) : '');

  async function load() {
    if (typeof XLSX !== 'undefined') return true;
    await new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js';
      s.onload = res; s.onerror = () => rej('SheetJS se nenačetl');
      document.head.appendChild(s);
    });
    return true;
  }

  function sheet(wb, name) {
    const ws = wb.Sheets[name]; if (!ws) return [];
    const rows = XLSX.utils.sheet_to_json(ws, { header: 1 });
    const hi = rows.findIndex(r => r && r.length > 5 && (r.includes('Smlouva ID') || r.includes('Zmluva ID')));
    if (hi < 0) return [];
    const h = rows[hi];
    return rows.slice(hi + 1).filter(r => r && r.length > 3).map(r => { const o = Object.fromEntries(h.map((k, i) => [k, r[i]])); o.ID = o['Smlouva ID'] ?? o['Zmluva ID']; return o; });
  }

  // Kategorie položky smlouvy (podle ServiceTypeName / ServiceName)
  function cat(it) {
    const t = it.ServiceTypeName || '', n = it.ServiceName || '', g = it.ServiceGroupName || '';
    if (/^Půjčení auta|^Požičovňa áut/.test(t) || /Pronájem vozu|Požičanie auta/.test(g)) return 'najem';
    if (/^Pojištění|^Poistenie/.test(t)) return /Základní pojištění|^CDW/i.test(n) ? 'poj_zakl' : 'poj_upsell';
    if (/Poškození|Poškodenie/.test(t) || /Poškození|Škody/.test(g)) return 'skody';
    if (/přestup|pokut|Provoz v pořádku|dopravn|Premávka v poriadku|dopravných lístkov|spracovanie dopravy/i.test(t + n)) return 'pokuty';
    if (/Další vybavení|Dodatočné vybavenie/.test(t)) return /dálniční|diaľničn|Vignette/i.test(n) ? 'znamka' : /Additional driver/i.test(n) ? 'ridic' : 'vybaveni';
    if (/Výjezd do zahraničí|Cross border/i.test(n)) return 'zahranici';
    if (/Další řidič|Ďalší vodič/i.test(t)) return 'ridic';
    if (/Mimo otevírací|Mimo hodín/i.test(t)) return 'mimo_hodiny';
    if (/Jednosměrný|Jednosmern/i.test(t)) return 'oneway';
    if (/Ujeté kilometry|Najazdené kilometre/i.test(t)) return 'km';
    if (/Palivo|tankovania/i.test(t)) return 'palivo';
    if (/řidič|vodič/i.test(t)) return 'vek_ridice';
    return 'ostatni';
  }
  const CATS = ['najem', 'poj_zakl', 'poj_upsell', 'vybaveni', 'znamka', 'zahranici', 'ridic', 'mimo_hodiny', 'oneway', 'km', 'palivo', 'vek_ridice', 'skody', 'pokuty', 'ostatni'];

  async function month(y, m, cancelled) {
    const last = new Date(y, m, 0).getDate();
    const r = await $http({
      method: 'GET', url: '/api/Report/getDetailedBookingOverview', headers: { Accept: 'application/ms-excel' }, responseType: 'arraybuffer',
      params: { IsActive: true, IsCancelled: cancelled, ClientData: false, DriverData: false, CarData: false, ItemData: !cancelled, AmountData: !cancelled,
        CarActivityData: false, OtherData: true, DateTimeOutFrom: `01.${p2(m)}.${y}.`, DateTimeOutTo: `${last}.${p2(m)}.${y}.` }
    });
    const wb = XLSX.read(new Uint8Array(r.data), { type: 'array' });
    const B = sheet(wb, 'Základní data').concat(sheet(wb, 'Základné údaje'));
    const A = {}; for (const x of sheet(wb, 'Množství').concat(sheet(wb, 'Suma'))) A[x.ID] = x;
    const O = {}; for (const x of sheet(wb, 'další').concat(sheet(wb, 'Iné'))) O[x.ID] = x;
    const I = {};
    for (const it of sheet(wb, 'Položky')) {
      const id = it.ID, c = cat(it); const k = (I[id] = I[id] || { pult: 0 });
      const v = +it.AmountNetWithDiscountDomestic || 0;
      k[c] = (k[c] || 0) + v;
      // doprodej na přepážce: položka přidaná až po rezervaci (ne nájem, škody, pokuty)
      if (it.IsCreatedOnReservation === false && !['najem', 'skody', 'pokuty', 'km', 'palivo'].includes(c)) k.pult += v;
    }
    const out = [];
    for (const b of B) {
      if (b.Fleet && !['Pronájem vozového parku', 'Vozový park na prenájom'].includes(b.Fleet)) continue; // HG, CC apod.
      const id = b.ID, a = A[id] || {}, o = O[id] || {}, it = I[id] || {};
      const dOut = xl(b.DateOut), dOpen = xl(o.InitialBookingDate ?? b.OpenDate);
      const net = a.Total ? (a.Total - (a.TotalVat || 0)) : null;
      const row = {
        mesic: `${y}-${p2(m)}`, zruseno: cancelled ? 1 : 0, typ: b.BookingSubTypeCode || '',
        pob_out: b.OfficeOutCode || '', pob_in: b.OfficeEstimatedInCode || b.OfficeInCode || '',
        kanal: b.BookingChannelName || '', partner: b.PartnerName || (/^Kancelá/.test(b.BookingChannelName || '') ? 'Kancelář' : ''),
        cenik: b.MainPricelistCode || '', sipp: b.BillingCarCategorySIPP || '',
        dni: b.Days ?? '', predstih: dOut && dOpen ? Math.max(0, Math.round((dOut - dOpen) / 86400000)) : '',
        den_tydne: dOut ? dOut.getUTCDay() : '', hod_out: dOut ? dOut.getUTCHours() : '',
        firma: b.IsClientCompany ? 1 : 0, promo: b.PromoCode ? 1 : 0, uzavreno: b.IsClosed ? 1 : 0,
        mena: a.CurrencyCode || '', celkem_net: net != null ? +net.toFixed(2) : '',
        celkem_net_czk: a.TotalDomestic && a.Total ? +(a.TotalDomestic * net / a.Total).toFixed(0) : '',
        sleva: a.TotalDiscount || 0,
        zrus_den: b.CancellationDate ? iso(xl(b.CancellationDate)) : '',
      };
      for (const c of CATS) row['k_' + c] = it[c] ? Math.round(it[c]) : 0;
      row.k_pult = Math.round(it.pult || 0);
      out.push(row);
    }
    return out;
  }

  function run(from, to) {
    const [fy, fm] = from.split('-').map(Number), [ty, tm] = to.split('-').map(Number);
    const jobs = []; for (let y = fy, m = fm; y < ty || (y === ty && m <= tm); m === 12 ? (y++, m = 1) : m++) jobs.push([y, m, false], [y, m, true]);
    const X = window.__CH = { total: jobs.length, done: 0, rows: [], err: [], running: true };
    (async () => {
      await load();
      let i = 0;
      const W = async () => { while (i < jobs.length) { const j = jobs[i++];
        for (let a = 0; a < 3; a++) { try { X.rows.push(...await month(...j)); break; } catch (e) { if (a === 2) X.err.push(j.join('-') + ':' + (e.status || e)); } }
        X.done++; } };
      await Promise.all([W(), W()]);
      X.running = false;
    })();
    return jobs.length;
  }

  function csv(from = 0, n = 800) {
    const R = window.__CH.rows; if (!R.length) return '';
    const h = Object.keys(R[0]);
    const esc = v => (v == null ? '' : /[",;\n]/.test(String(v)) ? '"' + String(v).replace(/"/g, '""') + '"' : String(v));
    const body = R.slice(from, from + n).map(r => h.map(k => esc(r[k])).join(','));
    return (from === 0 ? [h.join(',')] : []).concat(body).join('\n');
  }

  return { load, month, run, csv, cat };
})();
'RXCH ready';
