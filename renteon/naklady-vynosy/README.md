# Náklady vs výnosy půjčovny

Měsíční P&L po pobočkách (PRG, OSR, BTS, HAVEX zpětná fakturace) a ziskovost po SPZ, 09/2025–10/2026.

**Výnosy:** Renteon (CZ+SK, `renteon/vynosy-flotila`), Vyfakturuj RX Auto + RX Auto SK (dlouhodobé pronájmy), HAVEX Mobility.
**Náklady (Spark – přijaté faktury):**
- leasing: HAVEX platební kalendáře (`scripts/parse_pk.py`), odhad starších smluv z přehledu zápůjček, EFS na RX (`scripts/efs.py`)
- Carnetto RX přefakturace na RX Auto: půjčovné EFS (`scripts/carnetto_efs.py`) a pojištění flotily ČGP 6287974108 (`scripts/gcpparse.py`) → `scripts/carnetto_build.py` → `data/carnetto.csv`
- pojištění: Kooperativa (`koopload.py`), Generali RS (`gcpparse.py`), D.A.S.
- servis/opravy/ostatní: `scripts/servis_build.py`

**Postup:** vstupní CSV do `data/` → `python build_pl.py` (pl_pobocky.csv, pl_auta.csv, carnetto_mesice.csv) → `python build_xlsx_pl.py` → Excel; `dashboard_index.html` = stránka dashboardu (Dashboard artifact „Náklady vs výnosy půjčovny“).

Pobočka vozu = dominantní pobočka v Renteonu v daném měsíci; SK vozy BTS. Kurz €: 24,3. Data se nekomitují.
Chybí: palivo/DKV, mzdy, nájmy poboček, provize brokerů, franšíza.
