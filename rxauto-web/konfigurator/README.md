# Konfigurátor pronájmu – rxauto.cz/konfigurator

Klient si vybere vůz, pobočku (Praha / Ostrava / Bratislava), termín, nájezd a služby, cena se počítá živě,
dostupnost se ověří v Renteonu a klient pošle nezávaznou poptávku (bez platby – nejdřív prověřujeme klienta).

## Pravidla (Erik, 6. 11. 2026)
- Cena = měsíční cena × dní / 30, min. 30 dní, Škody max. 6 měsíců.
- Nájezd: v ceně 2 500 km/měs., každých dalších 1 000 km = 6 000 Kč/měs. bez DPH.
- Druhý řidič: u pronájmu nad 30 dní zdarma, jinak 120 Kč/den.
- Spoluúčast: standard 10 % min. 10 000 Kč; 5 % (min. 5 000) a 0 % za příplatek podle kategorie A/B/C
  (příplatky zatím prázdné → web ukáže „upřesníme v nabídce“).
- Vůz, který na pobočce není / není volný: hláška, že je dostupný na jiné pobočce a po dohodě ho přistavíme.
- Později: záloha přes Stripe.

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
  maxMesice, aktivni, poradi, obrazek, popisWeb (text pro klienta), servisVCene, poznamka (interní).
- `KonfiguratorNastaveni`: dniVMesici, minDni, kmVCene, krokKm, cenaKrok, ridicDen, ridicZdarmaOd, dph, najezdy.
- `KonfiguratorSpoluucast`: A/B/C, priplatek5, priplatek0 (Kč/měs. bez DPH).
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
- Omezení mapování SIPP: Kamiq Selection = MC (CFAR), Superb Combi SL = L&K (FWAR), Karoq sdílí IGAR s 3008 (CZ),
  Kodiaq SL = RS (FFAR). Tonale není v Renteonu → vždy „ověříme ručně“.

## Test 2026-11-06 (Test Site)
Ceník z CMS, předvýběr vozu, přepočet (Kodiaq RS, 30 dní, 3 500 km = 24 900 Kč bez DPH, backend spočítal stejně),
odeslání poptávky do `Poptavky` OK (testovací záznam smazán). Dostupnost zatím „ověříme ručně“ – chybí secrets.
