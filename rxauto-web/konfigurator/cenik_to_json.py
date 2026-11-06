"""Převede cenik_konfigurator.xlsx na JSON pro CMS kolekce konfigurátoru (KonfiguratorVozy, KonfiguratorNastaveni, KonfiguratorSpoluucast)."""
import json, sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1] if len(sys.argv) > 1 else "cenik_konfigurator.xlsx", data_only=True)
v = wb["Vozy"]; vozy = []
for i, r in enumerate(v.iter_rows(min_row=4, values_only=True)):
    if not r[0]: break
    yes = lambda x: str(x or "").strip().lower() == "ano"
    vozy.append({"title": r[0], "znacka": r[1], "cenaMesic": r[2], "kmVCene": r[3], "kategorieSpoluucasti": r[4],
                 "sippCz": r[5] or "", "sippSk": r[6] or "", "prg": yes(r[7]), "osr": yes(r[8]), "bts": yes(r[9]),
                 "maxMesice": r[10] if isinstance(r[10], (int, float)) else None, "aktivni": yes(r[11]), "poznamka": r[12] or "", "popisWeb": (r[13] if len(r) > 13 else "") or "", "servisVCene": yes(r[14]) if len(r) > 14 and r[14] else True, "skupina": (r[15] if len(r) > 15 else "") or "Osobní auta", "modelovyRok": r[16] if len(r) > 16 and isinstance(r[16], (int, float)) else None, "neomezenyPriplatek": r[17] if len(r) > 17 and isinstance(r[17], (int, float)) else None, "poradi": i + 1})
p = wb["Parametry"]; keys = ["dniVMesici", "minDniPronajmu", "kmVCene", "krokKm", "cenaKrok", "ridicDen", "ridicZdarmaOd", "dph", "kratkodobyKoef", "zakladMesice", "priplatekZaMesic"]
nast = [{"title": k, "hodnota": p.cell(4 + i, 2).value, "popis": p.cell(4 + i, 1).value} for i, k in enumerate(keys)]
s = wb["Spoluúčast"]; spol = []
for r in s.iter_rows(min_row=5, max_row=10, values_only=True):
    spol.append({"title": r[0], "popis": r[1], "priplatek5": r[3], "priplatek0": r[4]})
km = [r[0] for r in wb["Nájezd"].iter_rows(min_row=5, values_only=True) if r[0]]
nast.append({"title": "najezdy", "hodnotaText": ",".join(str(k) for k in km), "popis": "Nabízené nájezdy km/měsíc"})
print(json.dumps({"vozy": vozy, "nastaveni": nast, "spoluucast": spol}, ensure_ascii=False))
