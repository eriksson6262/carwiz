# Generátor dlouhodobé nájemní smlouvy (B2B)

Generuje Word (.docx) dlouhodobou nájemní smlouvu o nájmu dopravního prostředku
pod Carnetto RX s.r.o. pro B2B klienty.

## Použití

```bash
python3 gen_najemni_smlouva.py smlouva.json vystup.docx
```

JSON soubor obsahuje všechny konkrétní údaje (viz `najemni-smlouva.example.json`
jako šablonu). **Nikdy necommituj vyplněné JSONy** – osobní údaje klientů
patří na Google Drive (`RX Auto Claude/smlouvy-najemni/`), ne do repa.

## Struktura dokumentu

- I. Smluvní strany (Carnetto RX + nájemce)
- II. Předmět nájmu (vozidlo – model, SPZ, VIN, palivo)
- III. Doba nájmu
- IV. Nájemné a platební podmínky (cena bez DPH + výpočet s DPH 21 %)
- V. Předání a vrácení vozidla
- VI. Práva a povinnosti nájemce
- VII. Pojištění a odpovědnost za škodu
- VIII. Ukončení smlouvy
- IX. Závěrečná ustanovení

Měsíční cena s DPH se dopočítává automaticky (bez DPH × 1,21), stejně tak
celková částka za celou dobu nájmu.

Data `od` a `do` zapisuj ve formátu `YYYY-MM-DD` – skript je převede na český
textový formát ("27. listopadu 2026").
