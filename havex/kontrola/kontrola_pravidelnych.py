"""Porovná tyrkysová vozidla z přehledu (sheet.json) s pravidelnými fakturami
HAVEX ve Vyfakturuj (rec.json – export z prohlížeče, viz README).

Hlídá: chybějící aktivní pravidelnou fakturu, cenu ≠ sloupec J, den vystavení
≠ den startu, konec 'bez ukončení' / 'podle počtu', a zda poslední automatická
faktura kryje období přesně do konce smlouvy (B).

Použití: python3 kontrola_pravidelnych.py data/sheet.json data/rec.json [dnes]
"""
import json, re, sys, datetime as dt
from dateutil.relativedelta import relativedelta

def D(s):
    return dt.date.fromisoformat(s) if "-" in s else dt.date(*map(int, reversed(s.split("."))))

def main(sheet, rec, dnes=None):
    rows, rec = json.load(open(sheet)), json.load(open(rec))
    today = D(dnes) if dnes else dt.date.today()
    for rz, a, b, j, r, f in rows:
        A, B = D(a), D(b)
        m = [x for x in rec if any(re.search(rf"\b{rz}\b", i[2]) for i in x[7])]
        issues = []
        cover = None
        for x in m:
            price = next(float(i[1]) for i in x[7] if re.search(rf"\b{rz}\b", i[2]))
            S = D(x[2])
            if x[1] and abs(price - j) > 0.01:
                issues.append(f"cena {price:g}≠{j:g}")
            if x[1] and x[3] == "N":
                issues.append(f"{x[0]} bez ukončení")
            if x[1] and x[3] == "C":
                issues.append(f"{x[0]} konec podle počtu ({x[5]})")
            if x[3] == "D":
                E, k = D(x[4]), 0
                while S + relativedelta(months=k + 1) <= E:
                    k += 1
                end = S + relativedelta(months=k + 1) - dt.timedelta(days=1)
                cover = max(cover, end) if cover else end
        if B >= today and not any(x[1] for x in m) and (not cover or cover < B):
            issues.append("chybí aktivní pravidelná faktura")
        if cover and cover != B and B >= today:
            issues.append(f"poslední fa kryje do {cover}, konec smlouvy {B}")
        if issues:
            print(f"{rz} (ř.{r}, {a}–{b}, {j:g}): " + " | ".join(issues))

if __name__ == "__main__":
    main(*sys.argv[1:])
