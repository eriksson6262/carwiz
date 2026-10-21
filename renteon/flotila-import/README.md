# Import nových vozidel do Renteonu (přes interní API v prohlížeči)

Rychlejší než Cars.xlsx import. Spouští se v přihlášeném Renteonu (rxauto.s3.renteon.com)
v konzoli prohlížeče – `import_vozidel.js`. Bez hesel, používá session přihlášeného uživatele.

## Postup
1. Přihlásit se do Renteonu (CZ instance).
2. Doplnit pole `CARS` (SPZ, VIN, pobočka P/O, typ) a parametry nahoře ve skriptu
   (buyback, opening day, poznámka, inventurní číslo od).
3. Vložit skript do konzole → vytvoří kartu vozu (`POST /api/car`)
   a aktivitu „Otevření karty automobilu“ (def. 109, `POST /api/carActivity`) s pobočkou,
   datem, tachometrem a nádrží.
4. Po otevření karty přejde vůz do stavu Idle („NEAKTIVNÍ“ v CZ překladu = volný).

## ID (CZ Renteon)
| Co | ID |
|---|---|
| Pobočka Praha (PRG) / Ostrava (OSR) | 25 / 26 |
| Flotila „Pronájem vozového parku“ | 7 |
| Dodavatel/vlastník EURO FLEET SERVIS s.r.o. (ACJC) | 349779 |
| HAVEX (dodavatel/vlastník) | 1303 |
| Barva Vícebarevný (Multicolor) | 12 |
| Palivo benzín / nafta | 1 / 2 |
| Aktivita Otevření karty automobilu | 109 |

## Modely podle VIN prefixu (jak jsou ve flotile)
| VIN prefix | Model | ModelId | CategoryId |
|---|---|---|---|
| TMBGK6NW / TMBGR6NW | Kamiq AT | 871 | 222 |
| TMBJR7NU (TSI) / TMBLJ7NU (TDI) | Karoq SportLine | 619 | 1168 |
| TMBJR8NX | Octavia Combi IV Sportline AT | 2075 | 214 |
| TMBLN9PS / TMBJJ9PS | Kodiaq II Sportline AT | 2255 | 231 |
| TMBJH8NZ / TMBJN8NZ | Superb Combi AT | 623 | 218 |

## Nádrž
Renteon dělí nádrž na 8 dílků: 1/8 = `FuelTankSectionIn: 1`, litry = round(objem/8).
