# Náklady vs výnosy půjčovny

Měsíční P&L po pobočkách (PRG, OSR, BTS, HAVEX zpětná fakturace) a ziskovost po SPZ a letech, 01/2024–10/2026.

**Výnosy:** Renteon (CZ+SK, `renteon/vynosy-flotila`), Vyfakturuj RX Auto + RX Auto SK (dlouhodobé pronájmy), HAVEX Mobility.
**Náklady (Spark – přijaté faktury):**
- leasing: HAVEX platební kalendáře (`scripts/parse_pk.py`), odhad starších smluv z přehledu zápůjček, EFS na RX (`scripts/efs.py`)
- Carnetto RX přefakturace na RX Auto: půjčovné EFS (`scripts/carnetto_efs.py`) a pojištění flotily ČGP 6287974108 (`scripts/gcpparse.py`) → `scripts/carnetto_build.py` → `data/carnetto.csv`
- pojištění: Kooperativa (`koopload.py`), Generali RS (`gcpparse.py`), D.A.S.
- servis/opravy/ostatní: `scripts/servis_build.py` + faktury Auto Palace (mytí), Pavel Rejdík (servis PRG), SIMO CAR PLUS / Šimon Závěšický (servis OSR) → `data/servis2.csv`
- palivo: měsíční daňové doklady CCS (ccs@ccs.cz, „CCS-Danovy doklad - YYYYMM“) → `scripts/parse_ccs.py` → `data/palivo.csv` (SK tankování vč. SK DPH)
- nájmy poboček: CTP (letiště Praha), BTS aero (Bratislava, RX Auto SK), Letiště Ostrava → `data/najmy.csv`

**Postup:** vstupní CSV do `data/` → `python build_pl.py` (pl_pobocky.csv, pl_auta.csv, carnetto_mesice.csv) → `python build_xlsx_pl.py` → Excel; `dashboard_index.html` = stránka dashboardu (Dashboard artifact „Náklady vs výnosy půjčovny“).

Pobočka vozu = dominantní pobočka v Renteonu v daném měsíci; SK vozy BTS. Kurz €: 24,3. Data se nekomitují.
Chybí: mzdy, provize brokerů, franšíza.

**Od 2024:** výnosy po autech z Renteonu (getIncomeAndExpenseComparison po měsících, CZ i SK) a z Vyfakturuj (stejná klasifikace jako `renteon/vynosy-flotila`). Leasing do 06/2025 = odhad z HAVEX přehledu zápůjček (`scripts/leasing_build.py`, P0 = 2024-01). Pojištění 2024 `scripts/pojisteni_2024.py`, servisy 2024–08/2025 `scripts/build_servis_2024.py`. Chybějící nájmy poboček do 06/2025 = odhad podle pozdějších sazeb (kategorie `najem_odhad` v `build_pl.py`).

**Oprava výnosů (23. 10. 2026):** `python oprava_vynosu.py` po `build_pl.py` – doplní výnos z Renteonu CZ u aut, kde ho P&L po autech
neměl (porovnání se smlouvami po SPZ z Podrobného přehledu rezervace, `data/doplneni_renteon.csv`; např. 5SJ5242 ve flotile HG) a nájmy
fakturované z Vyfakturuj RX Auto SK (`data/doplneni_vyfakturuj_sk.csv`, € × 24,3; např. 8H02853). Celkem +1,04 mil. Kč za 2025–2026
(PRG +571 tis., OSR +152 tis., BTS +316 tis.). Do budoucna: v `build_pl.py` brát výnosy Renteonu po SPZ smlouvy bez ohledu na flotilu
a exportovat i Vyfakturuj RX Auto SK.
