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
