// Vyfakturuj – dlouhodobé pronájmy po měsících a pobočkách. Spouštět v přihlášené záložce app.vyfakturuj.cz.
// Export: Exporty → Export dokladů, JSON, podle DUZP, typy Faktura(1), Daňový doklad(16), Opravný(128), Příjmový(64).
// Malá období vrací JSON rovnou, velká vrací formulář s ID → POST /exporty/hromadny-export/by-vfiids/.
// Výstup je agregovaný (SPZ, částky) – bez osobních údajů neukládat jinam než do data/.
async function vfExport(fromY = 2024, toY = 2026, toM = 12) {
  const p = n => String(n).padStart(2, '0'); const inv = [];
  for (let y = fromY; y <= toY; y++) for (let m = 1; m <= 12; m++) { if (y === toY && m > toM) break;
    const fd = new FormData(); const last = new Date(y, m, 0).getDate();
    fd.append('document_export_filter[dateStart]', `01.${p(m)}.${y}`); fd.append('document_export_filter[dateEnd]', `${last}.${p(m)}.${y}`);
    fd.append('document_export_filter[dateSearchType]', 'taxablePeriod'); fd.append('document_export_filter[exportFileType]', 'json');
    for (const b of [1, 16, 128, 64]) fd.append('document_export_filter[documentBitType][]', b); fd.append('document_export_filter[submit]', '');
    const h = await (await fetch('/exporty/hromadny-export/', { method: 'POST', body: fd, credentials: 'include' })).text(); let a;
    if (h.trim().startsWith('[')) a = JSON.parse(h);
    else { const f = [...new DOMParser().parseFromString(h, 'text/html').forms].find(f => f.querySelector('[name="export-vfiids[vfiids]"]')); if (!f) continue;
      a = await (await fetch('/exporty/hromadny-export/by-vfiids/', { method: 'POST', body: new FormData(f), credentials: 'include' })).json(); }
    for (const x of a) if (!(x.storno && x.storno !== '0')) inv.push({ duzp: x.date_taxable_supply, cust: x.customer_name || `${x.customer_firstname || ''} ${x.customer_lastname || ''}`.trim(),
      items: (x.items || []).map(i => [i.text.replace(/\s+/g, ' ').trim(), +i['domestic-total_without_vat']]) });
  }
  return inv;
}
// Klasifikace položek: pokuty (přestupek/pokuta/admin. poplatek/mýtné), jistina (jistina/jistota/kauce),
// prodej (prodej/kupní/odkup/záloha/komise/odkaz na doklad, VIN bez období), najem (pronájem/období/rozsah dat/MM/RRRR/měs.).
// HAVEX Mobility vynechat. GLOBAL ASSISTANCE = vše nájem (asistenční služby), pobočka OSR.
const SPZ_RE = /\b(\d[A-Z][A-Z0-9])\s?(\d{4})\b|\b(\d[A-Z]{3})\s?(\d{3})\b|\b([A-Z]{2}\d{3}[A-Z]{2})\b/;
function classify(t, cust) { const s = t.toLowerCase();
  if (/global assist/i.test(cust)) return /přestup|pokut|administrativní poplatek/.test(s) ? 'pokuty' : 'najem';
  if (/přestup|pokut|administrativní poplatek|mýtn|parkovn[eé]/.test(s)) return 'pokuty';
  if (/jistin|jistot|kauc|depozit/.test(s)) return 'jistina';
  if (/prodej|kupní|odkup|záloh|komise|uhrazen[áa] (část|záloh)|daňový doklad \d|faktura \d|zálohov/.test(s)) return 'prodej';
  if (/pronáj|rental|nájem|období|\(\s?\d{1,2}\.\s?\d{1,2}\.?\s?-\s?\d{1,2}\.\s?\d{1,2}\.?|\d{1,2}\.\d{1,2}\.\s?-\s?\d{1,2}\.\d{1,2}\.|\d{2}\/20\d{2}|\bměs/.test(s)) return 'najem';
  if (/vin[: ]|tmb[a-z0-9]{14}|wv[a-z0-9]{15}|w[a-z0-9]{16}/.test(s)) return 'prodej';
  return 'ostatni'; }
// Pobočka podle SPZ: v Renteonu CZ api/car/getSimpleList → Id podle SPZ, api/carActivity/getSimpleListForCar (IncludeIdle)
// → dny po měsících podle OfficeOutCode, měsíc = pobočka s nejvíc dny. Položka bez SPZ → nejčastější SPZ daného klienta.
// Auta, která nejsou v Renteonu CZ ani SK → PRG a počítají se do vozidel PRG (distinct SPZ v měsíci).

// ---- Aktualizace 21. 10. 2026: jednotná klasifikace na úrovni dokladu ----
// Firma: přepínání v menu firmy (data-popup="vf.system.changeCompany", data-vfcid: RX Auto s.r.o. 26022, RX Auto SK 53196,
// Carnetto RX 78596). Po exportu vždy přepnout zpět na RX Auto s.r.o. Bratislava = RX Auto SK (vše BTS).
// Typ položky it(t): 'sale' (prodej/kupní/odkup/ojet), jinak 'rent' (pronájem, období, rozsah dat, MM/RRRR, (MM/RR), jistina,
// přestupek/pokuta/mýtné, spoluúčast, nadlimitní km, poškození, parkování, mytí), jinak 'sale' (záloha, (ZF…), daňový doklad,
// komise, VIN), jinak 'other'.
// Doklad = prodej, když: má 'sale' a nemá 'rent' | položka s VIN ≥ 100 000 bez období | nemá 'rent' a položka ≥ 60 000
// (mimo zprostředkování/rebate/úroky/provize/přefakturace). Doklad = pronájem, když má 'rent' (a GLOBAL ASSISTANCE vždy).
// V pronájmových dokladech je položka ≥ 150 000 bez data v závorce a ne jistina = prodej auta (smíšené doklady).
// Výnosy z pronájmu: typy 1, 16, 128, 64; prodeje: jen typy 1 (faktura) a 16 (daňový doklad), auta = unikátní VIN.
