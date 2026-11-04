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
Alfa Tonale PHEV od 19 900. Fotky = generické cutouty z IG design artefaktu, zmenšené na 380 px webp, v Media
Manageru (4d8ed0_…~mv2.webp). Ostatních 38 modelů zůstává v kolekci, jen skryté.
Pozor: výpis /vypis-auta zobrazí max. 12 položek (limit datasetu v editoru) – při 13 jedna vypadne.
Wix cache: změny se projeví hned s ?nocache=…, bez parametru až po vypršení cache.
