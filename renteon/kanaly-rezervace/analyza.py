#!/usr/bin/env python3
"""Analýza kanálů rezervací (Renteon CZ + SK) – vstup data/rezervace_CZ.csv, data/rezervace_SK.csv
(z collect_renteon.js), výstup agregované tabulky do output/ (bez osobních údajů).

Období: 12 ukončených měsíců podle data výdeje (OD..DO). CZ částky v Kč, SK v €, bez DPH.
Výnos = všechny položky smlouvy kromě škod a pokut (ty se fakturují zvlášť a nejsou to tržby za pronájem).
"""
import sys, json, pathlib
import pandas as pd, numpy as np

OD, DO = (sys.argv[1:3] if len(sys.argv) > 2 else ('2025-10', '2026-09'))
D = pathlib.Path(__file__).parent / 'data'; O = pathlib.Path(__file__).parent / 'output'; O.mkdir(exist_ok=True)

# Sloučení názvů partnerů → skupiny (Booking.com Transport Ltd = Rentalcars.com)
SKUPINA = {
    'Booking.com Transport Limited': 'Rentalcars.com (Booking)', 'Booking Group': 'Rentalcars.com (Booking)',
    'Gesmarket Internet para Vender S.L.': 'Gesmarket (DoYouSpain)', 'Discover Car Hire': 'DiscoverCars',
    'CARTRAWLER': 'CarTrawler', 'Expedia Inc.': 'Expedia', 'ECONOMY CAR RENTALS': 'Economy Car Rentals',
    'Economy Car Rentals': 'Economy Car Rentals', 'CARJET': 'Carjet', 'AUTO EUROPE': 'Auto Europe', 'Auto Europe': 'Auto Europe',
    'BSP AUTO': 'BSP Auto', 'BSP Autos': 'BSP Auto', 'AurumCars GmbH': 'Aurum / CHECK24', 'MicronNexus GmbH': 'MicronNexus (billiger-mietwagen)',
    'Web': 'Přímo – web', 'Kancelář': 'Přímo – pobočka',
}
UPSELL = ['k_poj_upsell', 'k_vybaveni', 'k_ridic', 'k_zahranici', 'k_znamka', 'k_vek_ridice']
POPL = ['k_mimo_hodiny', 'k_oneway', 'k_km', 'k_palivo', 'k_ostatni']


def nacti():
    fr = []
    for zeme, pob_mena in (('CZ', 'Kč'), ('SK', '€')):
        f = D / f'rezervace_{zeme}.csv'
        if not f.exists():
            continue
        x = pd.read_csv(f); x['zeme'] = zeme; x['mena_vyk'] = pob_mena; fr.append(x)
    d = pd.concat(fr, ignore_index=True)
    d = d[(d.typ != 'OFF') & (d.mesic >= OD) & (d.mesic <= DO)].copy()
    d['partner'] = d.partner.fillna('').replace('', 'Neuvedeno')
    d['skupina'] = d.partner.map(SKUPINA).fillna(d.partner)
    d['prime'] = d.skupina.str.startswith('Přímo')
    kc = [c for c in d.columns if c.startswith('k_') and c != 'k_pult']
    d['vynos'] = d[[c for c in kc if c not in ('k_skody', 'k_pokuty')]].sum(axis=1)
    d['upsell'] = d[UPSELL].sum(axis=1)
    d['delka'] = pd.cut(d.dni, [0, 1, 3, 6, 10, 20, 999], labels=['1 den', '2–3', '4–6', '7–10', '11–20', '21+'])
    d['predstih_k'] = pd.cut(d.predstih, [-1, 2, 7, 14, 30, 60, 999], labels=['0–2 dny', '3–7', '8–14', '15–30', '31–60', '61+'])
    return d


def kanaly(d):
    rows = []
    for (pob, sk), g in d.groupby(['pob_out', 'skupina']):
        a = g[g.zruseno == 0]; z = g[g.zruseno == 1]
        if len(a) == 0 and len(z) < 3:
            continue
        rows.append({
            'pobocka': pob, 'kanal': sk, 'prime': bool(g.prime.iloc[0]), 'mena': g.mena_vyk.iloc[0],
            'smluv': len(a), 'zruseno': len(z), 'storno_pct': round(100 * len(z) / max(1, len(a) + len(z)), 1),
            'dni': int(a.dni.sum()), 'prum_delka': round(a.dni.mean(), 1) if len(a) else None,
            'predstih_median': float(a.predstih.median()) if len(a) else None,
            'vynos': round(a.vynos.sum()), 'najem': round(a.k_najem.sum()),
            'vynos_den': round(a.vynos.sum() / max(1, a.dni.sum()), 1), 'najem_den': round(a.k_najem.sum() / max(1, a.dni.sum()), 1),
            'upsell_smlouva': round(a.upsell.mean(), 1) if len(a) else None,
            'pult_smlouva': round(a.k_pult.mean(), 1) if len(a) else None,
            'poj_upsell_pct': round(100 * (a.k_poj_upsell > 0).mean(), 1) if len(a) else None,
            'mimo_hodiny_pct': round(100 * (a.k_mimo_hodiny > 0).mean(), 1) if len(a) else None,
        })
    k = pd.DataFrame(rows)
    for pob in k.pobocka.unique():
        m = k.pobocka == pob
        k.loc[m, 'podil_smluv_pct'] = (100 * k.loc[m, 'smluv'] / k.loc[m, 'smluv'].sum()).round(1)
        k.loc[m, 'podil_vynosu_pct'] = (100 * k.loc[m, 'vynos'] / k.loc[m, 'vynos'].sum()).round(1)
    return k.sort_values(['pobocka', 'vynos'], ascending=[True, False])


def mesice(d):
    a = d[d.zruseno == 0]
    m = a.groupby(['pob_out', 'mesic']).apply(lambda g: pd.Series({
        'smluv': len(g), 'prime_smluv': int(g.prime.sum()), 'vynos': round(g.vynos.sum()),
        'prime_vynos': round(g[g.prime].vynos.sum()), 'dni': int(g.dni.sum())}), include_groups=False).reset_index()
    m['prime_podil_pct'] = (100 * m.prime_smluv / m.smluv).round(1)
    f = D / 'flotila.csv'  # Ø aut ve flotile pronájmu (getFleetStateByOfficeInPeriod), volitelné
    if f.exists():
        m = m.merge(pd.read_csv(f), on=['pob_out', 'mesic'], how='left')
        dnu = pd.to_datetime(m.mesic + '-01').dt.days_in_month
        m['vytizeni_pct'] = (100 * m.dni / (m.aut * dnu)).round(1)   # dny pronájmu podle měsíce výdeje / kapacita
        m['vynos_auto'] = (m.vynos / m.aut).round(0)
    return m


def profil(d, col):
    a = d[d.zruseno == 0]
    p = a.groupby(['pob_out', col], observed=True).agg(smluv=('dni', 'size'), dni=('dni', 'sum'), vynos=('vynos', 'sum'), najem=('k_najem', 'sum')).reset_index()
    p['vynos_den'] = (p.vynos / p.dni).round(1); p['najem_den'] = (p.najem / p.dni).round(1)
    p['podil_smluv_pct'] = (100 * p.smluv / p.groupby('pob_out').smluv.transform('sum')).round(1)
    return p.rename(columns={col: 'skupina'})


def doplnky(d):
    a = d[d.zruseno == 0]
    out = []
    for pob, g in a.groupby('pob_out'):
        n = len(g)
        for c in UPSELL + POPL + ['k_skody', 'k_pokuty', 'k_pult']:
            out.append({'pobocka': pob, 'polozka': c[2:], 'pct_smluv': round(100 * (g[c] > 0).mean(), 1),
                        'celkem': round(g[c].sum()), 'na_smlouvu': round(g[c].sum() / n, 1)})
    return pd.DataFrame(out)


if __name__ == '__main__':
    d = nacti()
    res = {'obdobi': [OD, DO], 'kanaly': kanaly(d), 'mesice': mesice(d), 'delka': profil(d, 'delka'),
           'predstih': profil(d, 'predstih_k'), 'sipp': profil(d, 'sipp'), 'doplnky': doplnky(d)}
    for k, v in res.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(O / f'{k}.csv', index=False)
    print('OK', {k: len(v) for k, v in res.items() if isinstance(v, pd.DataFrame)})
