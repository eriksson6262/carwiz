# Výnosy a flotila po měsících (CZ + SK)

Měsíční přehled výnosů bez DPH, počtu smluv a průměrného počtu vozidel pro PRG, OSR (Renteon CZ, Kč) a BTS (Renteon SK, €), srovnání rok proti roku. Pokuty se vyčleňují zvlášť.

## Postup
1. Ve vestavěném prohlížeči otevřít Renteon CZ (`rxauto.s3.renteon.com`), při loginu požádat Erika o přihlášení.
2. `collect_renteon.js`:
   - `revenue()` → report **Realizace po kancelářích** (`api/report/GetRealizationByOffice`), měsíc podle `DateOfPayment` (datum vyúčtování). Pobočka = kancelář OUT smlouvy.
   - `fleet()` → **Stav flotily po kancelářích v přehledu období** (`api/report/getFleetStateByOfficeInPeriod`), jen flotila 7 „Pronájem vozového parku“. `fleetAvailability` NEPOUŽÍVAT pro historii – vyřazená auta v ní chybí.
   - `fines([25,26])` → pokuty z položek dokladů (ServiceTypeId 14 + zpracování).
3. Totéž v SK (`cwslovakia.s6.renteon.com`, `fines([128])`).
4. Sestavit CSV `data/vynosy_flotila_v2.csv` (sloupce viz `build_xlsx.py`): `poplatky_bez_pokut = poplatky − pokuty − zprac_pokut`, `ostatni = výnos bez pokut − nájem − pojištění − poplatky bez pokut − škody`.
5. `python3 build_xlsx.py data/vynosy_flotila_v2.csv output/Vynosy_flotila.xlsx` + `recalc.py`.
6. Dashboard: typ Dashboard, dataset `vf` = přiložené CSV, stránka `dashboard_index.html`.

## Zjištění (20. 10. 2026)
- V 2025 (do srpna) se pokuty za celou flotilu fakturovaly přes pobočku **Ostrava** jako účty bez smlouvy (I–IX 2025: pokuty 514 tis. + zpracování 344 tis. Kč) → nafukovaly „poplatky“ OSR. Od září 2025 jsou pokuty u smluv pobočky rezervace (hlavně PRG).
- Bez pokut I–IX: PRG +0,6 %, OSR −8,6 %, BTS +63 %; smlouvy PRG +14 %, OSR +13 %, BTS +53 %.
