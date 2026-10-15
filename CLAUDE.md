# RX Auto – projekty

Privátní repozitář s veškerou prací Claude pro RX Auto, s.r.o. (Carwiz, Carnetto) a RX Auto SK s.r.o.
Komunikace česky, stručně, kompletní výstupy bez zbytečných otázek.

## Struktura
Každý projekt má vlastní složku. Do ní patří skripty, šablony, konfigurace a postupy.

| Složka | Obsah |
|---|---|
| `renteon/` | Renteon – ceníky, hromadné faktury, reklamace plateb, škody, flotila, e-maily Carwiz |
| `rxauto-ig/` | Instagram/Facebook RX Auto (Metricool, Canva) |
| `osek/` | OSEK – úroky z prodlení, měsíční faktura za provizi |
| `havex/` | HAVEX Mobility – fakturace ve Vyfakturuj, pravidelné faktury |
| `generator-smluv/` | Lokální generátor nájemních smluv (localhost:8765) |
| `linktree/` | Carwiz/Carnetto linktree web app |
| `datove-schranky/` | Automatizace čtení datové schránky (ISDS API) |
| `fleet-dokumenty/` | SOSBK, vinkulace, plné moci, nájemní smlouvy – šablony a generátory |
| `pokuty/` | Zpracování a přefakturace pokut |
| `rxauto-sk/` | Landing page rxauto.sk |
| `common/` | Sdílené – přihlašovací údaje pro skripty (`rxauto_config.py`, Keychain / `~/.rxauto.env`) |
| `mzdy/` | Měsíční bonusy zaměstnanců (provize Renteon, noční výpůjčky, pickupy) |

Nový projekt = nová složka + řádek do tabulky výše.

## Git – povinné
- Na začátku práce repo připoj (add_repo `eriksson6262/carwiz`, access push) a naklonuj.
- Po každé dokončené změně **automaticky commitni a pushni na `main`**, bez ptaní.
- Commit zpráva česky: co a proč. Prefix složkou, např. `renteon: oprava výpočtu sezónní přirážky`.
- Před pushem `git pull --rebase`, konflikty vyřeš sám.

## Co nikdy necommitovat
- Hesla, API klíče, tokeny, `.env` soubory. Skripty berou údaje přes `common/rxauto_config.py`, nikdy natvrdo v kódu.
- Osobní údaje klientů: RČ, čísla dokladů, vyplněné smlouvy, protokoly, exporty z Renteonu se zákazníky.
- Vstupní a výstupní data patří do `data/` nebo `output/` v dané složce – obojí je v `.gitignore`.
- Když si nejsi jistý, jestli soubor obsahuje osobní údaje, necommituj ho a zeptej se.
