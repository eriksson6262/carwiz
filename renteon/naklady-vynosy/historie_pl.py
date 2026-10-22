#!/usr/bin/env python3
"""P&L 05/2020–12/2023 (před začátkem build_pl.py) ve stejném formátu jako pl_pobocky.csv a pl_auta.csv.
Výnosy: data/renteon_historie.csv (Renteon CZ, smlouvy po SPZ a měsíci výdeje, pobočka výdeje),
        data/vyfakturuj_historie.csv (Vyfakturuj RX Auto CZ, nájemní položky po SPZ; druh havex = zpětná fakturace HAVEX).
Leasing: data/leasing_historie.csv (přehled zápůjček HAVEX – skutečné sazby smluv).
Pojištění, servis, palivo, nájem pobočky: v poště pro 2020–2023 nejsou (Kooperativa až od X/2023, Generali od IX/2023, servisy
od 2024) → ODHAD podle sazeb 2024 na vůz a měsíc (PRG/OSR) a nájmu pobočky 2024. Vozidel = vozo-měsíce leasingu napřímo + auta s výnosem bez leasingu.
Výstup: data/pl_pobocky_historie.csv, data/pl_auta_historie.csv; s --merge připojí k data/pl_pobocky.csv a data/pl_auta.csv."""
import sys, pathlib
import pandas as pd
D = pathlib.Path(__file__).parent / 'data'
DO = '2023-12'
SAZBA = {'PRG': dict(poj=1672, serv=1115, palivo=155), 'OSR': dict(poj=1405, serv=534, palivo=409)}   # Kč/vůz/měsíc, z pl_pobocky 2024
NAJEM = {'PRG': 30059, 'OSR': 24738}                                                                   # Kč/měsíc, odhad jako najem_odhad v build_pl.py
OSR_OD = '2021-01'

rn = pd.read_csv(D / 'renteon_historie.csv'); rn = rn[(rn.mesic <= DO) & (rn.pob.isin(['PRG', 'OSR']))]
vf = pd.read_csv(D / 'vyfakturuj_historie.csv'); vf = vf[vf.mesic <= DO]
le = pd.read_csv(D / 'leasing_historie.csv'); le = le[le.mesic <= DO]

# pobočka auta v měsíci: podle výnosu Renteon (ten měsíc, jinak převládající v roce), jinak PRG
rn['rok'] = rn.mesic.str[:4]
mpob = rn.groupby(['spz', 'mesic']).apply(lambda g: g.groupby('pob').vynos.sum().idxmax(), include_groups=False).to_dict()
ypob = rn.groupby(['spz', 'rok']).apply(lambda g: g.groupby('pob').vynos.sum().idxmax(), include_groups=False).to_dict()
pob = lambda s, m: mpob.get((s, m)) or ypob.get((s, m[:4])) or 'PRG'

rows = []   # (mesic, pobocka, spz, kategorie, castka)
for r in rn.itertuples(): rows.append((r.mesic, r.pob, r.spz, 'v_renteon', r.vynos))
for r in vf.itertuples():
    if r.druh == 'havex': rows.append((r.mesic, 'HAVEX_ZF', r.spz, 'v_havex', r.vynos))
    elif r.druh == 'ga': rows.append((r.mesic, 'OSR' if r.mesic >= OSR_OD else 'PRG', r.spz, 'v_vyfakturuj', r.vynos))
    else: rows.append((r.mesic, pob(r.spz, r.mesic), r.spz, 'v_vyfakturuj', r.vynos))
for r in le.itertuples():
    b = 'HAVEX_ZF' if r.typ == 'zpětná fakturace' else pob(r.spz, r.mesic)
    rows.append((r.mesic, b, r.spz, 'leasing_odhad' if False else 'leasing', r.castka_bez_dph))
x = pd.DataFrame(rows, columns=['mesic', 'pobocka', 'spz', 'kat', 'castka'])
x['pobocka'] = x.pobocka.where(~((x.pobocka == 'OSR') & (x.mesic < OSR_OD)), 'PRG')
# GLOBAL ASSISTANCE (asistenční služby) = Ostrava od 2021, jako v renteon/vynosy-flotila – řešeno u druhu 'ga' výše

# vozo-měsíce na pobočce: leasing napřímo (podíl měsíce) + auta s výnosem bez leasingu (1)
lm = le[le.typ == 'napřímo'].copy(); lm['b'] = [pob(s, m) for s, m in zip(lm.spz, lm.mesic)]
dim = pd.to_datetime(lm.mesic + '-01').dt.days_in_month
lm['podil'] = (lm.castka_bez_dph / lm.groupby(['smlouva', 'mesic']).castka_bez_dph.transform('max')).clip(upper=1)  # podíl měsíce
vm = lm.groupby(['mesic', 'b', 'spz']).podil.max().reset_index()
bez = x[x.kat.isin(['v_renteon', 'v_vyfakturuj'])][['mesic', 'pobocka', 'spz']].drop_duplicates()
bez = bez[~bez.set_index(['mesic', 'spz']).index.isin(vm.set_index(['mesic', 'spz']).index) & ~bez.spz.str.startswith('(')]
car = pd.concat([vm.rename(columns={'b': 'pobocka'}), bez.assign(podil=1.0)])
car['pobocka'] = car.pobocka.where(~((car.pobocka == 'OSR') & (car.mesic < OSR_OD)), 'PRG')
# odhad pojištění/servisu/paliva na auto
for k in ['poj', 'serv', 'palivo']:
    car[k] = car.podil * car.pobocka.map(lambda b: SAZBA.get(b, SAZBA['PRG'])[k])
est = car.melt(id_vars=['mesic', 'pobocka', 'spz'], value_vars=['poj', 'serv', 'palivo'], var_name='kat', value_name='castka')
est['kat'] = est.kat.map({'poj': 'pojisteni', 'serv': 'servis', 'palivo': 'palivo'})
x = pd.concat([x, est])

months = sorted(set(x.mesic))
pobs = []
for m in months:
    for b in ['PRG', 'OSR', 'BTS', 'HAVEX_ZF']:
        g = x[(x.mesic == m) & (x.pobocka == b)]
        s = lambda k: round(g[g.kat == k].castka.sum())
        vr, vv = s('v_renteon'), s('v_vyfakturuj') + s('v_havex')
        naj = NAJEM.get(b, 0) if (b == 'PRG' or (b == 'OSR' and m >= OSR_OD)) else 0
        row = dict(mesic=m, pobocka=b, vynos_renteon=vr, vynos_vyfakturuj=vv, vynos_celkem=vr + vv, leasing=s('leasing'), leasing_odhad=0,
                   carnetto_leasing=0, pojisteni=s('pojisteni'), carnetto_pojisteni=0, servis=s('servis'), opravy=0, ostatni=0, palivo=s('palivo'),
                   najem_pobocky=0, najem_odhad=naj)
        row['naklady_celkem'] = sum(row[k] for k in ['leasing', 'pojisteni', 'servis', 'palivo', 'najem_odhad'])
        row['vysledek'] = row['vynos_celkem'] - row['naklady_celkem']
        row['vozidel'] = round(car[(car.mesic == m) & (car.pobocka == b)].podil.sum(), 1)
        if any(row[k] for k in ['vynos_celkem', 'naklady_celkem']): pobs.append(row)
P = pd.DataFrame(pobs)

x['rok'] = x.mesic.str[:4].astype(int)
au = []
for (spz, rok), g in x.groupby(['spz', 'rok']):
    s = lambda k: round(g[g.kat == k].castka.sum())
    vr, vv, vh = s('v_renteon'), s('v_vyfakturuj'), s('v_havex')
    L, pj, sv, pa = s('leasing'), s('pojisteni'), s('servis'), s('palivo')
    au.append(dict(rok=rok, spz=spz, model='', sipp='', pobocka=g.groupby('pobocka').castka.sum().idxmax(), vynos_renteon=vr, vynos_vyfakturuj=vv,
                   vynos_havex=vh, vynos_celkem=vr + vv + vh, leasing=L, leasing_odhad=0, carnetto=0, pojisteni=pj, servis_opravy=sv, palivo=pa,
                   naklady_celkem=L + pj + sv + pa, vysledek=vr + vv + vh - L - pj - sv - pa,
                   poznamka='2020–2023: leasing z přehledu zápůjček, pojištění/servis/palivo odhad (sazby 2024)'))
A = pd.DataFrame(au)
P.to_csv(D / 'pl_pobocky_historie.csv', index=False); A.to_csv(D / 'pl_auta_historie.csv', index=False)
pd.set_option('display.width', 220)
print(P.groupby([P.mesic.str[:4], 'pobocka'])[['vynos_celkem', 'leasing', 'pojisteni', 'servis', 'najem_odhad', 'naklady_celkem', 'vysledek', 'vozidel']].sum().round(-3))
if '--merge' in sys.argv:
    for hist, cur in [(P, 'pl_pobocky'), (A, 'pl_auta')]:
        c = pd.read_csv(D / f'{cur}.csv')
        c = c[~((c.mesic < '2024') if 'mesic' in c else (c.rok < 2024))]
        out = pd.concat([hist[c.columns], c]).sort_values(['mesic', 'pobocka'] if 'mesic' in c else ['vysledek'])
        out.to_csv(D / f'{cur}.csv', index=False); print(cur, len(out))
