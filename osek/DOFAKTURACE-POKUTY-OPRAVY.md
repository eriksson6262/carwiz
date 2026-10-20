# OSEK – kontrola a dofakturace pokut, oprav a spoluúčastí

Auta pro OSEK Group s.r.o. (IČO 19581025) jsou od HAVEX Mobility a AUTOCENTRUM Jičín. Jejich náklady se přefakturují ve Vyfakturuj.

## Zdroje
- **Vyfakturuj**: seznam faktur OSEK přes `POST /system/ajax/invoices/` (filtr `vfiSearch=osek`, `dateFromTo=01.01.2010|31.12.2026`, stránkování parametrem `page`), položky z `/faktury/detail/<id>/` (občas vrátí 500 → zopakovat).
- **HAVEX pokuty**: Spark `faktury@rxauto.cz`, předmět `<RZ>_..._dopravní přestupek_Doklad č. 5/RRRR/NNNN`.
  - `5RRRRNNNN .pdf` = faktura HAVEX (jen číst, **nikdy nepřikládat**).
  - `<RZ>_<datum>_..._priloha_fa_dodavatel_N.pdf` = výzva úřadu, ta se přikládá.
  - Spark má HAVEX poštu jen cca od 9/2025; starší doklady jsou v Gmailu rxpokuty (vyhledávání indexuje text PDF).
- **Jičín opravy po PU**: faktury 2211xxxxxx. Faktury Jičína se nepřikládají.
- **Spoluúčast na OSEK: vždy 10 000 Kč za každou pojistnou událost (PU Kooperativa), 0 % DPH** – bez ohledu na skutečnou spoluúčast u pojišťovny (pokyn Erika 20.10.2026).

## Párování
- Datum přestupku samotné nestačí, ověřit i částku. U zahraničních pokut je částka OSEK často = pokuta HAVEX + 250 Kč.
- Řádky faktur OSEK „bez data“ (06–07/2025) párovat podle RZ, částky a data vystavení.
- Pozor na dobropisy HAVEX (např. 5/2026/510 storno duplicity 5/2026/452).

## Fakturace
- Pokuta: kopie poslední pokutové faktury (`/faktury/crud/<id>/kopie/`), položky „Fakturujeme Vám dopravní přestupek ze dne D.M.RRRR SPZ: XXX“ (0 %) + „Administrativní poplatek“ 400 Kč (21 %), splatnost 10 dní.
- Spoluúčast: kopie FA 20261883, text s číslem PU Kooperativa, 0 %.
- Servis mimo služby (HAVEX): kopie FA 20261286, 21 %.
- Předmět e-mailu „Faktura č. X a pokuta“. Přílohy: výzva úřadu / protokol o poškození (`protokol_poskozeni.py`). Nikdy faktury HAVEX ani Jičína.
- Vyfakturuj neumí přiložit soubor z kontejneru → PDF faktury stáhnout v prohlížeči (`public.vyfakturuj.cz/export/document/<kód>/?download=1` → `~/Downloads`), podklady zapsat do `~/Downloads/Claude pracovní/OSEK dofakturace RRRR-MM/` a odeslat přes Spark z faktury@rxauto.cz na mateusz.osek@osekrent.pl (kopie erik@rxauto.cz).
