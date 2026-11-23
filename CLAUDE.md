# RX Auto – projekty

Privátní repozitář s veškerou prací Claude pro RX Auto, s.r.o. (Carwiz, Carnetto) a RX Auto SK s.r.o.
Komunikace česky, stručně, kompletní výstupy bez zbytečných otázek.

## Struktura
Každý projekt má vlastní složku. Do ní patří skripty, šablony, konfigurace a postupy.

| Složka | Obsah |
|---|---|
| `renteon/` | Renteon – ceníky (`renteon/ceniky/`), výnosy a flotila (`renteon/vynosy-flotila/`), hromadné faktury, reklamace plateb, škody, flotila, e-maily Carwiz |
| `renteon/zimni-pneu/` | Přehled vozidel na zimní pneu (Renteon CZ+SK + pravidelné faktury Vyfakturuj) |
| `renteon/kanaly-rezervace/` | Kanály rezervací – mix brokerů vs přímé, výnos/den, doplňky, storna, vytíženost (CZ+SK) |
| `renteon/havex-zpetna/` | Zpětná fakturace HAVEX – přehled zápůjček vs. faktury Vyfakturuj, nevyfakturovaná auta |
| `renteon/naklady-vynosy/` | Náklady vs výnosy půjčovny – leasing, Carnetto přefakturace, pojištění, servisy po pobočkách a SPZ |
| `renteon/kontakty-bez-skod/` | Export kontaktů klientů bez účtované škody a pokuty (Renteon CZ+SK) |
| `rxauto-ig/` | Instagram/Facebook RX Auto (Metricool, Canva) |
| `osek/` | OSEK – úroky z prodlení, měsíční faktura za provizi |
| `havex/` | HAVEX Mobility – fakturace ve Vyfakturuj, pravidelné faktury |
| `generator-smluv/` | Lokální generátor nájemních smluv (localhost:8765) |
| `linktree/` | Carwiz/Carnetto linktree web app |
| `datove-schranky/` | Automatizace čtení datové schránky (ISDS API) |
| `fleet-dokumenty/` | SOSBK, vinkulace, plné moci, nájemní smlouvy – šablony a generátory |
| `pokuty/` | Zpracování a přefakturace pokut |
| `rxauto-sk/` | Landing page rxauto.sk |
| `rxauto-web/` | Web rxauto.cz (Wix) – CMS kolekce Auta/Karavany/Motorky, konsolidace nabídky vozidel |
| `common/` | Sdílené – přihlašovací údaje pro skripty (`rxauto_config.py`, Keychain / `~/.rxauto.env`) |
| `mzdy/` | Měsíční bonusy zaměstnanců (provize Renteon, noční výpůjčky, pickupy) |
| `team-leader/` | Team Leader skill – workflow mapy (WF1–WF5), routovací pravidla, eskalace |

Nový projekt = nová složka + řádek do tabulky výše.

## Git – povinné
- Na začátku práce repo připoj (add_repo `eriksson6262/carwiz`, access push) a naklonuj.
- Po každé dokončené změně **automaticky commitni a pushni na `main`**, bez ptaní.
- Commit zpráva česky: co a proč. Prefix složkou, např. `renteon: oprava výpočtu sezónní přirážky`.
- Před pushem `git pull --rebase`, konflikty vyřeš sám.

## Autonomie a soubory – Google Drive (povinné pro všechny projekty a agenty)
- Úkoly zpracuj **autonomně až do konce** (včetně uložení a odeslání, které Erik zadal). Neptej se, kam uložit, a nekonči hláškou „nejde uložit / nejde přiložit“ – použij postup níže.
  Zastav se jen u toho, co opravdu nejde bez Erika: hesla a přihlášení, platby, nevratné rozhodnutí, které může dopadnout dvojím způsobem.
- **Úložiště = Google Drive `xpeerik@gmail.com`**, složka `RX Auto Claude/` (`vstupy`, `vystupy`, `predavaci-protokoly`, `faktury`, `vinkulace`, `sosbk`, `pokuty`, `vyuctovani`, `prehled-zapujcek`). Nové složky zakládej uvnitř ní, ne v kořeni Drive.
- **Uložení:** konektor Google Drive (`create_file`, `base64Content` = `sha256:<hash>:<abs. cesta>`, limit ~3 MB na soubor).
- **Příloha e-mailu (Spark):** soubor nejdřív nahraj na Drive, pak ho přilož cestou synchronizované složky na Mac mini:
  `/Users/rxautoagentai/Library/CloudStorage/GoogleDrive-xpeerik@gmail.com/Můj disk/RX Auto Claude/<podsložka>/<soubor>`
  **Pozor:** „Můj disk“ je na disku v rozloženém Unicode (NFD) – v cestě piš `Mu\u030aj disk` (u + kombinující kroužek), s předsloženým „ů“ Spark soubor nenajde. Po nahrání chvíli počkej na synchronizaci a při „file not found“ zkus znovu.
  Nevyžaduje připojenou složku v chatu – Spark čte disk Macu sám. Ověřeno 23. 11. 2026.
- `device_bash` složku `RX Auto Claude` přes mount nepřečte („Resource deadlock avoided“); jiné složky Drive ano. Na čtení/zápis proto používej konektor Drive, lokální cestu jen pro přílohy.
- Příjemci bez Google účtu odkaz na Drive neotevřou – posílej soubor jako přílohu, ne odkaz.
- Soubory s osobními údaji patří na Drive, nikdy do repa.

## Co nikdy necommitovat
- Hesla, API klíče, tokeny, `.env` soubory. Skripty berou údaje přes `common/rxauto_config.py`, nikdy natvrdo v kódu.
- Osobní údaje klientů: RČ, čísla dokladů, vyplněné smlouvy, protokoly, exporty z Renteonu se zákazníky.
- Vstupní a výstupní data patří do `data/` nebo `output/` v dané složce – obojí je v `.gitignore`.
- Když si nejsi jistý, jestli soubor obsahuje osobní údaje, necommituj ho a zeptej se.
