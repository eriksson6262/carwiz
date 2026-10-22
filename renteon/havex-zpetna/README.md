# Zpětná fakturace HAVEX – co nebylo vyfakturováno

Porovnání přehledu zápůjček HAVEX (list „Vozy“, sloupec „K fakturaci zpět na CC“) s doklady Vyfakturuj RX Auto CZ na HAVEX Mobility.

1. Přehled zápůjček (poslední příloha od M. Dvořákové, Spark) → `data/vozy.pkl` (řádky listu Vozy).
2. Vyfakturuj (přihlášená záložka, export JSON podle DUZP 2020–2026) → položky odběratele HAVEX Mobility `data/havex_polozky.csv`
   (cislo, duzp, text, castka, typ, hlavicka = text před položkami + č. objednávky, id_parent); faktury k týmž SPZ na jiné odběratele → `data/jine_faktury.csv`.
   Šablony pravidelných faktur (všechny vč. ukončených, `/system/ajax/patterns/` isStopped=0 + detail `/faktury/crud-pravidelne/<id>/`) → `data/sablony.csv`.
3. `python3 parovani.py` – měsíční období podle smluv, párování položek (SPZ, jinak částka + začátek období) → `output/obdobi.csv`, `output/polozky_spz.csv`.
4. `python3 vystup.py` → `output/Nevyfakturovano_HAVEX.xlsx` (po autech, od 09/2021 a zvlášť před 09/2021).

Poznámky: první faktura na HAVEX ve Vyfakturuj je z 15. 9. 2021. SPZ se hledá v textu položky, pak v hlavičce faktury (dříve se psala tam),
pak podle šablony pravidelné faktury (stejná cena bez DPH + den začátku období). Regex SPZ zahrnuje i nový tvar 1AD L159.
Konec smlouvy podle přehledu – předčasně vrácená/prodaná auta mají „Mělo být“ nadsazené (žlutě, pokud k autu existují jiné faktury).
Data i výstupy obsahují odběratele – v `data/` a `output/`, necommitovat.
