# HAVEX – protokoly o vrácení vozidel (Petr Beyr)

Zpracování protokolů o vrácení vozidel, které posílá HAVEX Mobility (petr.beyr@havexmobility.cz).

## Postup
1. **Stažení** – Spark: `from:petr.beyr@havexmobility.cz after:<datum>`. Každé vozidlo má „Protokol o vrácení vozidla“ + „ProtokolKontroly“ (fotky), někdy „Kilometry“.
   **Pozor:** sémantické hledání Sparku s filtrem `from:` vrací jen ~20 „nejrelevantnějších“ výsledků – nové maily přebijí starší FW/Re:. Vždy hledat i podle jednotlivých RZ (z avíz vrácení od Dvořákové) a obecně „protokol o vrácení“ s `after:` bez `from:` (protokoly posílá i Tesařová, ACJC aj.). Kontrolovat, že ProtokolKontroly patří ke stejné RZ (8H84670 přišel s kontrolou 9H06026).
   FW zprávy jsou jen upomínky se stejnými přílohami. Opravené protokoly chodí jako RE: (nahradit původní).
   Ukládat jako `RZ Protokol o vraceni vozidla.pdf`, `RZ ProtokolKontroly.pdf`, `RZ Kilometry.pdf`.
2. **Roztřídění Fabian / RX Auto** – vozidlo patří Fabianovi, pokud ve Vyfakturuj existují faktury na Fábián Automotive Kft s danou RZ.
   Vyhledání (v přihlášené záložce app.vyfakturuj.cz/faktury/):
   ```js
   const f=document.querySelector('form[action*="ajax/invoices"]');
   const fd=new FormData(f); fd.set('-data-filter-[vfiSearch]','8H84601');
   const j=await (await fetch(f.action,{method:'POST',body:fd,credentials:'include'})).json();
   // j.data.items = HTML tabulka – hledat "Fábián Automotive Kft"
   ```
   Výstup: `Downloads/Protokoly_Beyr/Fabian` a `Downloads/Protokoly_Beyr/RX Auto`.
3. **Razítko RX Auto** (Fabian) – `stamp.py` vloží razítko do pole „předávajícího“.
4. **Vyúčtování pro Fabiana** – `parse.py` → `data.json`, pak `vyuctovani_cz.py` / `vyuctovani_en.py`.
   Podmínky Fabian: spoluúčast za každou PU: oprava pod 10 000 Kč = orientační cena + 21 % (max. 10 000), jinak 10 000 Kč (počet PU dle HAVEX protokolu); škody v oddílu A (hradí nájemce) = cena dle HAVEX + 21 %; nadlimitní km 7 Kč bez DPH.
   Datum dokladu = datum HAVEX protokolu. Při zpětném datu nastavit splatnost min. 10 dní od dneška (jinak hned odejdou automatické upomínky).
   Pozor: parse.py nenačte položku PU, jejíž částka je na řádku nad popisem (9H06057) – vždy porovnat počet PU s „Spoluúčast hrazená klientem“.
   Razítko (`data/razitko_rx.pdf`) lze v nouzi vyříznout z dříve odeslaného „Damage statement“: v DS je razítko+podpis v oblasti cca 407,237,540,277 (pt); přeložit na stránku tak, aby padlo do 220,611,345,651 (to očekávají stamp.py i vyuctovani_*.py).
5. **Faktury Fabianovi** – Vyfakturuj, přenesená daňová povinnost, CZK, popis CZ+EN „vyúčtování po vrácení vozidla“.
   Rychle: formulář kopie poslední Fabian faktury (`/faktury/crud/<id>/kopie/`, např. 13313741 = FA 20262074) – v přihlášené záložce
   načíst fetchem, nahradit `crud[items][*][]` (count/mj/text/price/data/vatRate=0/vatRateType=32) a POSTnout FormData; číslo a csrf se berou z čerstvě načteného formuláře.
   Položky: škody (A × 1,21), spoluúčast (n× PU), nadlimitní km (km × 7 Kč). Splatnost 22 dní.
   PDF faktury: `public.vyfakturuj.cz` je pro curl (cloud i Mac) blokované – stáhnout v záložce Vyfakturuj fetchem jako blob a `a.download` (uloží do ~/Downloads).
   E-mail Fabianovi: z faktury@ na penzugy@fabianautomotive.hu, cc daniel.pszota@fabianautomotive.hu; přílohy faktura + Damage statement + „RZ Vehicle inspection protocol with photos.pdf“ (= ProtokolKontroly).
   Beyrovi: odpověď do jeho vlákna z erik@ s `RZ Protokol o vraceni vozidla - podepsano.pdf`.
   Kooperativa (Gieselová): tabulka `Ukonceni_PS_Kooperativa_<datum>.xlsx` + protokoly `RZ.pdf`; čísla PS z DETAIL_PREDPIS xlsx (e-mail „Předpis pojistného … 6667100466“).
6. **Renteon** – RX vozy deaktivovat aktivitou „Deaktivace vozu“ (def. 121) s neaktivním stavem 31 = „Koupit zpět – pronájem“ (buyback lease), ne 32 (subrent). Fabian vozy v Renteonu nejsou.
7. **Ukončení pojistek** – Kooperativa (Gieselová) / Generali (Herrmann); pojišťovnu určit z výpisu Kooperativy (předpis pojistného, CSV) a vyúčtování flotily Generali.

## Spuštění
```
python3 parse.py data/data.json data/*"Protokol o vraceni vozidla.pdf"
python3 vyuctovani_cz.py data/data.json output/ data/razitko_rx.pdf
python3 vyuctovani_en.py data/data.json output/ data/razitko_rx.pdf
```
Protokoly, razítko a výstupy patří do `data/` a `output/` (necommitují se).

## Náklady vs. výnosy po vrácení
`naklady_vs_vynosy.py output/vysledek.xlsx data/` – vstupy v `data/`: `all.json` (parse.py ze všech protokolů), `vyf.json` (Fabian: nájem CZK, škody, pokuty z Vyfakturuj), `renteon.json` (RX: RentIncome/TotalIncome bez DPH z `/cs/api/report/getIncomeAndExpenseComparison`, Type car, IncomeType 2), `contracts.json` (RZ → smlouva HAVEX), `insurance.json` (RZ → měsíční pojistné HAV, počátek, smlouva; Kooperativa = DETAIL_PREDPIS xlsx z e-mailu „Předpis pojistného“, Generali = report vyúčtování RS 4785635732).
Nájem HAVEX = splátka × měsíce smlouvy (+ splátka/30 × dny prodloužení); sazby z e-mailů „Přehled zápůjček“ / platebních kalendářů. Předčasné vrácení nájem nesnižuje. Pojištění HAV platí RX (POV je ve splátce HAVEX) – počítá se předpis × 12/365 × dny do vrácení.
Fabian se fakturuje měsíčně (25.–24., 31.–30., 17.–16. nebo 30.–29. podle vozu, EUR); když vůz vrátí po konci posledního fakturovaného období, dofakturovat dny do vrácení (sazba/30 × dny).
