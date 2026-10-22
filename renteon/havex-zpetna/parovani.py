#!/usr/bin/env python3
"""Zpětná fakturace HAVEX: co mělo být vyfakturováno (přehled zápůjček, sloupec „K fakturaci zpět na CC“) vs. co je
ve Vyfakturuj RX Auto CZ na odběratele HAVEX Mobility. Vstup: data/vozy.pkl (list Vozy), data/havex_polozky.csv.
Párování položek: podle SPZ v textu; položky bez SPZ (2021–2022) podle částky (= k násobků měsíční částky) a dne začátku období.
Výstup: output/nevyfakturovano.csv (po smlouvách), output/obdobi.csv (po obdobích)."""
import re, datetime as dt, calendar, pathlib
import pandas as pd
B = pathlib.Path(__file__).parent
STOP = dt.date(2026, 9, 1)          # období začínající po tomto dni se ještě nepočítá (přehled k 30. 9. 2026)
d = pd.read_pickle(B / 'data/vozy.pkl'); d = d[d.zpet > 0].copy()
it = pd.read_csv(B / 'data/havex_polozky.csv')
SPZ = re.compile(r'\b(\d[A-Z][A-Z0-9]\s?[A-Z0-9]\d{3}|[A-Z]{2}\d{3}[A-Z]{2})\b')   # i nové 1AD L159
it = it.fillna({'hlavicka': '', 'text': ''})
spz_of = lambda t: list(dict.fromkeys(x.replace(' ', '') for x in SPZ.findall(str(t))))

# šablony pravidelných faktur (data/sablony.csv, všechny vč. ukončených) – SPZ z názvu/textu šablony, cena bez DPH
def sablony():
    f = B / 'data/sablony.csv'
    if not f.exists(): return pd.DataFrame(columns=['cena', 'den', 'start', 'spz'])
    t = pd.read_csv(f, dtype=str).fillna(''); t = t[t.odberatel.str.contains('HAVEX', case=False)]
    rows = []
    for r in t.itertuples():
        tx, ce, nm = r.texty.split(' ## '), r.ceny.split(';'), spz_of(r.nazev)
        for k, (x, c) in enumerate(zip(tx, ce)):
            sp = spz_of(x) or ([nm[k]] if len(nm) == len(tx) else nm)
            den = re.match(r'\D*(\d{1,2})\.', x)
            rows.append(dict(cena=float(c or 0), den=int(den.group(1)) if den else int(r.start[:2]),
                             start=dt.datetime.strptime(r.start, '%d.%m.%Y').date(), spz=sp))
    return pd.DataFrame(rows)
TPL = sablony()
def spz_sablona(castka, start, duzp):
    c = TPL[(abs(TPL.cena - castka) <= 1) & (TPL.start <= duzp + dt.timedelta(days=31))]
    if start is not None and len(c): c = c[c.den == start.day] if (c.den == start.day).any() else c
    return list(dict.fromkeys(x for l in c.spz for x in l))

def addm(x, n=1):
    y, m = x.year + (x.month - 1 + n) // 12, (x.month - 1 + n) % 12 + 1
    return dt.date(y, m, min(x.day, calendar.monthrange(y, m)[1]))

per = []
for i, r in d.iterrows():
    z = r.zac.date(); k = r.kon.date() if hasattr(r.kon, 'date') else STOP
    spz = (SPZ.search(str(r.auto)) or [''])[0].replace(' ', '')
    s = z
    while s <= k and s < STOP:
        e = min(addm(s) - dt.timedelta(days=1), k)
        full = (addm(s) - s).days
        per.append(dict(idx=i, smlouva=str(r.smlouva), spz=spz, od=s, do=e, castka=round(r.zpet * ((e - s).days + 1) / full, 0),
                        mesicni=r.zpet, firma=r.firma, fin=r.fin))
        s = addm(s)
P = pd.DataFrame(per); P['zaplaceno'] = 0.0; P['doklad'] = ''; P['bez_spz'] = 0.0; P['zdroj_spz'] = ''

def dates(t, rok):
    m = re.findall(r'(\d{1,2})\.\s?(\d{1,2})\.?\s?(\d{2,4})?', t)
    out = []
    mm_ = re.search(r'\((\d{2})/(\d{4})\)|^(\d{2})/(\d{4})\b', t)
    if not m and mm_:
        g = [x for x in mm_.groups() if x]; return [dt.date(int(g[1]), int(g[0]), 1)]
    for dd, mm, yy in m:
        try:
            y = int(yy) + (2000 if yy and len(yy) == 2 else 0) if yy else rok
            out.append(dt.date(y, int(mm), int(dd)))
        except ValueError:
            pass
    return out

it['rok'] = it.duzp.str[:4].astype(int)
unmatched = []
for r in it.sort_values('duzp').itertuples():
    if r.castka <= 0 or re.search(r'přestup|pokut|administrativní|jistin|škody|škodní|poškoz|přefaktur', r.text, re.I):
        continue
    sp, zdroj = spz_of(r.text), 'položka'
    ds = dates(r.text, r.rok)
    start = ds[0] if ds else None
    if not sp: sp, zdroj = spz_of(r.hlavicka), 'hlavička'          # dříve se SPZ psala do textu před položkami
    if not sp: sp, zdroj = spz_sablona(r.castka, start, dt.date.fromisoformat(r.duzp)), 'šablona'
    if not sp: zdroj = 'částka'
    cand = P[P.spz.isin(sp)] if sp else P
    if cand.empty:
        unmatched.append(r); continue
    if start is not None:
        if not sp:
            cand = cand[cand.od.apply(lambda o: abs((o - start).days) <= 2 or (o.day == start.day and o.month == start.month))]
        else:
            cand = cand[cand.od.apply(lambda o: o >= start - dt.timedelta(days=3))]
    if cand.empty:
        unmatched.append(r); continue
    cand = cand[cand.zaplaceno < cand.castka * 0.98]
    if not sp:   # bez SPZ: částka musí odpovídat k násobkům měsíční částky
        if cand.empty:
            unmatched.append(r); continue
        mes = ((ds[1] - ds[0]).days + 1) / 30.44 if len(ds) >= 2 and ds[1] > ds[0] else None
        ok = lambda m: any(abs(r.castka - m * k) <= max(2, 0.01 * m * k) for k in range(1, 13)) or (mes and abs(r.castka - m * mes) <= 0.04 * m * mes)
        cand = cand[cand.mesicni.apply(lambda m: bool(ok(m)))]
        if cand.empty:
            unmatched.append(r); continue
        cand = cand[abs(pd.to_datetime(cand.od) - pd.Timestamp(r.duzp)).dt.days <= 120]
    if cand.empty:
        unmatched.append(r); continue
    # rozdělit částku na po sobě jdoucí období jedné smlouvy
    first = cand.sort_values('od').iloc[0]
    rest = r.castka
    for j in P[(P.idx == first.idx) & (P.od >= first.od)].sort_values('od').index:
        if rest <= 1: break
        need = P.at[j, 'castka'] - P.at[j, 'zaplaceno']
        if need <= 0: continue
        pay = min(need, rest); P.at[j, 'zaplaceno'] += pay; P.at[j, 'bez_spz'] += 0 if zdroj in ('položka', 'hlavička') else pay; P.at[j, 'zdroj_spz'] = zdroj; P.at[j, 'doklad'] += ('' if not P.at[j, 'doklad'] else ',') + str(r.cislo); rest -= pay
    if rest > 1:
        unmatched.append(r._replace(castka=rest))

P['chybi'] = (P.castka - P.zaplaceno).clip(lower=0).round(0)
# součty po SPZ: všechny položky se SPZ (bez ohledu na období) + položky bez SPZ přiřazené párováním
def spz_items():
    rows = []
    for r in it.itertuples():
        if r.castka == 0 or re.search(r'přestup|pokut|administrativní|jistin|škody|škodní|poškoz|přefaktur', r.text, re.I): continue
        sp = spz_of(r.text) or spz_of(r.hlavicka)
        for x in sp:
            rows.append((x, r.duzp, r.castka / len(sp)))
    return pd.DataFrame(rows, columns=['spz', 'duzp', 'castka'])
SI = spz_items(); SI.to_csv(B / 'output/polozky_spz.csv', index=False)
P.to_csv(B / 'output/obdobi.csv', index=False)
S = P.groupby(['idx', 'smlouva', 'spz', 'firma', 'fin', 'mesicni']).agg(od=('od', 'min'), do=('do', 'max'), obdobi=('od', 'size'),
      ma_byt=('castka', 'sum'), vyfakturovano=('zaplaceno', 'sum'), chybi=('chybi', 'sum'),
      chybi_obdobi=('chybi', lambda s: int((s > 0.5 * P.loc[s.index, 'castka']).sum()))).reset_index()
S['klient'] = S.firma.str.split('/').str[1].fillna('')
S = S.sort_values('chybi', ascending=False)
S.to_csv(B / 'output/nevyfakturovano.csv', index=False)
U = pd.DataFrame(unmatched); U.to_csv(B / 'output/nesparovane_polozky.csv', index=False)
print('ma byt', round(P.castka.sum()), 'vyfakt', round(P.zaplaceno.sum()), 'chybi', round(P.chybi.sum()), 'nesparovane polozky', len(U), round(U.castka.sum()) if len(U) else 0)
print(P.groupby(pd.to_datetime(P.od).dt.year)[['castka', 'zaplaceno', 'chybi']].sum().round(-3))
