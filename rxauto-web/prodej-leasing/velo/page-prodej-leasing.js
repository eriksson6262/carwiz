// Prodej vozů z operativního leasingu – kód stránky (Wix page code)
// Na stránce je vlastní prvek (Custom Element, tag rx-prodej) s ID #rxProdej.
// Vozy se berou z CMS kolekce ProdejLeasing (zobrazitNaWebu = true, řazení podle pole poradi).
import wixData from 'wix-data';

$w.onReady(async function () {
  const el = $w('#rxProdej');
  let items = [];
  try {
    const r = await wixData.query('ProdejLeasing').eq('zobrazitNaWebu', true).ascending('poradi').limit(100).find();
    items = r.items.map((i) => ({
      title: i.title, znacka: i.znacka, obrazek: i.obrazek, modelovyRok: i.modelovyRok, najezdKm: i.najezdKm,
      palivo: i.palivo, prevodovka: i.prevodovka, vykon: i.vykon, cena: i.cena, spz: i.spz,
    }));
  } catch (e) { items = []; }
  el.setAttribute('data', JSON.stringify(items));
});
