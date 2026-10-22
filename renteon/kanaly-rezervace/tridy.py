#!/usr/bin/env python3
"""Ziskovost podle třídy vozu: data/pl_auta.csv (P&L po SPZ a rocích z renteon/naklady-vynosy, dashboard „Náklady vs výnosy“)
+ data/dny_auta.csv (dny po činnostech na SPZ a rok z Renteonu). Výstup output/tridy.csv, output/tridy_sipp.csv."""
import sys, pathlib
import pandas as pd
B = pathlib.Path(__file__).parent
ROKY = [int(x) for x in (sys.argv[1:] or ['2025', '2026'])]
TRIDA = {**{s: 'Mini' for s in ['MBMR', 'MDMR', 'MTMR']},
         **{s: 'Economy' for s in ['IGMR', 'IGAR', 'EDAR', 'EDMR', 'EWMR']},
         **{s: 'Compact' for s in ['CDAR', 'CDMR', 'CFAR', 'CFMR', 'CKMR', 'CWAR', 'PGAR']},
         **{s: 'Large / kombi' for s in ['IDAR', 'IWAR', 'FDAR', 'FWAR', 'LFAR', 'LFMR', 'LLAR']},
         **{s: 'SUV' for s in ['FFAR', 'UEAR', 'PFAR']},
         **{s: 'Minibus' for s in ['SVAR', 'SVMR', 'PVAR']}, 'FKMR': 'Dodávka', 'GFAR': 'Executive'}

pl = pd.read_csv(B / 'data' / 'pl_auta.csv'); dn = pd.read_csv(B / 'data' / 'dny_auta.csv')
d = pl.merge(dn, on=['spz', 'rok'], how='left')
d['sipp'] = d.sipp.fillna(d.sipp_renteon)
d = d[d.rok.isin(ROKY) & d.sipp.notna() & (d.poznamka.fillna('') != 'bez leasingu v datech')]
for c in ['dny_kratkodobe', 'dny_dlouhodobe', 'dny_interni', 'dny_volne']:
    d[c] = d[c].fillna(0)
d['dny_provoz'] = d.dny_kratkodobe + d.dny_dlouhodobe + d.dny_interni + d.dny_volne
d = d[(d.dny_provoz >= 30) & (d.dny_kratkodobe + d.dny_dlouhodobe > 0)]   # auta v provozu aspoň měsíc
d['trida'] = d.sipp.map(TRIDA).fillna('Ostatní')


def agg(g):
    dny = g.dny_provoz.sum()
    return pd.Series({
        'aut': g.spz.nunique(), 'aut_roky': round(dny / 365, 1),
        'vynos': g.vynos_celkem.sum(), 'z_toho_kratkodobe': g.vynos_renteon.sum(),
        'leasing': g.leasing.sum() + g.carnetto.sum(), 'pojisteni': g.pojisteni.sum(), 'servis': g.servis_opravy.sum(), 'palivo': g.palivo.sum(),
        'naklady': g.naklady_celkem.sum(), 'vysledek': g.vysledek.sum(),
        'marze_pct': round(100 * g.vysledek.sum() / max(1, g.vynos_celkem.sum()), 1),
        'vysledek_auto_mesic': round(g.vysledek.sum() / dny * 30.4) if dny else None,
        'vynos_auto_mesic': round(g.vynos_celkem.sum() / dny * 30.4) if dny else None,
        'naklad_auto_mesic': round(g.naklady_celkem.sum() / dny * 30.4) if dny else None,
        'kratkodobe_pct_dni': round(100 * g.dny_kratkodobe.sum() / dny, 1) if dny else None,
        'dlouhodobe_pct_dni': round(100 * g.dny_dlouhodobe.sum() / dny, 1) if dny else None,
        'ztratovych_aut_pct': round(100 * (g.vysledek < 0).mean(), 1),
    })


t = d.groupby('trida').apply(agg, include_groups=False).sort_values('vysledek_auto_mesic', ascending=False)
s = d.groupby(['trida', 'sipp']).apply(agg, include_groups=False).reset_index().sort_values('vysledek_auto_mesic', ascending=False)
(B / 'output').mkdir(exist_ok=True)
t.to_csv(B / 'output' / 'tridy.csv'); s.to_csv(B / 'output' / 'tridy_sipp.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(t.to_string()); print(s[s.aut_roky >= 2].to_string(index=False))
print('celkem aut-roků', round(d.dny_provoz.sum() / 365, 1), 'řádků', len(d))
