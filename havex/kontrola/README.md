# Kontrola fakturace HAVEX vs. přehled zápůjček

1. `python3 tyrkys_vozy.py prehled.xlsx > data/sheet.json` – tyrkysová vozidla (sloupec E) s A/B/J.
2. Export pravidelných faktur z Vyfakturuj (built-in browser, přihlášený účet):
   - `/faktury/pravidelne-faktury/`, filtr „Vše“, projet stránky přes `Data_filter.loadPage(p,1)`
     a posbírat `input[name="groupOperation[]"]` (ID).
   - Každé ID: `fetch('/faktury/crud-pravidelne/<id>/')`, číst `crud[odberatelSearch]`, `crud[vfpName]`,
     `crud[-form-::date::vfpDateStart]`, `crud[vfpRepeatType]`, `crud[-form-::date::vfpDateEnd]`,
     `crud[vfpRepeatCount]`, `crud[items][count|price|text][]`. Max ~6 požadavků paralelně
     (víc → server vrací stránky bez formuláře), s opakováním.
   - Aktivní = ID z filtru „Aktivní“.
   - Formát `rec.json`: `[id, aktivni(1/0), start, D|N|C, konec, pocet, perioda, [[ks, cena, text], ...]]`.
3. `python3 kontrola_pravidelnych.py data/sheet.json data/rec.json`
4. Vystavené faktury: `/faktury/crud/<id>/` má stejná pole `crud[items]…` – podle nich ověřit doplatky
   (součet měsíců × J vs. počet cyklů od startu).
