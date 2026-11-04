# E-mail poděkování + recenze + promo kód (CZ klienti)
- Pořadí v e-mailu: poděkování → odkaz + QR na Google recenzi Praha → Ostrava → promo kód Hello15 jako poděkování (není podmíněn recenzí).
- Odkazy na recenze: Praha `https://search.google.com/local/writereview?placeid=ChIJB1wGNgC_C0cRKbo9YP8VwGw`,
  Ostrava `https://search.google.com/local/writereview?placeid=ChIJuQa_GNDvE0cRxRANm1CsvVs`.
- Šablony email_EN.html / email_CZ.html používají merge tagy Brevo ({{ contact.FIRSTNAME }}, {{ unsubscribe }}); QR_PRAHA_URL / QR_OSTRAVA_URL nahradit URL nahraných obrázků.
- Jazyk: CZ pro .cz/.sk adresy, jinak EN. Vyřazeny podezřelé a proxy e-maily brokerů.
- Rozesílka: Brevo (Mailchimp free = jen 250 kontaktů). Data (CSV) necommitovat.
QR a CSV generuje make.py na Macu ve složce případu.

## Klienti z Vyfakturuj (RX Auto, s.r.o.) – 5.11.2026
- Adresář: `fetch('/adresar/?action=downloadCSV')` (přihlášený app.vyfakturuj.cz).
- Faktury s položkami: POST `/exporty/hromadny-export/` (formulář ze stránky, `exportFileType=json`) po měsících (víc najednou nevrátí soubor); data od 08/2020.
- Vyloučit odběratele (id_customer i e-mail) s nestornovanou fakturou, jejíž položka obsahuje pokut|přestup|administrativní poplatek|škody|poškoz|spoluúčast (pozor: „Škoda“ = značka).
- Vyřadit partnery (HAVEX, OSEK, Carwiz, Carnetto, HoppyGo, 1CAR, ALD…) a kontakty bez e-mailu. Výsledek 188 kontaktů.
- Šablona `email_VF_RXAuto_CZ.html` = CZ šablona přebrandovaná na RX Auto (podpis, rxauto.cz), stejné odkazy na recenze Praha/Ostrava a kód Hello15.
