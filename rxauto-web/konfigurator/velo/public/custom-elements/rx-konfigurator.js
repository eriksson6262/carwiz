// Konfigurátor pronájmu – vlastní prvek <rx-konfigurator> (Wix Custom Element, Velo soubor)
// Soubor v Wixu: public/custom-elements/rx-konfigurator.js
// Komunikace se stránkou:
//   atributy  config (JSON ceníku), availability (JSON výsledku ověření), result (JSON odeslání)
//   události  check {vuzId,pobocka,od,do,reqId}, submit {…celá konfigurace + kontakt}
const POBOCKY = [['PRG', 'Praha'], ['OSR', 'Ostrava'], ['BTS', 'Bratislava']];
const POLE = { PRG: 'prg', OSR: 'osr', BTS: 'bts' };

const CSS = `
:host{display:block;font-family:raleway,'Raleway','Helvetica Neue',Arial,sans-serif;color:#111;--line:#e3e3e3;--soft:#f6f6f4;--mute:#6b6b6b;--ok:#1f7a3f;--warn:#9a6a00;--bad:#a12a2a}
*{box-sizing:border-box}
.hero{max-width:1180px;margin:0 auto;padding:28px 16px 0}
.hero h1{font-size:34px;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin:0 0 8px}
.hero p{font-size:16px;color:var(--mute);margin:0;max-width:720px;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:8px 16px 32px;display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:32px;align-items:start}
h2{font-size:15px;letter-spacing:3px;text-transform:uppercase;font-weight:600;margin:28px 0 12px}
h2 .n{display:inline-block;width:24px;height:24px;border-radius:50%;background:#111;color:#fff;font-size:12px;line-height:24px;text-align:center;letter-spacing:0;margin-right:10px}
.cars{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}
.car{border:1px solid var(--line);border-radius:10px;background:#fff;padding:8px 10px 10px;cursor:pointer;text-align:left;font:inherit;color:inherit;transition:border-color .15s,box-shadow .15s}
.car:hover{border-color:#999}
.car[aria-pressed=true]{border-color:#111;box-shadow:0 0 0 1px #111}
.car img{width:100%;aspect-ratio:278/180;object-fit:cover;display:block;border-radius:6px;background:var(--soft)}
.car b{display:block;font-size:14px;margin-top:6px;line-height:1.25}
.car span{display:block;font-size:13px;color:var(--mute);margin-top:2px}
.grp{font-size:12.5px;letter-spacing:2px;text-transform:uppercase;color:var(--mute);margin:18px 0 8px;font-weight:600}
.car i{display:block;font-style:normal;font-size:12px;color:var(--mute);margin-top:2px}
.noimg{width:100%;aspect-ratio:278/180;border-radius:6px;background:var(--soft)}
.row{display:flex;flex-wrap:wrap;gap:8px}
.pill{border:1px solid var(--line);background:#fff;border-radius:999px;padding:9px 16px;font:inherit;font-size:14px;cursor:pointer;color:#111}
.pill:hover{border-color:#999}
.pill[aria-pressed=true]{background:#111;border-color:#111;color:#fff}
.pill small{opacity:.7;margin-left:4px}
.dates{display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:440px}
label.f{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--mute)}
input,textarea{font:inherit;font-size:15px;color:#111;border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fff;width:100%}
input:focus,textarea:focus,button:focus-visible{outline:2px solid #111;outline-offset:1px}
.opt{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--line);border-radius:10px;padding:12px 14px;cursor:pointer;margin-bottom:8px;background:#fff}
.opt[aria-checked=true]{border-color:#111;box-shadow:0 0 0 1px #111}
.opt .dot{flex:0 0 18px;height:18px;border-radius:50%;border:1.5px solid #999;margin-top:1px}
.opt[aria-checked=true] .dot{border:5px solid #111}
.opt .t{flex:1;font-size:14px}
.opt .t small{display:block;color:var(--mute);font-size:12.5px;margin-top:2px}
.opt .p{font-size:14px;font-weight:600;white-space:nowrap}
.hint{font-size:13px;color:var(--mute);margin:8px 0 0}
.incl{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:#333;margin-top:10px}
.incl span:before{content:'✓ ';color:var(--ok);font-weight:700}
.sum{position:sticky;top:90px;border:1px solid var(--line);border-radius:14px;padding:20px;background:var(--soft);margin-top:28px}
.sum h3{margin:0 0 4px;font-size:18px;font-weight:600}
.sum .meta{font-size:13px;color:var(--mute);margin-bottom:12px}
.li{display:flex;justify-content:space-between;gap:12px;font-size:13.5px;padding:6px 0;border-top:1px solid var(--line)}
.li small{display:block;color:var(--mute);font-size:12px}
.tot{display:flex;justify-content:space-between;align-items:baseline;margin-top:10px;padding-top:12px;border-top:2px solid #111}
.tot b{font-size:30px;font-weight:700;letter-spacing:-.5px;white-space:nowrap}
.tot b em{font-style:normal;font-size:15px;font-weight:600}
.tot span small{display:block;font-size:12px;color:var(--mute)}
.cel{display:flex;justify-content:space-between;gap:12px;font-size:13.5px;margin-top:10px;padding-top:8px;border-top:1px solid var(--line)}
.cel small{display:block;color:var(--mute);font-size:12px;text-align:right}
.vat{text-align:right;font-size:13px;color:var(--mute);margin-top:2px}
.mo{text-align:right;font-size:13px;margin-top:2px}
.st{margin-top:14px;border-radius:10px;padding:10px 12px;font-size:13.5px;line-height:1.4;background:#fff;border:1px solid var(--line)}
.st.dostupne{border-color:var(--ok);color:var(--ok)}
.st.jinde,.st.rucne,.st.neovereno{border-color:var(--warn);color:var(--warn)}
.st.nedostupne,.st.chyba,.err{border-color:var(--bad);color:var(--bad)}
.err{font-size:13.5px;margin-top:10px}
.cta{display:block;width:100%;margin-top:14px;background:#111;color:#fff;border:0;border-radius:999px;padding:14px;font:inherit;font-size:15px;font-weight:600;cursor:pointer;letter-spacing:.5px}
.cta:disabled{opacity:.4;cursor:default}
.form{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.form .full{grid-column:1/-1}
.chk{display:flex;gap:10px;align-items:flex-start;font-size:13px;color:#333}
.chk input{width:auto;margin-top:2px}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.done{border:1px solid var(--ok);border-radius:14px;padding:28px;text-align:center;background:#fff}
.done h3{margin:0 0 8px;font-size:22px}
.spin{display:inline-block;width:12px;height:12px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:s .7s linear infinite;vertical-align:-1px;margin-right:6px}
@keyframes s{to{transform:rotate(360deg)}}
.bar{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;background:#111;color:#fff;padding:10px 96px 10px 16px;display:none;align-items:center;gap:14px;box-shadow:0 -4px 16px rgba(0,0,0,.18)}
.bar.on{display:flex}
.bar .bp{display:flex;flex-direction:column;line-height:1.25;min-width:0}
.bar .bp b{font-size:20px;font-weight:700;white-space:nowrap}
.bar .bp small{font-size:12px;opacity:.75;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (max-width:520px){.bar{padding:10px 84px 10px 12px;gap:10px}.bar .nm{display:none}.bar .bp b{font-size:18px}.bar button{padding:9px 14px}.bar .dl{display:none}}
.bar button{margin-left:auto;background:#fff;color:#111;border:0;border-radius:999px;padding:9px 16px;font:inherit;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap}
@media (max-width:900px){.wrap{grid-template-columns:1fr;gap:0}.sum{position:static}}
@media (max-width:520px){.hero{padding:20px 12px 0}.hero h1{font-size:24px}.wrap{padding:4px 12px 24px}.cars{grid-template-columns:1fr 1fr;gap:8px}.car b{font-size:13px}.dates,.form{grid-template-columns:1fr}.tot b{font-size:22px}}
`;

const fmt = n => new Intl.NumberFormat('cs-CZ', { maximumFractionDigits: 0 }).format(Math.round(n)) + ' Kč';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const parseD = s => { const [y, m, d] = String(s).split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)); };
const addMonths = (d, m) => { const x = new Date(d.getTime()); x.setUTCMonth(x.getUTCMonth() + m); return x; };
const iso = d => d.toISOString().slice(0, 10);
const cz = s => { const [y, m, d] = s.split('-'); return `${+d}. ${+m}. ${y}`; };

// Stejná logika jako backend/konfigurator.web.js (backend je rozhodující)
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
  add(`Nájem ${vuz.title}`, vuz.cenaMesic * mes, `${fmt(vuz.cenaMesic)} / měsíc`);
  if (s.najezd === 'neomezeny' && vuz.neomezenyPriplatek != null) {
    add('Neomezený nájezd', vuz.neomezenyPriplatek * mes, `+${fmt(vuz.neomezenyPriplatek)} / měsíc`);
  } else if (vuz.kmVCene !== null) {
    const km = Number(s.najezd) || vuz.kmVCene;
    const kroky = Math.max(0, Math.ceil((km - vuz.kmVCene) / n.krokKm));
    if (kroky > 0) add(`Nájezd ${new Intl.NumberFormat('cs-CZ').format(km)} km/měs.`, kroky * n.cenaKrok * mes, `+${fmt(kroky * n.cenaKrok)} / měsíc`);
  }
  if (s.druhyRidic) {
    const zdarma = dni >= n.ridicZdarmaOd;
    add('Druhý řidič', zdarma ? 0 : n.ridicDen * dni, zdarma ? 'zdarma u pronájmu nad 30 dní' : `${n.ridicDen} Kč / den`);
  }
  if (s.spoluucast === '5' || s.spoluucast === '0') {
    const sp = cfg.spoluucast[vuz.kategorie] || {};
    const p = s.spoluucast === '5' ? sp.priplatek5 : sp.priplatek0;
    const has = p !== null && p !== undefined;
    add(s.spoluucast === '5' ? 'Spoluúčast 5 %' : 'Spoluúčast 0 %', has ? p * mes : null, has ? `+${fmt(p)} / měsíc` : 'příplatek upřesníme v nabídce');
  }
  return { vuz, dni, mes, chyby, polozky, celkem: Math.round(celkem), celkemSDph: Math.round(celkem * (1 + n.dph)), upresnime };
}

class RxKonfigurator extends HTMLElement {
  static get observedAttributes() { return ['config', 'availability', 'result']; }
  constructor() {
    super();
    this.root = this.attachShadow({ mode: 'open' });
    this.cfg = null;
    const zitra = new Date(); zitra.setDate(zitra.getDate() + 1);
    const od = iso(new Date(Date.UTC(zitra.getFullYear(), zitra.getMonth(), zitra.getDate())));
    this.s = { vuzId: null, pobocka: 'PRG', od, do: iso(addMonths(parseD(od), 1)), najezd: null, druhyRidic: false, spoluucast: '10' };
    this.k = { jmeno: '', firma: '', email: '', telefon: '', poznamka: '', souhlas: false, web: '' };
    this.dost = null; this.reqId = 0; this.odesilam = false; this.hotovo = null; this.chybaOdeslani = '';
    this.timer = null;
  }
  disconnectedCallback() { if (this.io) this.io.disconnect(); }
  connectedCallback() {
    if (!document.getElementById('rx-raleway')) {
      const l = document.createElement('link'); l.id = 'rx-raleway'; l.rel = 'stylesheet';
      l.href = 'https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap';
      document.head.appendChild(l);
    }
    this.render();
  }
  attributeChangedCallback(name, _o, val) {
    let d; try { d = JSON.parse(val); } catch (e) { return; }
    if (name === 'config') {
      this.cfg = d;
      if (d.preselect) {
        const p = String(d.preselect).toLowerCase();
        const v = d.vozy.find(x => x.id === d.preselect || x.title.toLowerCase() === p) || d.vozy.find(x => x.title.toLowerCase().includes(p));
        if (v) this.vyberVuz(v.id, false);
      }
      this.render(); this.naplanujOvereni();
    } else if (name === 'availability') {
      if (d.reqId === this.reqId) { this.dost = d; this.renderSum(); }
    } else if (name === 'result') {
      this.odesilam = false;
      if (d.ok) { this.hotovo = d; this.render(); this.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      else { this.chybaOdeslani = d.chyba || 'Odeslání se nepodařilo, zkuste to prosím znovu nebo nám zavolejte.'; this.renderSum(); }
    }
  }
  vuz() { return this.cfg && this.cfg.vozy.find(v => v.id === this.s.vuzId); }
  najezdy() { return String(this.cfg.nastaveni.najezdy || '2500').split(',').map(Number); }
  vyberVuz(id, rerender = true) {
    this.s.vuzId = id;
    const v = this.vuz();
    if (v) {
      if (this.s.najezd === 'neomezeny' && v.neomezenyPriplatek == null) this.s.najezd = null;
      if (v.kmVCene !== null && this.s.najezd !== 'neomezeny' && !this.najezdy().includes(this.s.najezd)) this.s.najezd = v.kmVCene;
      if (!v[POLE[this.s.pobocka]]) { const k = POBOCKY.find(p => v[POLE[p[0]]]); if (k) this.s.pobocka = k[0]; }
      if (v.maxMesice && parseD(this.s.do) > addMonths(parseD(this.s.od), v.maxMesice)) this.s.do = iso(addMonths(parseD(this.s.od), v.maxMesice));
    }
    if (rerender) { this.render(); this.naplanujOvereni(); }
  }
  naplanujOvereni() {
    clearTimeout(this.timer);
    const v = this.vuz(); const r = this.cfg && spocitej(this.cfg, this.s);
    if (!v || !r || r.chyby.length) { this.dost = null; this.renderSum(); return; }
    this.reqId++; this.dost = { stav: 'loading', reqId: this.reqId };
    const detail = { vuzId: this.s.vuzId, pobocka: this.s.pobocka, od: this.s.od, do: this.s.do, reqId: this.reqId };
    this.renderSum();
    this.timer = setTimeout(() => this.dispatchEvent(new CustomEvent('check', { detail })), 500);
  }

  render() {
    if (!this.cfg) { this.root.innerHTML = `<style>${CSS}</style><div class="wrap"><p class="hint"><span class="spin"></span>Načítám nabídku…</p></div>`; return; }
    if (this.hotovo) {
      const d = this.hotovo.dostupnost || {};
      this.root.innerHTML = `<style>${CSS}</style><div class="wrap" style="display:block;max-width:720px"><div class="done">
        <h3>Děkujeme, poptávka je odeslaná</h3>
        <p>Ozveme se vám obvykle do 1 pracovního dne s potvrzením a dalším postupem (ověření klienta, smlouva, předání).</p>
        ${d.text ? `<p class="hint">${esc(d.text)}</p>` : ''}
        <button class="pill" id="znovu" style="margin-top:12px">Nová konfigurace</button></div></div>`;
      this.root.getElementById('znovu').onclick = () => { this.hotovo = null; this.render(); };
      return;
    }
    const v = this.vuz(), n = this.cfg.nastaveni;
    const minOd = (() => { const z = new Date(); z.setDate(z.getDate() + 1); return iso(new Date(Date.UTC(z.getFullYear(), z.getMonth(), z.getDate()))); })();
    const karta = c => `<button class="car" data-car="${esc(c.id)}" aria-pressed="${c.id === this.s.vuzId}">
        ${c.obrazek ? `<img src="${esc(c.obrazek)}" alt="" loading="lazy">` : '<div class="noimg"></div>'}<b>${esc(c.title)}</b>${c.modelovyRok ? `<i>Modelový rok ${c.modelovyRok}</i>` : ''}<span>${c.cenaMesic === null ? 'cena na dotaz' : 'od ' + fmt(c.cenaMesic) + ' / měs.'}</span></button>`;
    const skupiny = [];
    this.cfg.vozy.forEach(c => { const g = c.skupina || 'Osobní auta'; let x = skupiny.find(y => y.g === g); if (!x) { x = { g, v: [] }; skupiny.push(x); } x.v.push(c); });
    const cars = skupiny.map(x => (skupiny.length > 1 ? `<div class="grp">${esc(x.g)}</div>` : '') + `<div class="cars">${x.v.map(karta).join('')}</div>`).join('');
    const pob = POBOCKY.map(([k, nz]) => `<button class="pill" data-pob="${k}" aria-pressed="${this.s.pobocka === k}">${nz}${v && !v[POLE[k]] ? '<small>· přistavení</small>' : ''}</button>`).join('');
    let najezd = '';
    if (v && v.kmVCene === null) najezd = `<p class="hint">U vozu ${esc(v.title)} je nájezd neomezený.</p>`;
    else {
      const base = v ? v.kmVCene : n.kmVCene;
      najezd = `<div class="row">${this.najezdy().map(km => {
        const k = Math.max(0, Math.ceil((km - base) / n.krokKm));
        return `<button class="pill" data-km="${km}" aria-pressed="${(this.s.najezd || base) === km}">${new Intl.NumberFormat('cs-CZ').format(km)} km${k ? `<small>+${fmt(k * n.cenaKrok)}</small>` : '<small>v ceně</small>'}</button>`;
      }).join('')}${v && v.neomezenyPriplatek != null ? `<button class="pill" data-km="neomezeny" aria-pressed="${this.s.najezd === 'neomezeny'}">Neomezeně<small>+${fmt(v.neomezenyPriplatek)}</small></button>` : ''}</div><p class="hint">Měsíčně v ceně ${new Intl.NumberFormat('cs-CZ').format(base)} km, každých dalších ${new Intl.NumberFormat('cs-CZ').format(n.krokKm)} km za ${fmt(n.cenaKrok)} / měsíc bez DPH.</p>`;
    }
    const sp = v ? (this.cfg.spoluucast[v.kategorie] || {}) : {};
    const spOpt = [['10', 'Spoluúčast 10 %, min. 10 000 Kč', 'standard', 'v ceně'], ['5', 'Spoluúčast 5 %, min. 5 000 Kč', 'snížená', sp.priplatek5 != null ? '+' + fmt(sp.priplatek5) + ' / měs.' : 'příplatek dle vozu'], ['0', 'Spoluúčast 0 %', 'bez spoluúčasti', sp.priplatek0 != null ? '+' + fmt(sp.priplatek0) + ' / měs.' : 'příplatek dle vozu']]
      .map(([k, t, s2, p]) => `<div class="opt" role="radio" tabindex="0" data-sp="${k}" aria-checked="${this.s.spoluucast === k}"><span class="dot"></span><span class="t">${t}<small>${s2}</small></span><span class="p">${p}</span></div>`).join('');
    const ridicInfo = (() => { const r = spocitej(this.cfg, this.s); return r.dni >= n.ridicZdarmaOd ? 'zdarma (pronájem nad 30 dní)' : `${n.ridicDen} Kč / den, u pronájmu nad 30 dní zdarma`; })();

    this.root.innerHTML = `<style>${CSS}</style><div class="hero"><h1>Konfigurátor pronájmu</h1><p>Vyberte vůz, pobočku, termín a nájezd. Cenu spočítáme hned a dostupnost ověříme v našem rezervačním systému. Pošlete nezávaznou poptávku, po ověření klienta vám potvrdíme rezervaci.</p></div><div class="wrap"><div>
      <h2><span class="n">1</span>Vůz</h2>${cars}
      ${v && (v.popisWeb || v.modelovyRok) ? `<p class="hint">${v.modelovyRok ? `Modelový rok ${v.modelovyRok}. ` : ''}${esc(v.popisWeb || '')}</p>` : ''}
      <h2><span class="n">2</span>Pobočka a termín</h2>
      <div class="row">${pob}</div>
      <div class="dates" style="margin-top:12px">
        <label class="f">Převzetí<input type="date" id="od" min="${minOd}" value="${this.s.od}"></label>
        <label class="f">Vrácení<input type="date" id="do" min="${this.s.od}" value="${this.s.do}"></label>
      </div>
      <div class="row" style="margin-top:10px">${[1, 2, 3, 6, 12].filter(m => v ? (!v.maxMesice || m <= v.maxMesice) : m <= 6).map(m => `<button class="pill" data-mes="${m}">${m} ${m === 1 ? 'měsíc' : m < 5 ? 'měsíce' : 'měsíců'}</button>`).join('')}</div>
      <p class="hint">Minimální doba pronájmu ${n.minDni} dní${v && v.maxMesice ? `, u vozu ${esc(v.title)} maximálně ${v.maxMesice} měsíců` : (v ? ', bez omezení maximální doby' : '')}.</p>
      <h2><span class="n">3</span>Nájezd</h2>${najezd}
      <h2><span class="n">4</span>Služby</h2>
      <div class="opt" role="checkbox" tabindex="0" id="ridic" aria-checked="${this.s.druhyRidic}" style="margin-bottom:14px"><span class="dot" style="border-radius:4px"></span><span class="t">Druhý řidič<small>${ridicInfo}</small></span></div>
      ${spOpt}
      <div class="incl"><span>Povinné ručení a havarijní pojištění</span><span>Asistence 24/7</span><span>Pojištění skel</span><span>Sezónní pneumatiky</span>${!v || v.servisVCene ? '<span>Pravidelný servis</span>' : ''}<span>Dálniční známka</span></div>
      <h2><span class="n">5</span>Kontakt</h2>
      <div class="form">
        <label class="f">Jméno a příjmení *<input id="jmeno" autocomplete="name" value="${esc(this.k.jmeno)}"></label>
        <label class="f">Firma / IČO<input id="firma" autocomplete="organization" value="${esc(this.k.firma)}"></label>
        <label class="f">E-mail *<input id="email" type="email" autocomplete="email" value="${esc(this.k.email)}"></label>
        <label class="f">Telefon *<input id="telefon" type="tel" autocomplete="tel" value="${esc(this.k.telefon)}"></label>
        <label class="f full">Poznámka<textarea id="poznamka" rows="3" placeholder="např. přistavení na adresu, čas převzetí, další požadavky">${esc(this.k.poznamka)}</textarea></label>
        <label class="hp">Web<input id="web" tabindex="-1" autocomplete="off"></label>
        <label class="chk full"><input type="checkbox" id="souhlas" ${this.k.souhlas ? 'checked' : ''}>Souhlasím se zpracováním osobních údajů za účelem vyřízení poptávky a ověření klienta.</label>
      </div>
      </div><aside class="sum" id="sum"></aside></div><div class="bar" id="bar"></div>`;
    this.sledujSouhrn();
    this.bind();
    this.renderSum();
  }

  renderSum() {
    const el = this.root.getElementById && this.root.getElementById('sum');
    if (!el || !this.cfg) return;
    const r = spocitej(this.cfg, this.s), v = r.vuz;
    let h = '';
    if (!v) h = `<h3>Vaše konfigurace</h3><p class="meta">Začněte výběrem vozu.</p>`;
    else {
      const pob = POBOCKY.find(p => p[0] === this.s.pobocka)[1];
      h = `<h3>${esc(v.title)}${v.modelovyRok ? ` <small style="font-weight:400;color:var(--mute);font-size:13px">${v.modelovyRok}</small>` : ''}</h3><p class="meta">${esc(pob)} · ${cz(this.s.od)} – ${cz(this.s.do)}${r.dni ? ` · ${r.dni} dní` : ''}</p>`;
      if (r.chyby.length) h += r.chyby.map(c => `<p class="err">${esc(c)}</p>`).join('');
      else if (r.naDotaz) h += `<div class="li"><span>Cena</span><span>na dotaz</span></div><p class="hint">Cenu vám pošleme v nabídce.</p>`;
      else {
        const mesicne = r.dni >= this.cfg.nastaveni.dniVMesici;
        const del = mesicne ? r.mes : 1;
        h += `<p class="meta" style="margin:0 0 4px">${mesicne ? 'Měsíčně' : `Za ${r.dni} dní`}</p>`;
        h += r.polozky.map(p => { const info = mesicne && /\/ měsíc$/.test(p.info || '') ? '' : p.info; return `<div class="li"><span>${esc(p.label)}${info ? `<small>${esc(info)}</small>` : ''}</span><span>${p.castka === null ? '—' : fmt(p.castka / del)}</span></div>`; }).join('');
        if (mesicne) h += `<div class="tot"><span>Cena za měsíc<small>bez DPH</small></span><b>${fmt(r.celkem / r.mes)}</b></div>
          <div class="vat">${fmt(r.celkemSDph / r.mes)} / měsíc s DPH</div>`;
        else h += `<div class="tot"><span>Cena za den<small>bez DPH</small></span><b>${fmt(r.celkem / r.dni)}</b></div>
          <div class="vat">${fmt(r.celkemSDph / r.dni)} / den s DPH</div>
          <div class="cel"><span>Celkem za ${r.dni} dní</span><span>${fmt(r.celkem)} bez DPH<small>${fmt(r.celkemSDph)} s DPH</small></span></div>`;
        h += `${r.upresnime ? '<p class="hint">Příplatek za sníženou spoluúčast upřesníme v nabídce.</p>' : ''}`;
      }
      const d = this.dost;
      if (d && d.stav === 'loading') h += `<div class="st"><span class="spin"></span>Ověřuji dostupnost v termínu…</div>`;
      else if (d && d.text) h += `<div class="st ${esc(d.stav)}">${esc(d.text)}</div>`;
      if (!v[POLE[this.s.pobocka]]) {
        const doma = POBOCKY.filter(p => v[POLE[p[0]]]).map(p => p[1]).join(' / ');
        if (!d || d.stav !== 'jinde') h += `<div class="st jinde">Vůz je k dispozici na pobočce ${esc(doma)}. Po dohodě je možné jej přistavit na pobočku ${esc(pob)}.</div>`;
      }
    }
    if (this.chybaOdeslani) h += `<p class="err">${esc(this.chybaOdeslani)}</p>`;
    const lze = v && !r.chyby.length && !this.odesilam;
    h += `<button class="cta" id="odeslat" ${lze ? '' : 'disabled'}>${this.odesilam ? '<span class="spin"></span>Odesílám…' : 'Odeslat nezávaznou poptávku'}</button>
      <p class="hint">Poptávka je nezávazná. Po ověření klienta vám pošleme potvrzení a smlouvu. Ceny v Kč.</p>`;
    el.innerHTML = h;
    this.renderBar(r);
    const b = this.root.getElementById('odeslat');
    if (b) b.onclick = () => this.odeslat();
  }

  sledujSouhrn() {
    if (this.io) this.io.disconnect();
    const sum = this.root.getElementById('sum');
    if (!sum || !('IntersectionObserver' in window)) return;
    this.io = new IntersectionObserver(en => { this.sumVidet = en[0].isIntersecting; this.renderBar(); }, { threshold: 0.15 });
    this.io.observe(sum);
  }

  renderBar(r) {
    const bar = this.root.getElementById && this.root.getElementById('bar');
    if (!bar || !this.cfg) return;
    r = r || spocitej(this.cfg, this.s);
    if (!r.vuz || this.sumVidet) { bar.classList.remove('on'); return; }
    let t;
    if (r.chyby.length) t = `<div class="bp"><b style="font-size:15px">${esc(r.vuz.title)}</b><small>${esc(r.chyby[0])}</small></div>`;
    else if (r.naDotaz) t = `<div class="bp"><b>Cena na dotaz</b><small>${esc(r.vuz.title)} · ${r.dni} dní</small></div>`;
    else if (r.dni >= this.cfg.nastaveni.dniVMesici) t = `<div class="bp"><b>${fmt(r.celkem / r.mes)} <span style="font-size:13px;font-weight:400">/ měsíc bez DPH</span></b><small><span class="nm">${esc(r.vuz.title)} · </span>${r.dni} dní</small></div>`;
    else t = `<div class="bp"><b>${fmt(r.celkem / r.dni)} <span style="font-size:13px;font-weight:400">/ den bez DPH</span></b><small><span class="nm">${esc(r.vuz.title)} · </span>celkem ${fmt(r.celkem)} za ${r.dni} dní</small></div>`;
    bar.innerHTML = t + '<button type="button" id="kSouhrnu">Souhrn<span class="dl"> a poptávka</span></button>';
    bar.classList.add('on');
    this.root.getElementById('kSouhrnu').onclick = () => this.root.getElementById('sum').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  bind() {
    const $ = id => this.root.getElementById(id);
    this.root.querySelectorAll('[data-car]').forEach(b => b.onclick = () => this.vyberVuz(b.dataset.car));
    this.root.querySelectorAll('[data-pob]').forEach(b => b.onclick = () => { this.s.pobocka = b.dataset.pob; this.render(); this.naplanujOvereni(); });
    this.root.querySelectorAll('[data-km]').forEach(b => b.onclick = () => { this.s.najezd = b.dataset.km === 'neomezeny' ? 'neomezeny' : Number(b.dataset.km); this.render(); });
    this.root.querySelectorAll('[data-mes]').forEach(b => b.onclick = () => { this.s.do = iso(addMonths(parseD(this.s.od), Number(b.dataset.mes))); this.render(); this.naplanujOvereni(); });
    const radio = el => { this.s.spoluucast = el.dataset.sp; this.render(); };
    this.root.querySelectorAll('[data-sp]').forEach(el => { el.onclick = () => radio(el); el.onkeydown = e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); radio(el); } }; });
    const r = $('ridic'); const tog = () => { this.s.druhyRidic = !this.s.druhyRidic; this.render(); };
    r.onclick = tog; r.onkeydown = e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); tog(); } };
    $('od').onchange = e => {
      if (!e.target.value) return;
      const delka = Math.round((parseD(this.s.do).getTime() - parseD(this.s.od).getTime()) / 86400000);
      this.s.od = e.target.value;
      const novy = new Date(parseD(this.s.od).getTime() + Math.max(delka, this.cfg.nastaveni.minDni) * 86400000);
      this.s.do = iso(novy); this.render(); this.naplanujOvereni();
    };
    $('do').onchange = e => { if (!e.target.value) return; this.s.do = e.target.value; this.render(); this.naplanujOvereni(); };
    ['jmeno', 'firma', 'email', 'telefon', 'poznamka', 'web'].forEach(id => $(id).oninput = e => { this.k[id] = e.target.value; });
    $('souhlas').onchange = e => { this.k.souhlas = e.target.checked; };
  }

  odeslat() {
    const k = this.k;
    if (!k.jmeno.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(k.email.trim()) || k.telefon.replace(/\D/g, '').length < 9) {
      this.chybaOdeslani = 'Vyplňte prosím jméno, platný e-mail a telefon (sekce 5 Kontakt).'; this.renderSum(); return;
    }
    if (!k.souhlas) { this.chybaOdeslani = 'Potvrďte prosím souhlas se zpracováním osobních údajů.'; this.renderSum(); return; }
    this.chybaOdeslani = ''; this.odesilam = true; this.renderSum();
    this.dispatchEvent(new CustomEvent('submit', { detail: { ...this.s, ...k } }));
  }
}
if (!customElements.get('rx-konfigurator')) customElements.define('rx-konfigurator', RxKonfigurator);
// Editor Wixu občas neuloží vlastní název tagu – registrujeme i výchozí tag prvku.
if (!customElements.get('wix-default-custom-element')) customElements.define('wix-default-custom-element', class extends RxKonfigurator {});
