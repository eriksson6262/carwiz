# Kanály rezervací – odkud jsou zákazníci a kolik vynáší (CZ + SK)

Rozpad smluv za 12 měsíců podle kanálu (Rentalcars, DiscoverCars, CarTrawler…, přímý web, pobočka), pobočky, délky pronájmu,
předstihu rezervace a kategorie auta. Výnos/den, doplňkový prodej, storna, vytíženost flotily. Cíl: kde vzít víc klientů a tržeb.

## Sběr (vestavěný prohlížeč, přihlášený Renteon)
1. CZ `rxauto.s3.renteon.com`, SK `cwslovakia.s6.renteon.com` – vložit `collect_renteon.js` přes javascript_tool.
2. `RXCH.run('2025-10','2026-10')` → na pozadí stáhne report **Podrobný přehled rezervace**
   (`api/Report/getDetailedBookingOverview`, xlsx) po měsících výdeje, zvlášť aktivní a zrušené. ~30 s.
3. Excel se parsuje ve stránce (SheetJS), ven jde jen anonymizovaný řádek na smlouvu – žádná jména, čísla smluv, SPZ, poznámky.
   `RXCH.csv(0,5000)` → gzip+base64 → `data/rezervace_CZ.csv`, `data/rezervace_SK.csv` (necommitovat).
4. Flotila: `api/report/getFleetStateByOfficeInPeriod` (CZ fleet 7, SK fleet 20) → `data/flotila.csv` (pob_out, mesic, aut).

## Výpočet
`python3 analyza.py 2025-10 2026-09` → `output/kanaly.csv, mesice.csv, delka.csv, predstih.csv, sipp.csv, doplnky.csv`.
- CZ v Kč, SK v €, bez DPH (`AmountNetWithDiscountDomestic` položek smlouvy).
- Výnos = všechny položky kromě škod a pokut. Typ OFF (nabídky) vynechán. Měsíc = měsíc výdeje.
- `k_pult` = doplňky přidané až na přepážce (`IsCreatedOnReservation = false`).
- Partner `Booking.com Transport Limited` = Rentalcars.com. Částky jsou to, co je v Renteonu (u partnerů s netto ceníky už po provizi).
- Využití flotily = dny podle činností aut (`activities()` v `collect_renteon.js` → `data/aktivity_CZ.csv`), ne podle smluv.
  Pozor: první verze (22. 10.) počítala jen dny krátkodobých smluv podle měsíce výdeje → vyšlo ~42 % v létě, což bylo špatně.
- Vyfakturuj: export dokladů podle DUZP (postup v `../vynosy-flotila/collect_vyfakturuj.js`), nájemní položky po měsících → `data/vyfakturuj_dlouhodobe.csv`.

## Zjištění (22. 10. 2026, X/2025–IX/2026)
Viz dashboard „Kanály rezervací“ (typ Dashboard, datasety = CSV z `output/`, stránka `dashboard_index.html`). PRG: Rentalcars 43 % smluv / 35 % výnosu za 909 Kč/den, přímý web 16 % / 21 % za 1 210 Kč/den.
Doplňkové pojištění: PRG 29 % smluv, OSR 24 %, BTS 16 %.

## Využití flotily – oprava (23. 10. 2026)
- Renteon „obsazeno“ (fleetAvailability, BookedFleetCount) PRG: VII–VIII 2026 Ø 87–89 %, 29 dní ≥ 90 %, špička 93–94 %. Počítá i budoucí rezervace a blokace.
- Podle činností aut PRG (flotila pronájmu, Ø 187 aut v srpnu): krátkodobé 51 %, dlouhodobé 17 %, interní 11 %, servis/přesun 4 %, volné (Líný) 18 %.
  Mimo sezónu (I–III) krátkodobé jen 17–21 %, dlouhodobé 33–36 %, interní 20–23 %.
- Interní („Vnitřní“) trvale ~20 aut flotily pronájmu + ~6 HG v PRG – nutno ověřit, co to je.
- Vyfakturuj dlouhodobí B2B (bez HAVEX a Fábiána) ~1,2–1,4 mil. Kč měsíčně; typicky 12–17 tis. Kč/auto/měsíc (≈ 400–550 Kč/den) vs krátkodobé ~900 Kč/den.

## Ziskovost podle třídy (23. 10. 2026)
`python3 tridy.py 2025 2026` – P&L po SPZ z dashboardu „Náklady vs výnosy“ (`data/pl_auta.csv`, asset `pl_auta.csv`) + dny po činnostech
na SPZ a rok z Renteonu (`data/dny_auta.csv`, stejná klasifikace jako `activities()`). Jen auta s SIPP, ≥ 30 dní v provozu, bez řádků „bez leasingu v datech“.
Výsledek/auto/měsíc = výsledek / dny provozu × 30,4. V nákladech chybí mzdy, provize brokerů, franšíza a palivo po autech.
- Auta převážně v dlouhodobém pronájmu (< 20 % dní krátkodobě): ≈ 0 Kč/měsíc; převážně krátkodobá (50–80 %): ≈ +9 tis., > 80 %: ≈ +11,7 tis. Kč/měsíc.
- Velké třídy: Economy EDAR +6,1 tis., Compact CFAR +5,9 tis., Economy IGAR +5,1 tis., SUV FFAR +5,0 tis., IWAR +3,8 tis., FWAR +2,7 tis. Kč/auto/měsíc.
- Minibus SVAR +16,8 tis., ale 3 auta a chybí pojištění; GFAR a mini bez leasingu v datech – nespolehlivé.
