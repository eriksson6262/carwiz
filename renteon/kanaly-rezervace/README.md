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
- Vytíženost = dny krátkodobých smluv v Renteonu / (Ø aut × dny v měsíci). Auta pronajatá dlouhodobě mimo Renteon (Vyfakturuj) ji snižují.

## Zjištění (22. 10. 2026, X/2025–IX/2026)
Viz dashboard „Kanály rezervací“. PRG: Rentalcars 43 % smluv / 35 % výnosu za 909 Kč/den, přímý web 16 % / 21 % za 1 210 Kč/den.
Doplňkové pojištění: PRG 29 % smluv, OSR 24 %, BTS 16 %.
