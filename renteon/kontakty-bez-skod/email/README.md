# E-mail poděkování + recenze + promo kód (CZ klienti)
- Pořadí v e-mailu: poděkování → odkaz + QR na Google recenzi Praha → Ostrava → promo kód Hello15 jako poděkování (není podmíněn recenzí).
- Odkazy na recenze: Praha `https://search.google.com/local/writereview?placeid=ChIJB1wGNgC_C0cRKbo9YP8VwGw`,
  Ostrava `https://search.google.com/local/writereview?placeid=ChIJuQa_GNDvE0cRxRANm1CsvVs`.
- Šablony email_EN.html / email_CZ.html používají merge tagy Brevo ({{ contact.FIRSTNAME }}, {{ unsubscribe }}); QR_PRAHA_URL / QR_OSTRAVA_URL nahradit URL nahraných obrázků.
- Jazyk: CZ pro .cz/.sk adresy, jinak EN. Vyřazeny podezřelé a proxy e-maily brokerů.
- Rozesílka: Brevo (Mailchimp free = jen 250 kontaktů). Data (CSV) necommitovat.
QR a CSV generuje make.py na Macu ve složce případu.
