#!/usr/bin/env python3
"""Oprava výnosů v P&L (23. 10. 2026) – doplní, co v build_pl.py chybělo:
1) výnos z Renteonu CZ u aut, kde P&L po autech měl < 50 % výnosu podle Podrobného přehledu rezervace (SPZ smlouvy, měsíc výdeje,
   pobočka výdeje) → data/doplneni_renteon.csv (spz, mesic, pob, vynos Kč bez DPH);
2) dlouhodobé pronájmy fakturované z Vyfakturuj RX Auto SK (P&L bral jen RX Auto CZ) → data/doplneni_vyfakturuj_sk.csv (€ × 24,3).
Vstup/výstup: data/pl_auta.csv, data/pl_pobocky.csv (přepíše; originály uloží jako *_puvodni.csv)."""
import pathlib, shutil
import pandas as pd
D = pathlib.Path(__file__).parent / 'data'; KURZ = 24.3
for f in ['pl_auta', 'pl_pobocky']:
    if not (D / f'{f}_puvodni.csv').exists():
        shutil.copy(D / f'{f}.csv', D / f'{f}_puvodni.csv')
auta = pd.read_csv(D / 'pl_auta_puvodni.csv'); pob = pd.read_csv(D / 'pl_pobocky_puvodni.csv')
rn = pd.read_csv(D / 'doplneni_renteon.csv'); sk = pd.read_csv(D / 'doplneni_vyfakturuj_sk.csv')
sk['vynos'] = (sk.vynos_eur * KURZ).round(0)
for df, col in [(rn, 'vynos_renteon'), (sk, 'vynos_vyfakturuj')]:
    df['rok'] = df.mesic.str[:4].astype(int)
    for (spz, rok), g in df.groupby(['spz', 'rok']):
        m = (auta.spz == spz) & (auta.rok == rok)
        if not m.any():
            auta.loc[len(auta)] = {**{c: 0 for c in auta.columns}, 'rok': rok, 'spz': spz, 'model': '', 'sipp': '', 'pobocka': g.pob.mode()[0], 'poznamka': ''}
            m = (auta.spz == spz) & (auta.rok == rok)
        add = g.vynos.sum()
        if col == 'vynos_renteon':
            add = max(0, add - auta.loc[m, col].iloc[0])     # doplnit jen rozdíl
        auta.loc[m, col] += round(add); auta.loc[m, 'vynos_celkem'] += round(add); auta.loc[m, 'vysledek'] += round(add)
        p = auta.loc[m, 'poznamka'].fillna('').iloc[0]
        auta.loc[m, 'poznamka'] = (p + ('; ' if p else '') + ('doplněn výnos Renteon' if col == 'vynos_renteon' else 'doplněn Vyfakturuj SK'))
        share = g.vynos / g.vynos.sum()
        for (_, r), s in zip(g.iterrows(), share):
            q = (pob.mesic == r.mesic) & (pob.pobocka == r.pob)
            v = round(add * s)
            pob.loc[q, col] += v; pob.loc[q, 'vynos_celkem'] += v; pob.loc[q, 'vysledek'] += v
auta = auta.sort_values('vysledek')
auta.to_csv(D / 'pl_auta.csv', index=False); pob.to_csv(D / 'pl_pobocky.csv', index=False)
d0 = pd.read_csv(D / 'pl_pobocky_puvodni.csv')
print('doplněno do poboček:', (pob.vynos_celkem.sum() - d0.vynos_celkem.sum()))
print(pob.groupby(['pobocka', pob.mesic.str[:4]]).vynos_celkem.sum().sub(d0.groupby(['pobocka', d0.mesic.str[:4]]).vynos_celkem.sum()).loc[lambda s: s != 0])
