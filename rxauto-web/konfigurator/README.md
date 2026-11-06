# Konfigurátor pronájmu – rxauto.cz/konfigurator

Klient si vybere vůz, pobočku (Praha / Ostrava / Bratislava), termín, nájezd a služby, cena se počítá živě,
dostupnost se ověří v Renteonu a klient pošle nezávaznou poptávku (bez platby – nejdřív prověřujeme klienta).

## Pravidla (Erik, 6. 11. 2026)
- Od 30 dní: cena = měsíční cena × dní / 30, zvýrazněná cena za měsíc, bez celkového součtu.
  Ceníková měsíční cena platí pro pronájem od 6 měsíců; každý celý kalendářní měsíc kratší = +10 %
  (5 měs. +10 %, 3 měs. +30 %, 1 měs. +50 %). Výchozí termín v konfigurátoru = 6 měsíců. Nastavení zakladMesice, priplatekZaMesic.
- Pod 30 dní (min. 1 den): denní cena = (měsíční cena + 100 %) / 30 = měsíc × 2 / 30, zvýrazněná cena za den + celkový součet.
  Příplatky (nájezd, spoluúčast) se poměrně přepočítávají × dní / 30. Škody max. 6 měsíců.
- Nájezd: v ceně 2 500 km/měs., každých dalších 1 000 km = 6 000 Kč/měs. bez DPH.
- Druhý řidič: u pronájmu nad 30 dní zdarma, jinak 120 Kč/den.
- Spoluúčast (Erik 6. 11. 16:30): standard 10 % min. 10 000 Kč. Pod 30 dní: 5 % a 0 % za příplatek Kč/DEN podle kategorie
  (list Spoluúčast). Od 30 dní: 5 % = +10 % z ceny nájmu (vč. přirážky za kratší pronájem), 0 % nelze (volba zašedlá).
  Původně: 5 % (min. 5 000) a 0 % za příplatek podle kategorie A/B/C
  (prázdný příplatek → web ukáže „upřesníme v nabídce“).
- Vůz, který na pobočce není / není volný: hláška, že je dostupný na jiné pobočce a po dohodě ho přistavíme.
- Později: záloha přes Stripe.
- Úprava 6. 11. odpoledne: 3008 = 13 900 Kč/měs. + volba neomezeného nájezdu za pevný příplatek 6 000 Kč/měs.;
  3008 a Tonale bez omezení doby (tlačítko 12 měsíců); přidány Mercedes GLE a CLE 300 4MATIC (MR 2025, cena na dotaz),
  Peugeot Boxer L3H2 (skupina Dodávky, 20 700 Kč/měs. = 690 Kč/den × 30 – ověřit), obytné vozy Roller Team
  Livingstone 2 Sport a Hobby Optima T65 HFL (skupina Obytné vozy, cena na dotaz, dostupnost ručně).
  Modelové roky: 3008 2022, Tonale 2024, GLE/CLE 2025. Nové kategorie spoluúčasti P (prémiové), D (dodávky), O (obytné).
- Ceník od Erika 6. 11. 15:29: GLE 59 900, CLE 29 900, obytné vozy 39 000 Kč/měs.; Boxer ponechán 20 700.
  Příplatky spoluúčast 5 % / 0 % (Kč/měs.): A 200/400, B 300/500, C 400/600, P 800/1 500, D 300/500, O 400/800.

## Soubory
| Soubor | Kde ve Wixu |
|---|---|
| `velo/backend/konfigurator.web.js` | Backend → `konfigurator.web.js` (ceník z CMS, Renteon token + dostupnost, uložení poptávky, notifikace) |
| `velo/public/custom-elements/rx-konfigurator.js` | Public → `custom-elements/rx-konfigurator.js` (UI, Shadow DOM, výpočet ceny) |
| `velo/page-konfigurator.js` | Kód stránky „Konfigurátor“ (most mezi prvkem a backendem) |
| `cenik_konfigurator.xlsx`, `build_cenik.py` | Ceník k aktualizaci (listy Parametry, Spoluúčast, Vozy, Nájezd, Kalkulace) |
| `cenik_to_json.py` | Excel → JSON pro CMS kolekce |

Stránka `/konfigurator` (skrytá v menu), prvek Custom Element `#rxKonfigurator`, tag `rx-konfigurator`
(soubor registruje i `wix-default-custom-element`, protože editor tag občas neuloží). Na živé doméně se výška
prvku přizpůsobí obsahu. Tlačítko „Spočítat cenu“ na /dlouhodoby-pronajem vede na konfigurátor (dřív „Vybrat auto“ → kotva).
`?vuz=Kodiaq` v URL předvybere vůz.

## CMS kolekce
- `KonfiguratorVozy` (čtení všichni): title, cenaMesic, kmVCene, kategorieSpoluucasti, sippCz, sippSk, prg/osr/bts,
  maxMesice, aktivni, poradi, obrazek, popisWeb (text pro klienta), servisVCene, poznamka (interní),
  skupina (Osobní auta / Dodávky / Obytné vozy), modelovyRok, neomezenyPriplatek (Kč/měs., prázdné = bez volby).
- `KonfiguratorNastaveni`: dniVMesici, minDniPronajmu (min. 1 den; starý klíč minDni=30 drží jen pro starou zveřejněnou verzi, po publikaci smazat), kratkodobyKoef (2), kmVCene, krokKm, cenaKrok, ridicDen, ridicZdarmaOd, dph, najezdy.
- `KonfiguratorSpoluucast`: A/B/C/P/D/O, priplatek5, priplatek0 (Kč/měs. bez DPH).
- `Poptavky` (jen admin) – **osobní údaje klientů, nikdy neexportovat do repa.**

Aktualizace ceníku: upravit Excel → `python3 cenik_to_json.py cenik.xlsx` → přepsat položky v CMS
(nebo upravit přímo v CMS). Backend drží ceník v cache 5 minut.

## Renteon
- CZ `rxauto.s3.renteon.com` (PRG office 25, OSR 26, ceník 1850 CW Web), SK `cwslovakia.s6.renteon.com` (BTS 128, ceník 352).
- `POST /token` (grant_type=password, client_id=Inhouse.WebApp, office_id) → Bearer;
  `POST /api/availability/search/` → `AvailabilityCarCategories[].SIPP / AvailableCount` (počty jsou za pobočku).
- Údaje ve Wix Secrets Manageru: `RENTEON_CZ_USER`, `RENTEON_CZ_PASSWORD`, `RENTEON_SK_USER`, `RENTEON_SK_PASSWORD`
  (zadává Erik, ideálně samostatný API uživatel s právem jen číst dostupnost).
- Bez údajů / při chybě konfigurátor funguje dál, jen ukáže „ověříme ručně“ a poptávka se uloží se stavem `neovereno`.
- SIPP nových vozů (CZ, jen Praha): GLE = GFAR, CLE = UEAR, Boxer = FKMR. Obytné vozy nejsou v Renteonu.
- Omezení mapování SIPP: Kamiq Selection = MC (CFAR), Superb Combi SL = L&K (FWAR), Karoq sdílí IGAR s 3008 (CZ),
  Kodiaq SL = RS (FFAR). Tonale není v Renteonu → vždy „ověříme ručně“.

## Test 2026-11-06 (Test Site)
Ceník z CMS, předvýběr vozu, přepočet (Kodiaq RS, 30 dní, 3 500 km = 24 900 Kč bez DPH, backend spočítal stejně),
odeslání poptávky do `Poptavky` OK (testovací záznam smazán). Dostupnost zatím „ověříme ručně“ – chybí secrets.
