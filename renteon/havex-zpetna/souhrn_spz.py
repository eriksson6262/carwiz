#!/usr/bin/env python3
"""Rozdíl po SPZ: mělo být vyfakturováno (přehled) vs. vyfakturováno (položky se SPZ + položky bez SPZ přiřazené párováním)."""
import pathlib, re, pandas as pd
B = pathlib.Path(__file__).parent
P = pd.read_csv(B / 'output/obdobi.csv', parse_dates=['od', 'do']); SI = pd.read_csv(B / 'output/polozky_spz.csv')
V = pd.read_pickle(B / 'data/vozy.pkl')
OD = pd.Timestamp('2021-09-01')
def souhrn(df, si):
    e = df.groupby('spz').agg(ma=('castka', 'sum'), bez=('bez_spz', 'sum'), od=('od', 'min'), do=('do', 'max'), n=('od', 'size'),
                              smlouvy=('smlouva', lambda s: ', '.join(dict.fromkeys(s))), klient=('firma', lambda s: ', '.join(dict.fromkeys(str(x).split('/')[1].strip() for x in s if '/' in str(x)))),
                              idx=('idx', 'first'))
    v = si.groupby('spz').castka.sum()
    e['se_spz'] = e.index.map(v).fillna(0); e['vyf'] = e.se_spz + e.bez; e['chybi'] = e.ma - e.vyf
    e['model'] = e.idx.map(lambda i: re.sub(r'^rz:\s*\S+,\s*', '', str(V.loc[i, 'auto'])))
    mis = df[df.chybi > 0.5 * df.castka].groupby('spz').od.apply(lambda s: ', '.join(sorted({d.strftime('%m/%y') for d in s}, key=lambda x: (x[3:], x[:2]))))
    e['mesice'] = e.index.map(mis).fillna('')
    return e.sort_values('chybi', ascending=False)
A = souhrn(P[P.od >= OD], SI[SI.duzp >= '2021-09'])
A.to_csv(B / 'output/spz_od_2021-09.csv')
print(len(A), 'aut;', (A.chybi > 1000).sum(), 'aut s rozdílem > 1000 Kč; chybí', round(A[A.chybi > 1000].chybi.sum()), '; přefakturováno navíc', round(-A[A.chybi < -1000].chybi.sum()))
A['rok'] = A.od.dt.year
print(A[A.chybi > 1000].groupby('rok').chybi.agg(['size', 'sum']).round())
print(A[A.chybi > 1000].head(25)[['klient', 'smlouvy', 'od', 'do', 'ma', 'vyf', 'chybi']].to_string())
