// Prodej vozů z operativního leasingu – vlastní prvek (Wix Custom Element, tag rx-prodej)
// Data posílá kód stránky přes atribut "data" (JSON pole z CMS kolekce ProdejLeasing).
const CSS = `
:host{display:block;font-family:'Helvetica Neue',Arial,sans-serif;color:#111;--g:#19a463;--bg:#f4f4f2}
*{box-sizing:border-box}
.wrap{max-width:1180px;margin:0 auto;padding:40px 20px 60px}
h1{font-size:40px;line-height:1.1;margin:0 0 12px;font-weight:800;letter-spacing:-.5px}
.lead{font-size:17px;color:#444;max-width:760px;margin:0 0 28px;line-height:1.5}
.ben{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:0 0 40px}
.b{background:var(--bg);border-radius:14px;padding:16px 16px 16px 50px;position:relative;font-size:15px;line-height:1.4}
.b:before{content:'✓';position:absolute;left:16px;top:14px;width:24px;height:24px;border-radius:50%;background:var(--g);color:#fff;font-weight:800;font-size:14px;display:flex;align-items:center;justify-content:center}
.b b{display:block;margin-bottom:2px}
h2{font-size:26px;margin:0 0 14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}
.chip{border:1px solid #ccc;background:#fff;border-radius:20px;padding:7px 14px;font-size:14px;cursor:pointer}
.chip[aria-pressed=true]{background:#111;color:#fff;border-color:#111}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:16px;overflow:hidden;background:#fff;display:flex;flex-direction:column}
.img{aspect-ratio:16/10;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden}
.img img{width:100%;height:100%;object-fit:cover}
.noimg{color:#aaa;font-size:13px}
.c{padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px;flex:1}
.t{font-weight:700;font-size:16px;line-height:1.3;min-height:42px}
.p{display:flex;flex-wrap:wrap;gap:6px}
.p span{background:var(--bg);border-radius:8px;padding:4px 8px;font-size:12.5px;color:#333}
.pr{font-size:22px;font-weight:800;margin-top:auto}
.pr small{display:block;font-size:12px;font-weight:400;color:#666}
.btn{display:block;text-align:center;background:#111;color:#fff;text-decoration:none;border-radius:24px;padding:11px;font-weight:700;font-size:14px;transition:transform .15s,background .15s}
.btn:hover{background:var(--g);transform:translateY(-1px)}
.note{font-size:13px;color:#666;margin-top:22px}
.empty{padding:30px;background:var(--bg);border-radius:14px;text-align:center;color:#555}
@media(max-width:600px){h1{font-size:30px}.wrap{padding:24px 14px 40px}}
`;
const VYHODY = [
  ['Jeden majitel', 'Vůz od nového provozujeme my – známe celou jeho historii.'],
  ['Pravidelný autorizovaný servis', 'Servis podle předpisů výrobce v autorizovaném servisu.'],
  ['Doložený nájezd', 'Kilometry i servisní historie jsou doložené, žádné stáčení.'],
  ['Nejdřív si ho vyzkoušejte', 'Vůz si můžete pronajmout a vyzkoušet, jak dlouho budete potřebovat.'],
  ['Žádné maskované opravy', 'Neprodáváme „vylepšené“ vozy s opravami, které by navyšovaly cenu.'],
  ['Odpočet DPH', 'Ceny uvádíme bez DPH – plátci DPH si daň mohou odečíst.'],
  ['Férová cena', 'Bez překupníků, prodáváme přímo z naší flotily.'],
  ['Výkup protiúčtem', 'Váš stávající vůz můžeme vykoupit na protiúčet.'],
];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const imgUrl = (v) => {
  const m = String(v || '').match(/^wix:image:\/\/v1\/([^/]+)\//);
  if (m) return `https://static.wixstatic.com/media/${m[1]}/v1/fill/w_640,h_400,al_c,q_85,enc_auto/vuz.webp`;
  return /^https?:/.test(v || '') ? v : '';
};

class RxProdej extends HTMLElement {
  constructor() { super(); this.root = this.attachShadow({ mode: 'open' }); this.cars = []; this.f = 'Vše'; }
  static get observedAttributes() { return ['data']; }
  attributeChangedCallback(n, o, v) { if (n === 'data') { try { this.cars = JSON.parse(v) || []; } catch (e) { this.cars = []; } this.render(); } }
  connectedCallback() { this.render(); }
  render() {
    const brands = ['Vše', ...Array.from(new Set(this.cars.map((c) => c.znacka).filter(Boolean)))];
    const list = this.f === 'Vše' ? this.cars : this.cars.filter((c) => c.znacka === this.f);
    const card = (c) => {
      const u = imgUrl(c.obrazek);
      const props = [c.modelovyRok && `${c.modelovyRok}`, c.najezdKm, c.palivo, c.prevodovka, c.vykon].filter(Boolean);
      const subj = encodeURIComponent(`Zájem o vůz: ${c.title}${c.spz ? ' (' + c.spz + ')' : ''}`);
      const naDotaz = /dotaz/i.test(c.cena || '') || !c.cena;
      return `<div class="card"><div class="img">${u ? `<img src="${esc(u)}" alt="${esc(c.title)}" loading="lazy">` : '<span class="noimg">Foto doplníme</span>'}</div>
        <div class="c"><div class="t">${esc(c.title)}</div><div class="p">${props.map((p) => `<span>${esc(p)}</span>`).join('')}</div>
        <div class="pr">${naDotaz ? 'Cena na dotaz' : esc(String(c.cena).replace(/\s*bez DPH/i, ''))}${naDotaz ? '' : '<small>bez DPH</small>'}</div>
        <a class="btn" href="mailto:info@rxauto.cz?subject=${subj}">Mám zájem</a></div></div>`;
    };
    this.root.innerHTML = `<style>${CSS}</style><div class="wrap">
      <h1>Prodej vozů z operativního leasingu</h1>
      <p class="lead">Vozy z naší vlastní flotily, které po skončení operativního leasingu prodáváme. Žádná překvapení – víme o každém kilometru.</p>
      <div class="ben">${VYHODY.map(([a, b]) => `<div class="b"><b>${esc(a)}</b>${esc(b)}</div>`).join('')}</div>
      <h2>Vozy k prodeji</h2>
      ${brands.length > 2 ? `<div class="chips">${brands.map((b) => `<button class="chip" data-b="${esc(b)}" aria-pressed="${b === this.f}">${esc(b)}</button>`).join('')}</div>` : ''}
      ${list.length ? `<div class="grid">${list.map(card).join('')}</div>` : '<div class="empty">Nabídku právě aktualizujeme. Napište nám na info@rxauto.cz.</div>'}
      <p class="note">Ceny jsou uvedeny bez DPH a mohou se měnit podle aktuálního stavu vozu. Prohlídku i zkušební jízdu domluvíme na info@rxauto.cz.</p>
    </div>`;
    this.root.querySelectorAll('[data-b]').forEach((b) => { b.onclick = () => { this.f = b.dataset.b; this.render(); }; });
  }
}
if (!customElements.get('rx-prodej')) customElements.define('rx-prodej', RxProdej);
