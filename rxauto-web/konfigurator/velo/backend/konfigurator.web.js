// Konfigurátor pronájmu – backend (Wix Velo web module)
// Soubor v Wixu: backend/konfigurator.web.js
// Přihlašovací údaje do Renteonu jsou ve Wix Secrets Manageru (nikdy v kódu):
//   RENTEON_CZ_USER, RENTEON_CZ_PASSWORD, RENTEON_SK_USER, RENTEON_SK_PASSWORD
import { Permissions, webMethod } from 'wix-web-module';
import { fetch } from 'wix-fetch';
import { getSecret } from 'wix-secrets-backend';
import wixData from 'wix-data';
import { notifications } from 'wix-crm-backend';

const RENTEON = {
  CZ: { base: 'https://rxauto.s3.renteon.com', user: 'RENTEON_CZ_USER', pass: 'RENTEON_CZ_PASSWORD', loginOffice: 25, pricelist: 1850 },
  SK: { base: 'https://cwslovakia.s6.renteon.com', user: 'RENTEON_SK_USER', pass: 'RENTEON_SK_PASSWORD', loginOffice: 128, pricelist: 352 }
};
const POBOCKY = {
  PRG: { nazev: 'Praha', inst: 'CZ', office: 25, pole: 'prg', sipp: 'sippCz' },
  OSR: { nazev: 'Ostrava', inst: 'CZ', office: 26, pole: 'osr', sipp: 'sippCz' },
  BTS: { nazev: 'Bratislava', inst: 'SK', office: 128, pole: 'bts', sipp: 'sippSk' }
};
const OPT = { suppressAuth: true };

// ---------- konfigurace (ceník z CMS) ----------
let cfgCache = null, cfgTime = 0;
async function nactiKonfiguraci() {
  if (cfgCache && Date.now() - cfgTime < 5 * 60 * 1000) return cfgCache;
  const [v, n, s] = await Promise.all([
    wixData.query('KonfiguratorVozy').eq('aktivni', true).ascending('poradi').limit(100).find(OPT),
    wixData.query('KonfiguratorNastaveni').limit(100).find(OPT),
    wixData.query('KonfiguratorSpoluucast').limit(100).find(OPT)
  ]);
  const nastaveni = {};
  n.items.forEach(i => { nastaveni[i.title] = i.hodnotaText ? i.hodnotaText : i.hodnota; });
  const spoluucast = {};
  s.items.forEach(i => { spoluucast[i.title] = { popis: i.popis, priplatek5: num(i.priplatek5), priplatek0: num(i.priplatek0) }; });
  const vozy = v.items.map(i => ({
    id: i._id, title: i.title, znacka: i.znacka, cenaMesic: num(i.cenaMesic), kmVCene: num(i.kmVCene),
    kategorie: i.kategorieSpoluucasti, prg: !!i.prg, osr: !!i.osr, bts: !!i.bts,
    maxMesice: num(i.maxMesice), popisWeb: i.popisWeb || '', servisVCene: i.servisVCene !== false, skupina: i.skupina || 'Osobní auta', modelovyRok: num(i.modelovyRok), neomezenyPriplatek: num(i.neomezenyPriplatek), obrazek: i.obrazek || '', overitelny: !!(i.sippCz || i.sippSk)
  }));
  cfgCache = { vozy, nastaveni, spoluucast, _sipp: Object.fromEntries(v.items.map(i => [i._id, { sippCz: i.sippCz, sippSk: i.sippSk }])) };
  cfgTime = Date.now();
  return cfgCache;
}
function num(x) { return (x === null || x === undefined || x === '') ? null : Number(x); }

export const getKonfigurace = webMethod(Permissions.Anyone, async () => {
  const c = await nactiKonfiguraci();
  return { vozy: c.vozy, nastaveni: c.nastaveni, spoluucast: c.spoluucast };
});

// ---------- výpočet ceny (stejná logika jako v prvku na stránce) ----------
function parseD(s) { const [y, m, d] = String(s).split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)); }
function addMonths(d, m) { const x = new Date(d.getTime()); x.setUTCMonth(x.getUTCMonth() + m); return x; }

function spocitej(cfg, s) {
  const n = cfg.nastaveni, chyby = [], polozky = [];
  const vuz = cfg.vozy.find(v => v.id === s.vuzId);
  if (!vuz) return { chyby: ['Vyberte vůz.'], polozky };
  if (!s.od || !s.do) return { vuz, chyby: ['Zvolte termín pronájmu.'], polozky };
  const od = parseD(s.od), dO = parseD(s.do);
  const dni = Math.round((dO.getTime() - od.getTime()) / 86400000);
  if (dni < n.minDni) chyby.push(`Minimální délka pronájmu je ${n.minDni} dní.`);
  if (vuz.maxMesice && dO > addMonths(od, vuz.maxMesice)) chyby.push(`U tohoto vozu je maximální doba pronájmu ${vuz.maxMesice} měsíců.`);
  const mes = dni / n.dniVMesici;
  if (vuz.cenaMesic === null) return { vuz, dni, mes, chyby, polozky, naDotaz: true };
  let celkem = 0, upresnime = false;
  const add = (label, castka, info) => { polozky.push({ label, castka, info }); if (castka === null) upresnime = true; else celkem += castka; };
  add(`Nájem ${vuz.title} (${fmtN(vuz.cenaMesic)} Kč/měs.)`, vuz.cenaMesic * mes);
  if (s.najezd === 'neomezeny' && vuz.neomezenyPriplatek !== null) {
    add('Neomezený nájezd', vuz.neomezenyPriplatek * mes);
  } else if (vuz.kmVCene !== null) {
    const km = Number(s.najezd) || vuz.kmVCene;
    const kroky = Math.max(0, Math.ceil((km - vuz.kmVCene) / n.krokKm));
    if (kroky > 0) add(`Navýšení nájezdu na ${fmtN(km)} km/měs.`, kroky * n.cenaKrok * mes);
  }
  if (s.druhyRidic) {
    const zdarma = dni >= n.ridicZdarmaOd;
    add('Druhý řidič', zdarma ? 0 : n.ridicDen * dni, zdarma ? 'zdarma u pronájmu nad 30 dní' : `${n.ridicDen} Kč/den`);
  }
  if (s.spoluucast === '5' || s.spoluucast === '0') {
    const sp = cfg.spoluucast[vuz.kategorie] || {};
    const p = s.spoluucast === '5' ? sp.priplatek5 : sp.priplatek0;
    add(s.spoluucast === '5' ? 'Snížená spoluúčast 5 % (min. 5 000 Kč)' : 'Spoluúčast 0 %', p === null || p === undefined ? null : p * mes,
      p === null || p === undefined ? 'příplatek upřesníme v nabídce' : undefined);
  }
  return { vuz, dni, mes, chyby, polozky, celkem: Math.round(celkem), celkemSDph: Math.round(celkem * (1 + n.dph)), upresnime };
}
function fmtN(x) { return new Intl.NumberFormat('cs-CZ').format(Math.round(x)); }

// ---------- Renteon ----------
const tokeny = {};
async function token(inst) {
  const t = tokeny[inst];
  if (t && t.exp > Date.now()) return t.v;
  const r = RENTEON[inst];
  const [u, p] = await Promise.all([getSecret(r.user), getSecret(r.pass)]);
  if (!u || !p) throw new Error('chybí přihlašovací údaje ' + inst);
  const body = `grant_type=password&username=${encodeURIComponent(u)}&password=${encodeURIComponent(p)}&client_id=Inhouse.WebApp&office_id=${r.loginOffice}`;
  const res = await fetch(r.base + '/token', { method: 'post', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
  if (!res.ok) throw new Error('Renteon login ' + inst + ' ' + res.status);
  const j = await res.json();
  tokeny[inst] = { v: j.access_token, exp: Date.now() + Math.min((j.expires_in || 3600) - 120, 3600) * 1000 };
  return j.access_token;
}
function rDate(s) { const [y, m, d] = s.split('-'); return `${d}.${m}.${y}. 10:00`; }

const dostCache = {};
async function dostupnostSipp(kod, sipp, od, dO) {
  const p = POBOCKY[kod], r = RENTEON[p.inst];
  const key = [kod, sipp, od, dO].join('|');
  const c = dostCache[key];
  if (c && Date.now() - c.t < 10 * 60 * 1000) return c.v;
  const tk = await token(p.inst);
  const res = await fetch(r.base + '/api/availability/search/?pageSize=200', {
    method: 'post',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tk },
    body: JSON.stringify({ BookingTypeId: '2', AvailableOnly: false, OfficeOutId: p.office, OfficeInId: p.office, DateTimeOut: rDate(od), DateTimeIn: rDate(dO), PricelistIds: [r.pricelist] })
  });
  if (res.status === 401) { delete tokeny[p.inst]; throw new Error('Renteon 401'); }
  if (!res.ok) throw new Error('Renteon availability ' + res.status);
  const j = await res.json();
  const kat = (j.AvailabilityCarCategories || []).filter(k => k.SIPP === sipp);
  const volno = kat.reduce((a, k) => a + Math.max(0, k.AvailableCount || 0), 0);
  dostCache[key] = { t: Date.now(), v: volno };
  return volno;
}

async function overInterne(vuzId, pobocka, od, dO) {
  const cfg = await nactiKonfiguraci();
  const vuz = cfg.vozy.find(v => v.id === vuzId);
  if (!vuz || !POBOCKY[pobocka]) return { stav: 'chyba', text: 'Neplatný výběr.' };
  const sipp = cfg._sipp[vuzId] || {};
  const nazev = POBOCKY[pobocka].nazev;
  const kodyVozu = Object.keys(POBOCKY).filter(k => vuz[POBOCKY[k].pole]);
  if (!vuz.overitelny) return { stav: 'rucne', text: 'Dostupnost tohoto vozu ověříme ručně a ozveme se vám.' };
  const vysledek = {};
  let chyba = false;
  await Promise.all(kodyVozu.map(async k => {
    const s = sipp[POBOCKY[k].sipp];
    if (!s) return;
    try { vysledek[k] = await dostupnostSipp(k, s, od, dO); } catch (e) { console.error('Renteon', k, e.message); chyba = true; }
  }));
  if (vysledek[pobocka] > 0) return { stav: 'dostupne', text: `Vůz je v termínu dostupný na pobočce ${nazev}.` };
  const jinde = Object.keys(vysledek).filter(k => k !== pobocka && vysledek[k] > 0).map(k => POBOCKY[k].nazev);
  if (jinde.length) return { stav: 'jinde', pobocky: jinde, text: `Na pobočce ${nazev} vůz v termínu volný není, je dostupný na pobočce ${jinde.join(' / ')}. Po dohodě je možné vůz přistavit.` };
  if (chyba && !Object.keys(vysledek).length) return { stav: 'neovereno', text: 'Dostupnost se teď nepodařilo ověřit automaticky – ověříme ji ručně.' };
  return { stav: 'nedostupne', text: 'V tomto termínu vůz bohužel volný není. Pošlete poptávku – nabídneme nejbližší možný termín nebo podobný vůz.' };
}

export const overDostupnost = webMethod(Permissions.Anyone, async (q) => {
  if (!q || !q.vuzId || !q.pobocka || !/^\d{4}-\d{2}-\d{2}$/.test(q.od || '') || !/^\d{4}-\d{2}-\d{2}$/.test(q.do || '')) return { stav: 'chyba', text: 'Doplňte vůz, pobočku a termín.' };
  try { return await overInterne(q.vuzId, q.pobocka, q.od, q.do); }
  catch (e) { console.error(e); return { stav: 'neovereno', text: 'Dostupnost se teď nepodařilo ověřit automaticky – ověříme ji ručně.' }; }
});

// ---------- poptávka ----------
export const odeslatPoptavku = webMethod(Permissions.Anyone, async (p) => {
  p = p || {};
  if (p.web) return { ok: true }; // honeypot
  const str = (x, max) => String(x || '').trim().slice(0, max || 200);
  const jmeno = str(p.jmeno), email = str(p.email), telefon = str(p.telefon, 40);
  if (!jmeno || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || telefon.replace(/\D/g, '').length < 9) return { ok: false, chyba: 'Vyplňte jméno, platný e-mail a telefon.' };
  if (!p.souhlas) return { ok: false, chyba: 'Potvrďte souhlas se zpracováním údajů.' };
  const cfg = await nactiKonfiguraci();
  const v = spocitej(cfg, p);
  if (!v.vuz) return { ok: false, chyba: 'Vyberte vůz.' };
  if (v.chyby && v.chyby.length) return { ok: false, chyba: v.chyby.join(' ') };
  let dost;
  try { dost = await overInterne(p.vuzId, p.pobocka, p.od, p.do); } catch (e) { dost = { stav: 'neovereno', text: 'neověřeno' }; }
  const spText = { '10': '10 % (min. 10 000 Kč)', '5': '5 % (min. 5 000 Kč)', '0': '0 %' }[p.spoluucast] || '10 % (min. 10 000 Kč)';
  const item = {
    title: jmeno, email, telefon, firma: str(p.firma), model: v.vuz.title + (v.vuz.modelovyRok ? ' (' + v.vuz.modelovyRok + ')' : ''),
    pobocka: (POBOCKY[p.pobocka] || {}).nazev || '', od: p.od, do: p.do, dni: v.dni,
    najezd: v.vuz.kmVCene === null || p.najezd === 'neomezeny' ? null : Number(p.najezd) || v.vuz.kmVCene,
    najezdText: v.vuz.kmVCene === null || p.najezd === 'neomezeny' ? 'neomezený' : (Number(p.najezd) || v.vuz.kmVCene) + ' km/měs.', druhyRidic: !!p.druhyRidic, spoluucast: spText,
    cenaBezDph: v.naDotaz ? null : v.celkem,
    dostupnost: `${dost.stav}: ${dost.text}`, poznamka: str(p.poznamka, 2000), stav: 'nová'
  };
  await wixData.insert('Poptavky', item, OPT);
  try {
    await notifications.notify(
      `Nová poptávka z konfigurátoru: ${item.model}, ${item.pobocka}, ${item.od} – ${item.do}, ${item.cenaBezDph ? fmtN(item.cenaBezDph) + ' Kč bez DPH' : 'cena na dotaz'} (${jmeno})`,
      ['Dashboard', 'Mobile', 'Browser'],
      { recipients: { role: 'All_Contributors' }, title: 'Poptávka pronájmu', actionTitle: 'Otevřít poptávky', actionTarget: { url: 'https://manage.wix.com/dashboard/48d34089-c30b-4b3c-ace5-b1fb2a3049a5/database/data/Poptavky' } }
    );
  } catch (e) { console.error('notify', e.message); }
  return { ok: true, dostupnost: dost, cena: item.cenaBezDph };
});
