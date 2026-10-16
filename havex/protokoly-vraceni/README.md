# HAVEX – protokoly o vrácení vozidel (Petr Beyr)

Zpracování protokolů o vrácení vozidel, které posílá HAVEX Mobility (petr.beyr@havexmobility.cz).

## Postup
1. **Stažení** – Spark: `from:petr.beyr@havexmobility.cz after:<datum>`. Každé vozidlo má „Protokol o vrácení vozidla“ + „ProtokolKontroly“ (fotky), někdy „Kilometry“.
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
   Podmínky Fabian: spoluúčast paušálně 10 000 Kč za každou PU (počet PU dle HAVEX protokolu), nadlimitní km 7 Kč bez DPH.
   Datum dokladu = datum HAVEX protokolu.
5. **Faktury Fabianovi** – Vyfakturuj, přenesená daňová povinnost, CZK, popis CZ+EN „vyúčtování po vrácení vozidla“.
6. **Ukončení pojistek** – Kooperativa (Gieselová) / Generali (Herrmann); pojišťovnu určit z výpisu Kooperativy (předpis pojistného, CSV) a vyúčtování flotily Generali.

## Spuštění
```
python3 parse.py data/data.json data/*"Protokol o vraceni vozidla.pdf"
python3 vyuctovani_cz.py data/data.json output/ data/razitko_rx.pdf
python3 vyuctovani_en.py data/data.json output/ data/razitko_rx.pdf
```
Protokoly, razítko a výstupy patří do `data/` a `output/` (necommitují se).
