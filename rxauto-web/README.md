# rxauto-web – web rxauto.cz (Wix)

Wix site „RX AUTO“ (`48d34089-c30b-4b3c-ace5-b1fb2a3049a5`), CMS kolekce:
- `Auta` – nabídka aut k pronájmu, **1 záznam = 1 model** (od 2026-11-04)
- `Karavany`, `Motorky`
- `adi6LightHalfFullTitles*` = odeslané kontaktní formuláře (osobní údaje, neexportovat do repa)

## Pole kolekce Auta
title, znacka, typVozidla, palivo, typPrevodovky, vykonMotoru, objemMotoru, pohon, cena,
msto (text „Praha, Ostrava“), **pobocky** (ARRAY_STRING: Praha/Ostrava/Bratislava), kratkyPopis,
vybava, image, mediagallery, landingPage, zobrazitNaWebu.

## Konsolidace 2026-11-04
`konsolidace_auta.py` – ze zálohy kolekce vybere na model 1 záznam (priorita: zobrazit na webu,
cena, landing page, galerie, nejnovější), sloučí pobočky/palivo/převodovku/výkon a vrátí seznam
duplicit. Výsledek: 131 → 46 modelů, 85 duplicit odebráno přes Wix Data API (bulk patch + bulk remove).
Záloha původních 131 záznamů: `data/auta_backup_2026-11-04.json` (lokálně, mimo git).

## Nabídka z Instagramu (2026-11-05)
Na webu (`zobrazitNaWebu` + `landingPage` = ano) je jen 13 modelů z IG nabídky měsíčního nájmu
(`rxauto-ig/nabidka-mesicni-najem`, CZ ceny Kč/měsíc bez DPH z 27. 10.): Fabia MC 9 900, Kamiq Selection 10 900,
Kamiq MC 11 900, Karoq SL 12 900, Octavia 12 900, Octavia Combi SL 13 900, Superb SL / Superb Combi SL 14 900,
Superb Combi L&K 16 900, Kodiaq SL 16 900, Kodiaq RS 4×4 18 900, Peugeot 3008 na dotaz (neomezený nájezd),
Alfa Tonale PHEV od 19 900. Ostatní modely zůstávají v kolekci, jen skryté.

### Úprava 2026-11-05 (2)
- Fotky: dlaždice 420×349 (Fabia/Kamiq 520×432) s průhledným okrajem – celé auto se vejde do karty 278×231
  (karta má object-fit cover, proto auto max. 86 % šířky / 62 % výšky, střed v 60 % výšky). Ostré, žádný ořez.
  Upload do Wixu jen jako base64 po jednom (shell na Wix nedosáhne); delší base64 (>15 kB) se při přepisu
  rozbíjí → držet webp do ~8 kB (quality 40–50).
- Přidán Mercedes CLE 300 4MATIC (9 990 Kč/týden vč. DPH, týdenní IG nabídka), viditelné i Mercedes Vito,
  BMW X3 (7 990 Kč/týden) a X4 (8 990 Kč/týden) s novými fotkami, BMW X1, 218i, VW Multivan, 2× Peugeot Boxer.
  Celkem 22 viditelných.
- Landing page /dlouhodoby-pronajem („Auta v nabídce“, pole landingPage): jen CLE, Kodiaq RS 4×4, Tonale.
Pozor: výpis /vypis-auta zobrazí max. 12 položek (limit datasetu v editoru) – nutno zvýšit v editoru / tlačítko „Načíst další“.
Karty ve výpisu se po kliknutí neotevřou – opakovač nemá odkaz na dynamickou stránku (link-auta-1-title), oprava jen v editoru.
Wix cache: změny se projeví hned s ?nocache=…, bez parametru až po vypršení cache.

### Úprava 2026-11-05 (3) – landing page = Škodovky z letáků
- landingPage = ano jen u 11 Škod z letáků (Fabia MC, Kamiq Selection, Kamiq MC, Karoq SL, Octavia,
  Octavia Combi SL, Superb SL, Superb Combi SL, Superb Combi L&K, Kodiaq SL, Kodiaq RS 4×4); CLE a Tonale odebrány.
- Opakovač na /dlouhodoby-pronajem má kartu 601×349 → 420px dlaždice byly rozmazané. Nové dlaždice 640×372
  (průhledné, auto max. 88 % viditelné šířky ořezu 278×231 a 60 % výšky, střed v 58 % výšky, webp q50/alpha 40,
  7–9 kB). Stejný soubor slouží i výpisu /vypis-auta (celé auto viditelné). Wix je servíruje v nativních 601 px.
- Upload: UploadImageToWixSite (base64) a **vždy ověřit hash** v prohlížeči na rxauto.cz:
  `fetch(static.wixstatic.com/media/4d8ed0_<id>~mv2.webp)` → SHA-256 + velikost musí sedět s lokálním souborem
  (přepis base64 občas tiše poškodí bajty). Záložní cesta: base64 po 2,5k kouscích do localStorage prohlížeče,
  kontrola hashe, `site-media/v1/files/generate-upload-url` → PUT z prohlížeče.
- Opakovač na landing page zobrazí max. 9 položek (limit datasetu) → Kamiq MC a Fabia MC se teď nezobrazí,
  dokud se v editoru nezvýší počet položek na 12. Tlačítko „Více“ na landing page vede na detail /auta-1/<slug>.
- Detail /auta-1/<slug> nemá v šabloně žádný obrázek (týká se všech aut) – doplnit v editoru prvek obrázku
  navázaný na pole image. Škodovky nemají vyplněné palivo/objem/výkon/pohon (prázdný štítek paliva v kartě).

### Úprava 2026-11-05 (4)
- Detail /auta-1/<slug> bere fotku z galerie (pole mediagallery) – u 21 viditelných aut doplněna hlavní fotka do galerie (API, hned živé).
- Mercedes Vito skryt (zobrazitNaWebu prázdné). Boxer (oba): cena „od 690 Kč/den bez DPH“.
- Editor (publikováno 2026-11-05): menu „Auta“ → „Flotila“; výpis Flotila – dataset 30 položek, fotka v kartě
  odkazuje na detail (Auta (Title)); landing page – dataset 12 položek.
- S publikací šla ven i dřívější změna menu „Dlouhodobý pronájem“ → „Flexibilní pronájem“ (schváleno Erikem).

## Konfigurátor pronájmu (2026-11-06)
Nová stránka /konfigurator (Velo + vlastní prvek, ceník v CMS, dostupnost z Renteonu, poptávky do kolekce Poptavky).
Detail v `konfigurator/README.md`. Tlačítko „Vybrat auto“ na /dlouhodoby-pronajem přejmenováno na „Spočítat cenu“ → /konfigurator.
- 2026-11-06: po zapnutí Dev Mode Publish hlásil chybu buildu v původním kódu stránky Flotila (`public/pages/ie56l.js`,
  ř. 13 – tři nadbytečné „(“ v podmínce filtrů). Opraveno v editoru, jiné chyby kód nehlásí.
- 2026-11-06 večer:
  - Landing „Auta v nabídce“ – v CMS Auta přidán GLE a landingPage = ano i pro Tonale, CLE, 3008, Boxer;
    dataset1 v editoru omezuje počet položek → v kódu stránky `setPageSize(30)` (`konfigurator/velo/page-flexibilni-pronajem.js`).
  - Tlačítko „Spočítat cenu →“ (#button8, odkaz /konfigurator) vráceno do prostředního bílého sloupce mezi fotkami
    (section2 → columnStrip7 → column25), 170×52, černé, zaoblené, pulzuje (wix-animations), hover = invertní barvy.
  - Dlaždice GLE / CLE / Tonale sjednoceny se Škodami: 1280×744, bílé pozadí, auto 57 % šířky (max. 48 % výšky),
    spodek kol v 80 % výšky – `obrazky/normalizuj_dlazdici.py`. GLE je AI fotka (bílé pozadí, SPZ „GLE 2025“).
    Peugeot 3008 má zdroj jen 420×349 a v kartě je větší než ostatní – chce to lepší fotku.
  - Flotila (/vypis-auta): všech 22 karet sjednoceno stejnou normou (1280×744, bílé pozadí, auto 57 % šířky / max 48 % výšky,
    spodek 80 %) – Škody, 3008, BMW X1/X3/X4/218i, Multivan (+ Transporter, stejná fotka), Boxery. Zdroje mají jen 420–1200 px,
    takže zvětšení je převzorkování (postupně po 1,5×) + doostření (unsharp mask), ne AI upscale. Zpracováno v prohlížeči
    stejným algoritmem jako `obrazky/normalizuj_dlazdici.py`; nové soubory car-<vůz>-1280.webp v Media Manageru,
    přepsáno v CMS Auta (image + mediagallery) i KonfiguratorVozy (obrazek).
  - Konfigurátor: tlačítka doby pronájmu ukazují aktivní volbu (výchozí 6 měsíců zvýrazněné jako 2 500 km).
  - Flotila doplněno: Boxer fotky prohozeny (L3H2 = vysoká dlouhá, 3 seat = krátká), X4 a X1 „Modelový rok 2021“ v krátkém popisu,
    Fiat 500 Cabrio zapnut (zobrazitNaWebu, sjednocená fotka, cena na dotaz). Nové položky GLC (cena na dotaz) a M5 Competition
    (9 990 Kč/den bez DPH, F90 4,4 V8 460 kW) – zatím skryté, čekají na fotky (pak normalizovat a zapnout zobrazitNaWebu).
    BMW 218i – fotku mění Erik v CMS.
  - Flotila: štítek na kartě místo paliva ukazuje modelový rok (nové pole `modelovyRok` v CMS Auta; kód
    `konfigurator/velo/page-flotila-stitek-rok.js`). Roky: Škoda 2026, BMW 2021 (218i 2022), 3008 2021/22, Mercedes 2025, GLC 2026,
    M5 2021, Fiat 500 2022, Tonale 2024. Boxery a Multivan rok nemají → štítek skrytý.
  - Popup (lightbox „Leták Škoda“): nový leták „Novinka – Konfigurátor pronájmu“ (840×1188, kreslený v prohlížeči přes canvas,
    soubor rxauto-letak-konfigurator.webp), klik na leták → stránka Konfigurátor.
