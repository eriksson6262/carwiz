# Výnosy a flotila po měsících (CZ + SK)

Měsíční přehled výnosů bez DPH (Renteon + Vyfakturuj), počtu smluv a průměrného počtu vozidel pro PRG, OSR (Kč) a BTS (€), 2024–2026, srovnání rok proti roku. Pokuty se vyčleňují zvlášť.

## Postup
1. Ve vestavěném prohlížeči otevřít Renteon CZ (`rxauto.s3.renteon.com`), při loginu požádat Erika o přihlášení.
2. `collect_renteon.js`:
   - `revenue()` → report **Realizace po kancelářích** (`api/report/GetRealizationByOffice`), měsíc podle `DateOfPayment` (datum vyúčtování). Pobočka = kancelář OUT smlouvy.
   - `fleet()` → **Stav flotily po kancelářích v přehledu období** (`api/report/getFleetStateByOfficeInPeriod`), jen flotila 7 „Pronájem vozového parku“. `fleetAvailability` NEPOUŽÍVAT pro historii – vyřazená auta v ní chybí.
   - `fines([25,26])` → pokuty z položek dokladů (ServiceTypeId 14 + zpracování).
3. Vyfakturuj: `collect_vyfakturuj.js` (export JSON podle DUZP, klasifikace položek, pobočka podle SPZ z Renteonu). Bez HAVEX Mobility; GLOBAL ASSISTANCE = OSR; auta mimo Renteon = PRG (+ do počtu vozidel).
4. Totéž v SK (`cwslovakia.s6.renteon.com`, `fines([128])`).
4. Sestavit CSV `data/vynosy_flotila.csv` (od ledna 2024; BTS začala v březnu 2024) (sloupce viz `build_xlsx.py`): `poplatky_bez_pokut = poplatky − pokuty − zprac_pokut`, `ostatni = výnos bez pokut − nájem − pojištění − poplatky bez pokut − škody`.
5. `python3 build_xlsx.py data/vynosy_flotila.csv output/Vynosy_flotila.xlsx` + `recalc.py`. Excel: 3 roky (2024–2026), graf výnos (sloupce) + Ø vozidel (plná) + smlouvy (přerušovaná), barva = rok.
6. Dashboard: typ Dashboard, dataset `vf` = přiložené CSV, stránka `dashboard_index.html`.

## Zjištění (20. 10. 2026)
- V 2025 (do srpna) se pokuty za celou flotilu fakturovaly přes pobočku **Ostrava** jako účty bez smlouvy (I–IX 2025: pokuty 514 tis. + zpracování 344 tis. Kč) → nafukovaly „poplatky“ OSR. Od září 2025 jsou pokuty u smluv pobočky rezervace (hlavně PRG).
- Bez pokut I–IX: PRG +0,6 %, OSR −8,6 %, BTS +63 %; smlouvy PRG +14 %, OSR +13 %, BTS +53 %.

- I–IX 2024 → 2025 → 2026 (bez pokut): PRG 8,75 → 13,27 → 13,34 mil. Kč; OSR 1,19 → 1,76 → 1,61 mil. Kč; BTS 48 → 87 → 142 tis. €.
- 2024: pokuty téměř výhradně přes OSR (účty bez smlouvy).

- S Vyfakturuj (I–IX 2024 → 2025 → 2026): PRG 19,6 → 26,0 → 27,7 mil. Kč (z toho Vyfakturuj 10,8 → 12,7 → 14,4); OSR 1,87 → 2,47 → 2,43 mil. Kč (Vyfakturuj 0,68 → 0,72 → 0,83).
- Vyfakturuj obsahuje i prodeje aut (AUTOCENTRUM Jičín, AZISFIN, HAVEX-auto…) – ty se do výnosů z pronájmu nepočítají.
