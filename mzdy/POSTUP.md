# Mzdy – měsíční bonusy Tomáš Svačinka a Dan Kašovský

Bonus se počítá vždy za **předchozí měsíc** (v říjnu se dělá září).

## Složky bonusu

| Složka | Zdroj | Sazba |
|---|---|---|
| Provize z doplňkového prodeje | Renteon → Přehledy → Odbyt → **Doplňkový prodej** (`#/report/sales/additionalSales`), přednastavený „Předchozí měsíc“, Export do Excelu; list „Doplňkový prodej“, sloupec **TotalServiceBonusAmount** | dle Renteonu |
| Noční výpůjčky | Fotka sdílené poznámky (nadpis = měsíc, sekce **Carwiz** a **ACE**), kterou kluci posílají do WhatsApp skupiny **PRG** (číst přes WhatsApp Web v Chromu); každá čárka = 1 noční výpůjčka. Sečíst Carwiz + ACE na osobu | 600 Kč / ks |
| Pickupy | Měsíční mail od **Mateusze Oseka** (`mateusz.osek@osekrent.pl` → `erik@rxauto.cz`, předmět „Report“, chodí kolem 13. v měsíci; najdeš ve Sparku filtrem `from:mateusz.osek@osekrent.pl`), příloha `Closed agreements 2024 Prague updated -NN.xlsx`; list daného měsíce (např. `SEP 26`); počet smluv (`PRG-…`) se sloupcem **AgentOut** = `tsvacinka` / `dkasovsky` | 240 Kč / ks |

Login v Renteonu: Tomáš = `tsvacinka`, Dan = `dkasovsky`.

## Výpočet

```
bonus = TotalServiceBonusAmount + noci × 600 + pickupy × 240
```

## Poznámky
- Export z Renteonu jde stáhnout i bez souboru: v záložce Renteonu přes angular `$http.post('/cs/api/report/getAdditionalSalesExcel', {IsByDateOut:false, DateFrom:'01.MM.YYYY.', DateTo:'DD.MM.YYYY.'}, {responseType:'arraybuffer'})` a rozparsovat SheetJS.
- Report „Na konci“ (IsByDateOut=false) = podle data vrácení, stejně jako closed agreements.
- Pro čárky v poznámce platí číslo napsané za čárkami.
- Do repa nikdy neukládat konkrétní částky ani exporty (osobní/mzdové údaje) – jen postup.

---

# Mzdy – Carwiz SK (Bratislava, BTS)

Bonus za **předchozí měsíc** pro BTS tým (Peter Remeš, Slavo, Miro Bednár).

| Složka | Zdroj | Sazba |
|---|---|---|
| Provize z doplňkového prodeje | SK Renteon `https://cwslovakia.s6.renteon.com/sk/#/report/sales/additionalSales` (Doplnkový predaj), předchozí měsíc, list „Doplnkový predaj“, sloupec **TotalServiceBonusAmount** (EUR) | dle Renteonu |
| Odpracované hodiny | Píše Erik každý měsíc | 8 € / h |

```
bonus = TotalServiceBonusAmount + hodiny × 8 €
```

- Kdo v reportu nemá řádek (nic neprodal), má provizi 0.
- Export stejně jako u CZ: angular `$http.post('/sk/api/report/getAdditionalSalesExcel', {IsByDateOut:false, DateFrom, DateTo}, {responseType:'arraybuffer'})` + SheetJS. Přihlášení drží vestavěný prohlížeč Claude desktop appky.
