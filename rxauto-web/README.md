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
