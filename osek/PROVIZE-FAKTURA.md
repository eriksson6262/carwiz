# OSEK – měsíční faktura za provizi (Carwiz PRG)

Fakturuje se za **předchozí měsíc** z reportu Closed agreements od Mateusze Oseka (mail „Report“, viz `mzdy/POSTUP.md`).

## Kde vzít čísla
List měsíce (např. `SEP 26`), souhrnný blok vpravo (nad blokem `dkasovsky`):
- **pick up + drop off** – celkový počet (např. `AB101`) → počet mytí
- **TOTAL Netto** (např. `AC102`) → zprostředkování (zaokrouhlit na 2 des. místa)

## Faktura ve Vyfakturuj
Vytvořit **kopií poslední provizní faktury** OSEK Group s.r.o. (Detail → Možnosti → Vytvořit kopii dokladu, `/faktury/crud/<id>/kopie/`). Odběratel OSEK Group s.r.o., IČO 19581025, splatnost 10 dní, ceny bez DPH, 21 %.

| Počet | Text | Cena za MJ |
|---|---|---|
| počet pickupů | mytí exterier (car wash) | 299 Kč |
| 2 ks | parkování | 5 900 Kč |
| 1 ks | zprostředkování | TOTAL Netto |

Text před položkami = období `MM/YY`. Datum vystavení = DUZP = dnešek.
Poslední vzory: FA 20261457 (07/26), FA 20261631 (08/26).
