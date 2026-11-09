// Detail auta (Auta (Title), efvqp.js) a karavanu (Karavany (Název), fis3b.js) – stejný kód, liší se KOLEKCE.
// Tlačítko #button2: když je vůz v konfigurátoru (pole konfiguratorVuz v CMS), přejmenuje se na „Spočítej“
// a vede rovnou do konfigurátoru s předvybraným vozem (/konfigurator?vuz=<id z KonfiguratorVozy>). Jinak zůstává „Poptat“.
import wixData from 'wix-data';
import wixLocation from 'wix-location';

const KOLEKCE = 'Auta'; // na detailu karavanu 'Karavany'

async function aktualniPolozka() {
  try {
    const ds = $w('#dynamicDataset');
    await new Promise((res) => ds.onReady(res));
    const it = ds.getCurrentItem();
    if (it) return it;
  } catch (e) { /* dataset se jmenuje jinak – dohledáme podle URL */ }
  const cesta = decodeURIComponent('/' + [wixLocation.prefix, ...wixLocation.path].filter(Boolean).join('/')).toLowerCase();
  const r = await wixData.query(KOLEKCE).limit(100).find();
  return r.items.find((i) => Object.keys(i).some((k) => k.startsWith('link-') && typeof i[k] === 'string' && decodeURIComponent(i[k]).toLowerCase() === cesta)) || null;
}

$w.onReady(async function () {
  const it = await aktualniPolozka();
  if (it && it.konfiguratorVuz) {
    const b = $w('#button2');
    b.label = 'Spočítej';
    b.link = '/konfigurator?vuz=' + encodeURIComponent(it.konfiguratorVuz);
    b.target = '_self';
  }
});
