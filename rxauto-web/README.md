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
- 2026-11-09:
  - Fotky 218i, GLC Coupé a M5 Competition (AI z Photo Studia, Erik) sjednoceny na 1280×744, GLC a M5 zapnuty na Flotile
    (GLC přejmenováno na „GLC Coupé“ podle fotky).
  - Rozházené dlaždice na Flotile: opakovač skládá karty po sloupcích, takže vyšší karta posune vše pod ní. Příčina = zalomený
    text (CLE „190 kW (258 k)“, Tonale „206 kW (280 k)“, X1 cena na 3 řádky) → zkráceno na „190 kW“, „206 kW“,
    „18 900 Kč/měsíc bez DPH“. Všech 25 karet má teď stejnou výšku 560 px. Nové texty držet krátké (výkon jen v kW, cena 1–2 řádky).
  - Z Flotily smazána omylem vložená kopie starého tlačítka „Spočítat cenu“.
  - Zveřejněno 2026-11-09 13:15 (Erik „publikuj“): konfigurátor (předvolba 6 měsíců, bez příplatků), tlačítko „Spočítat cenu →“
    mezi fotkami, Flotila se štítky roku, popup s letákem Konfigurátor → /konfigurator. Ověřeno na živém webu.
  - Odpoledne: BMW X4 a X3 nové AI fotky (MR 2022, štítek i popis), X1 zlatá metalíza (MR 2021) – Photo Studio, sjednoceno 1280×744.
  - Konfigurátor: Roller Team s AI fotkou, nově Bürstner Delfin (AI fotka) a obytný přívěs Lifestyle Camper X-Line (fotka z kolekce
    Karavany) – oba „cena na dotaz“, Praha, spoluúčast O, mimo Renteon. U přívěsu se zatím ukazují volby nájezdu (konfigurátor
    je má pro všechny vozy).
  - Popup leták v2 (rxauto-letak-konfigurator-v2.webp): jen logo, NOVINKA, nadpis, velká fotka Superbu a tlačítko „Spočítat cenu →“;
    klik → /konfigurator.
- 2026-11-09 večer: smazáno Hobby Optima (KonfiguratorVozy + Karavany) a motorka KTM 1290 (Motorky) na Erikův pokyn.
  Nová CMS kolekce `ProdejLeasing` (prodej vozů po operativním leasingu: title, znacka, obrazek, modelovyRok, najezdKm, palivo,
  prevodovka, vykon, cena, dostupneOd, popis, zobrazitNaWebu, poradi) – stránka v menu čeká na editor (zamčený jiným uživatelem).
  Čeká: větší fotky Rolleru a Delfínu v konfigurátoru, karta Bürstner Delfin v Karavanech, publikace popupu v2.
- 2026-11-09 22:15: editor převzat (s.hanka měl editor zavřený), zveřejněn popup v2. Roller a Delfin v konfigurátoru zvětšené
  (vůz 94 % šířky / 92 % výšky dlaždice), nová karta Bürstner Delfin v kolekci Karavany (AI fotka 1200×628, palivo Diesel,
  ostatní údaje prázdné – doplnit). Ověřeno na živém webu.
- 2026-11-09 noc: Karavany – Roller Team nová AI fotka (1200×628 jako Delfin). Konfigurátor – fotky osobních aut v dlaždicích
  zvětšené přes Wix crop URL (`/v1/crop/x_230,y_192,w_820,h_477/fill/w_640,h_372,...`) v poli obrazek kolekce KonfiguratorVozy.
- Nová stránka v menu „Prodej vozů“ (/prodej-vozu, SEO title „Prodej vozů z operativního leasingu | RX AUTO“):
  - vlastní prvek `rx-prodej` (Velo `public/custom-elements/rx-prodej.js`, ID `#rxProdej`), kód stránky
    `prodej-leasing/velo/page-prodej-leasing.js` načte kolekci `ProdejLeasing` (zobrazitNaWebu, řazení poradi) a pošle JSON do atributu `data`.
  - Výhody: jeden majitel, autorizovaný servis, doložený nájezd, pronájem na vyzkoušení, žádné maskované opravy, odpočet DPH,
    férová cena, výkup protiúčtem. Financování na Erikův pokyn odebráno.
  - Ceny (Erik): aktuální zůstatková cena z tabulky ZH_RX pro aktuální měsíc + marže 40 000 Kč bez DPH (Peugeot 15 000),
    zaokrouhleno nahoru na tisíce; jen bez DPH. Nájezd z Renteonu (CZ+SK, api/car/getSimpleList). Interní zůstatky ani marže
    se do CMS/repa neukládají – v kolekci je jen výsledná prodejní cena.
  - Pozor v editoru: název tagu custom elementu se uloží až po opuštění pole (Tab) a znovu-otevření dialogu; ověřit v Test Site
    (v DOM musí být `<rx-prodej>`).
- 2026-11-09 23:05: z ProdejLeasing smazány 8H58836 (Karoq) a 8H59271 (Superb Combi L&K) na Erikův pokyn → 28 vozů.
  Stránka Prodej vozů zveřejněna (Erik „publikuj“), ověřeno na živém webu (menu + 28 karet).
- 2026-11-09 noc (2):
  - ProdejLeasing: smazán levnější Multivan 8AR9080 (4MOTION) → 27 vozů. Modelové roky podle Renteonu: Renteon nemá vyplněné
    `ProductionYear`, rok = prefix inventárního čísla (např. 22/7 → 2022, sedí s datem první aktivity). Změna jen X4 8AX8544 → 2021.
    Scala 8H59043 v Renteonu není → 2026 (leasing od 4/2026).
  - Pozor: 8H34367 je v tabulce ZH_RX jako Peugeot 3008, v Renteonu jako Škoda Karoq SportLine – ověřit.
  - AI fotky (Photo Studio): Scala Monte Carlo červená, Formentor šedá (barva z Renteonu), 2008 Allure oranžová, 2008 GT bílá.
    Normalizace 1280×744 (vůz 57 % šířky) v prohlížeči, nahrány jako jeden sprite `prodej-sprite-4vozy.webp` (1280×2976),
    v CMS obrazek = crop URL `/v1/crop/x_0,y_<744*i>,w_1280,h_744/fill/w_640,h_400,...`.
  - Upload tip: PUT na upload.wixmp.com z ExecuteWixAPI nejde (401 – přidává Wix auth). Nahrávat z prohlížeče (fetch PUT),
    víc obrázků = jeden sprite + crop URL nebo `site-media/v1/files/import` s crop URL (vytvoří samostatné soubory).
  - Hlavička: tlačítko „Flexibilní pronájem →“ (#button11) přesunuto vedle loga (desktop X 560 / Y 3, 200×38), kulaté rohy 18 px,
    stín, hover zelená #19a463 s bílým textem. Menu už nepřekrývá „Kontakt“. Mobil: X 76, šířka 176, text bez šipky
    (`web/masterPage.js`).
  - Popup „Leták Škoda“ v3: dvě novinky, dva obrázky s vlastním odkazem – #image2 horní půlka (Konfigurátor → /konfigurator),
    #image3 spodní půlka (Prodej vozů po leasingu → /prodej-vozu). Desktop 420×297 každý, mobil 260×184.
    Soubory rxauto-letak-v3-konfigurator.webp, rxauto-letak-v3-prodej.webp (celek rxauto-letak-v3-celek.webp).
- 2026-11-09 23:55: 8H34367 opraven na Škoda Karoq SportLine 2.0 TDI DSG (Renteon: 110 kW, diesel, automat, 12 005 km,
  MR 2024, foto car-karoq-1280.webp; cena dál na dotaz – v ZH_RX nemá splátkový kalendář). Scala 8H59043 MR 2024 (Erik).
  Zveřejněno (Erik „publikuj“): hlavička s tlačítkem vedle loga, popup v3 se dvěma novinkami. Ověřeno na živém webu.
- 2026-11-09 23:52: 8H34367 smazán z ProdejLeasing (v ZH_RX chybně jako Peugeot 3008, bez zůstatkové ceny; v Renteonu je to
  Karoq SportLine) → 26 vozů.
- 2026-11-10 00:30: Odkazy „Spočítej“ přímo do konfigurátoru s předvybraným vozem (`/konfigurator?vuz=<_id KonfiguratorVozy>`).
  - Nové pole `konfiguratorVuz` (TEXT) v CMS Auta a Karavany = _id vozu v KonfiguratorVozy. Vyplněno pro 16 aut
    (GLE, CLE, Kamiq ×2, Octavia, Octavia Combi SL, Superb SL/Combi SL/Combi L&K, Tonale, Karoq, 3008, Kodiaq SL/RS,
    Fabia MC, Boxer L3H2) a 3 karavany (Delfin, Roller, X-Line). Prázdné = vůz v konfigurátoru není → „Poptat“ (M5, GLC, X1–X4,
    218i, Multivan, 500 Cabrio, Boxer 3 seat).
  - Dlaždice: Flotila (#button1 Poptat → Spočítej), Flexibilní pronájem (#button1 Více → Spočítej, zrušeno napojení na dataset).
    Detaily auta a karavanu (#button2 Poptat → Spočítej). Kód: `konfigurator/velo/page-dlazdice-spocitej.js`,
    `page-detail-spocitej.js`. Nový vůz do konfigurátoru = doplnit jeho _id do konfiguratorVuz v Auta/Karavany.
  - Hlavička: tlačítko „Flexibilní pronájem →“ posunuto níž (Y 8) – zarovnané s logem.
  Zveřejněno 2026-11-10 00:31 (Erik „publikuj“), ověřeno na živém webu (dlaždice, detail M5 = Poptat, Delfin = Spočítej).
