# Mzdy – měsíční bonusy Tomáš Svačinka a Dan Kašovský

Bonus se počítá vždy za **předchozí měsíc** (v říjnu se dělá září).

## Složky bonusu

| Složka | Zdroj | Sazba |
|---|---|---|
| Provize z doplňkového prodeje | Renteon → Přehledy → Odbyt → **Doplňkový prodej** (`#/report/sales/additionalSales`), přednastavený „Předchozí měsíc“, Export do Excelu; list „Doplňkový prodej“, sloupec **TotalServiceBonusAmount** | dle Renteonu |
| Noční výpůjčky | Sdílená poznámka Erika v iPhonu (nadpis = měsíc, sekce **Carwiz** a **ACE**); každá čárka = 1 noční výpůjčka. Sečíst Carwiz + ACE na osobu | 600 Kč / ks |
| Pickupy | Soubor `Closed_agreements_2024_Prague_updated_*.xlsx`, list daného měsíce (např. `SEP 26`); počet smluv (`PRG-…`) se sloupcem **AgentOut** = `tsvacinka` / `dkasovsky` | 240 Kč / ks |

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
