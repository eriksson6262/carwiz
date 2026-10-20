#!/usr/bin/env python3
"""Stage 2: apply sample factors to live CW-PP rows -> new pricelists + estimates.
Reads out/stage1.json + data/CZ.json, data/SK.json. Writes out/stage2.json
"""
import json, os, statistics as st, datetime as dt
from collections import defaultdict
import sys
sys.path.insert(0, os.path.dirname(__file__))
from reprice import (NEW_K, BASE, D, ISO, fmt, TODAY, WIN_END, CLASSES, SIPP2K, BANDS, BMIN, BMAX,
                     DUR2BAND, LOC)

st1 = json.load(open(f'{BASE}/out/stage1.json'))
S = st1['S']; F = {tuple(k.split('|')): v for k, v in st1['F'].items()}
cz = json.load(open(f'{BASE}/data/CZ.json')); sk = json.load(open(f'{BASE}/data/SK.json'))
PLS = {'CZ': cz['PL'], 'SK': sk['PL']}

BAND_DURS = {'2-3': [3], '4-6': [4], '7-7': [7], '8-13': [10], '14-14': [14], '15-20': [14]}


def period_key(a, b):
    return f'{fmt(a)}-{fmt(b)}'


def factor_table(L):
    """factor[(class, (a,b), band)] for all periods of location L within window."""
    country, office, oid = LOC[L]
    PL = PLS[country]
    samp = defaultdict(list)
    for s in S:
        if s['L'] == L and s['f'] is not None:
            samp[s['k']].append((ISO(s['p']), s['du'], s['f']))
    # periods present for repriced SIPPs in window
    periods = sorted({(max(D(r['F']), TODAY), min(D(r['T']), WIN_END)) for r in PL
                      if r['Oid'] == oid and r['S'] in SIPP2K and D(r['T']) >= TODAY and D(r['F']) <= WIN_END})
    tab = {}; info = {}
    for k in CLASSES:
        src = 'C' if (L == 'OSR' and k == 'E') else k
        if L == 'BTS' and k == 'E':
            continue
        sm = samp.get(src, [])
        med = {}
        for band, durs in BAND_DURS.items():
            v = [f for p, du, f in sm if du in durs and p <= WIN_END]
            med[band] = st.median(v) if v else 1.0
        raw = {}
        for (a, b) in sorted(set(periods) | {(max(D(r['F']), TODAY), min(D(r['T']), WIN_END)) for r in PL if r['Oid'] == oid and r['S'] in CLASSES[k] and D(r['T']) >= TODAY and D(r['F']) <= WIN_END}):
            for band, durs in BAND_DURS.items():
                v = [f for p, du, f in sm if du in durs and a <= p <= b]
                raw[((a, b), band)] = (st.median(v), len(v)) if v else (None, 0)
        def get(a, b, band):
            return raw.get(((a, b), band), (None, 0))
        pl = sorted({(max(D(r['F']), TODAY), min(D(r['T']), WIN_END)) for r in PL
                     if r['Oid'] == oid and r['S'] in CLASSES[k] and D(r['T']) >= TODAY and D(r['F']) <= WIN_END})
        for (a, b) in pl:
            # Erik 20.10.2026: blokují se jen vyzvednutí 24.–27.12. (pravidla +500 % CZ / +300 % SK), od 28.12. normálně konkurenceschopné
            if k in NEW_K and a <= dt.date(2026, 12, 27) and b >= dt.date(2026, 12, 24):
                for band in BAND_DURS:
                    tab[(k, (a, b), band)] = 1.0; info[(k, (a, b), band)] = 'Vánoce beze změny'
                continue
            for band in BAND_DURS:
                f, n = get(a, b, band)
                note = f'{n} vz.'
                if a <= dt.date(2026, 12, 27) and b >= dt.date(2026, 12, 25) and a >= dt.date(2026, 12, 25):
                    f, note = 1.0, 'Vánoce beze změny'
                elif a >= dt.date(2026, 12, 30) and b <= dt.date(2027, 1, 7):
                    # P9/P10 = P11 (first period starting 08.01.)
                    nxt = [p for p in pl if p[0] == dt.date(2027, 1, 8)]
                    if nxt:
                        f2, n2 = get(nxt[0][0], nxt[0][1], band)
                        f, note = (f2 if f2 is not None else med[band]), '= období od 8.1.'
                elif a >= dt.date(2026, 12, 18) and b <= dt.date(2026, 12, 24) and band not in ('2-3', '4-6'):
                    prv = [p for p in pl if p[1] == dt.date(2026, 12, 17)]
                    if prv:
                        f2, n2 = get(prv[0][0], prv[0][1], band)
                        f, note = (f2 if f2 is not None else med[band]), '= období před 18.12.'
                elif n < 2:
                    # neighbours average, else class median
                    i = pl.index((a, b)); nb = []
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(pl):
                            fx, nx = get(pl[j][0], pl[j][1], band)
                            if fx is not None and nx >= 2: nb.append(fx)
                    if f is not None:
                        nb.append(f)
                    f, note = (st.mean(nb), 'průměr sousedů') if nb else (med[band], 'medián třídy')
                tab[(k, (a, b), band)] = f
                info[(k, (a, b), band)] = note
    return tab, info, periods


def enforce(p):
    """per-day non-increasing, total non-decreasing, 21- = 3x 7-7"""
    order = BANDS[1:7]   # 1-1 is set from 2-3 afterwards and never pushes other bands
    for i in range(1, len(order)):
        b, pb = order[i], order[i - 1]
        p[b] = min(p[b], p[pb])
        p[b] = max(p[b], p[pb] * BMAX[pb] / BMIN[b])
    p['21-'] = 3 * p['7-7']
    return {k: round(v, 2) for k, v in p.items()}


def sk_xmas_split(rows, changes):
    """remaining SK rows 25.-29.12. (not repriced classes): 25.-27. = 30.12. row, 28.-29. keep."""
    res = []
    for r in rows:
        if D(r['F']) == dt.date(2026, 12, 25) and D(r['T']) == dt.date(2026, 12, 29):
            nb = [x for x in rows if x['S'] == r['S'] and x.get('O', x.get('Oid')) == r.get('O', r.get('Oid')) and D(x['F']) == dt.date(2026, 12, 30)]
            if nb:
                res.append(dict(r, T=fmt(dt.date(2026, 12, 27)), D=dict(nb[0]['D']), new=True,
                                note={'x': 'Vánoce SK: základ = 30.12., přirážku dělá pravidlo +300 %'}))
                changes.append(dict(L='BTS', S=r['S'], F=r['F'], T='27.12.2026.', old=r['D'], new=nb[0]['D'], fac={}))
                res.append(dict(r, F=fmt(dt.date(2026, 12, 28))))
                continue
        res.append(r)
    return res


# Erik 10.10.2026: minimální cena za den bez DPH PO SLEVĚ z pravidel obsazenosti (nesmí za to přijít nikdy)
MIN_AFTER = {'E': 6.5, 'C': 7.5, 'I': 9.0, 'F': 13.0}
# Erik 19.10.2026: kompromisní minima pro CZ (Praha + Ostrava) po slevě; SK beze změny
MIN_AFTER_C = {'CZ': {'E': 5.0, 'C': 5.5, 'I': 6.5, 'F': 13.0}, 'SK': MIN_AFTER}
MIN_DEFAULT = 6.5
import math


def max_discount(country, sipp):
    """lowest multiplier from active non-mandatory negative pricing rules covering the SIPP"""
    rules = (cz if country == 'CZ' else sk)['RULES']
    m = 1.0
    for r in rules:
        adj = r.get('PriceAdjustmentPercentage') or 0
        if adj >= 0: continue
        cats = [c.strip() for c in (r.get('CarCategoriesText') or '').split(',')]
        if r.get('IsAllCarCategories') or sipp in cats:
            m = min(m, 1 + adj / 100)
    return m


MIN_SIPP = {'GFAR': 65.0}   # Erik 12.10.2026: GFAR nikdy pod 65 €/den (ani delší pronájem)


def floor_for(country, sipp):
    mn = MIN_SIPP.get(sipp) or MIN_AFTER_C.get(country, MIN_AFTER).get(sipp[0], MIN_DEFAULT)
    return math.ceil(mn / max_discount(country, sipp) * 100) / 100


def apply_floor(rows, changes, country):
    """price floor per day for all future rows; 21- stays 3x 7-7 where repriced, 1-1 >= 2-3."""
    from reprice import TODAY
    oid2L = {v[2]: L for L, v in LOC.items() if v[0] == country}
    res = []
    for r in rows:
        MIN_DAY = floor_for(country, r['S'])
        if D(r['T']) < TODAY or not any((r['D'].get(b) or 0) < MIN_DAY for b in BANDS[:7]):
            res.append(r); continue
        a = D(r['F'])
        if a < TODAY:   # keep past part unchanged
            res.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1)))); a = TODAY
        old = dict(r['D']); d = dict(r['D'])
        for b in BANDS[:7]:
            if d.get(b) is not None and d[b] < MIN_DAY: d[b] = MIN_DAY
        d['1-1'] = max(d['1-1'], d['2-3'])
        if d.get('21-') is not None:
            d['21-'] = round(max(d['21-'], 3 * d['7-7']) if r.get('new') else max(d['21-'], MIN_DAY), 2)
        nr = dict(r, F=fmt(a), D=d, new=True, floor=True)
        nr.setdefault('L', oid2L.get(r['Oid']))
        res.append(nr)
        if not r.get('new'):
            changes.append(dict(L=oid2L.get(r['Oid']), S=r['S'], F=fmt(a), T=r['T'], old=old, new=d, fac={}))
        else:
            for ch in changes:
                if ch['S'] == r['S'] and ch['F'] == r['F'] and ch['T'] == r['T'] and ch['L'] == oid2L.get(r['Oid']):
                    ch['new'] = d
    return res


SK21_DONE = True   # set True once SK CW-PP 21- band already tripled in Renteon


def build(country):
    PL = PLS[country]
    locs = [L for L, v in LOC.items() if v[0] == country]
    tabs = {L: factor_table(L) for L in locs}
    oid2L = {LOC[L][2]: L for L in locs}
    out = []; changes = []
    for r in PL:
        L = oid2L.get(r['Oid'])
        a, b = D(r['F']), D(r['T'])
        k = SIPP2K.get(r['S'])
        reprice = L and k and not (L == 'BTS' and k == 'E') and not (k in NEW_K and L != 'PRG') and b >= TODAY and a <= WIN_END
        if not reprice:
            if country == 'SK' and b >= TODAY and r['D'].get('21-') is not None and not SK21_DONE:
                if a < TODAY:
                    out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1)), new=False)); a = TODAY
                d2 = dict(r['D']); d2['21-'] = round(3 * r['D']['21-'], 2)
                out.append(dict(r, F=fmt(a), D=d2, new=True, L='BTS', k=None, note21='21- x3'))
                changes.append(dict(L='BTS', S=r['S'], F=fmt(a), T=r['T'], old=r['D'], new=d2, fac={}))
                continue
            out.append(dict(r, new=False)); continue
        # split at TODAY
        if a < TODAY:
            out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1)), new=False))
            a = TODAY
        tab, info, periods = tabs[L]
        if b > WIN_END:   # should not happen with current boundaries
            out.append(dict(r, F=fmt(WIN_END + dt.timedelta(days=1)), new=False)); b = WIN_END
        old = {x: r['D'][x] for x in BANDS}
        fac = {band: tab.get((k, (a, b), band), 1.0) for band in BAND_DURS}
        new = {band: old[band] * fac[band] for band in BAND_DURS}
        ratio11 = old['1-1'] / old['2-3'] if old['2-3'] else 1.67
        new['21-'] = 0
        new['1-1'] = 0
        new = enforce({x: new[x] for x in BANDS})
        new['1-1'] = round(max(new['2-3'], new['2-3'] * ratio11), 2)
        xmas = a >= dt.date(2026, 12, 25) and b <= dt.date(2026, 12, 27)
        if xmas:
            new = dict(old)  # P8 unchanged
            if country == 'SK' and b <= dt.date(2026, 12, 27):
                # Erik 20.10.2026: řádky vyzvednutí 24.–27.12. se nemění (rezervace nechceme, přirážku dělá pravidlo +300 %)
                out.append(dict(r, F=fmt(a), new=False)); continue
            if country == 'SK':
                # SK: base x6 in 25.-29.12. AND mandatory rule +300 % for 24.-27.12. = double surcharge.
                # 25.-27.12. -> neighbour (30.12.) price, rule does the surcharge; 28.-29.12. keep old high price
                nb = [x for x in PL if x['S'] == r['S'] and x['Oid'] == r['Oid'] and D(x['F']) == dt.date(2026, 12, 30)]
                if nb and a <= dt.date(2026, 12, 27):
                    nbr = nb[0]['D']; kk = SIPP2K.get(r['S'])
                    fac2 = {band: tab.get((k, (dt.date(2026, 12, 30), D(nb[0]['T'])), band), 1.0) for band in BAND_DURS}
                    nn = {band: nbr[band] * fac2[band] for band in BAND_DURS}
                    nn['21-'] = 0; nn['1-1'] = 0
                    nn = enforce({x: nn[x] for x in BANDS})
                    nn['1-1'] = round(max(nn['2-3'], nn['2-3'] * (nbr['1-1'] / nbr['2-3'] if nbr['2-3'] else 1.67)), 2)
                    out.append(dict(r, F=fmt(a), T=fmt(dt.date(2026, 12, 27)), D=nn, new=True, L=L, k=k, fac=fac2,
                                    note={'x': 'Vánoce SK: základ = 30.12., přirážku dělá pravidlo +300 %'}))
                    changes.append(dict(L=L, S=r['S'], F=fmt(a), T='27.12.2026.', old=old, new=nn, fac=fac2))
                    if b <= dt.date(2026, 12, 27):
                        continue   # row already split by an earlier import (25.-27.12.)
                    a = dt.date(2026, 12, 28)
                old21 = dict(old); old21['21-'] = round(3 * old['7-7'], 2)
                new = old21
        nr = dict(r, F=fmt(a), T=fmt(b), D=new, new=True, L=L, k=k, fac=fac,
                  note={band: info.get((k, (a, b), band)) for band in BAND_DURS})
        out.append(nr)
        changes.append(dict(L=L, S=r['S'], F=fmt(a), T=fmt(b), old=old, new=new, fac=fac))
    if country == 'SK':
        out = sk_xmas_split(out, changes)
    out = apply_floor(out, changes, country)
    return out, changes, {L: {f'{k}|{period_key(*p)}|{band}': v for (k, p, band), v in tabs[L][0].items()} for L in locs}


PGAR_OVER_IGAR = 1.10   # Erik 12.10.2026: PGAR na úrovni Karoqu (IGAR), lehce dražší


DERIVED = [('PGAR', 'IGAR', PGAR_OVER_IGAR),   # PGAR na úrovni Karoqu, lehce dražší
           ('SVMR', 'SVAR', 0.95)]            # Erik 12.10.2026: SVMR (manuál) lehce pod SVAR
# Erik 20.10.2026: MBMR/MDMR/MTMR = kategorie mini -> cena jako EDMR (economy manuál) na stejné pobočce, CZ i SK
DERIVED_MINI = [('MBMR', 'EDMR', 1.0), ('MDMR', 'EDMR', 1.0), ('MTMR', 'EDMR', 1.0)]


def pgar_from_igar(rows, changes):
    for tgt, src, mult in DERIVED:
        rows = derive_from(rows, changes, tgt, src, mult)
    return rows


def mini_from_edmr(rows, changes):
    """mini (MBMR/MDMR/MTMR) = EDMR na všech pobočkách (Praha, Ostrava, Bratislava), budoucí řádky."""
    from reprice import TODAY
    for TG, SRC, MULT in DERIVED_MINI:
        if not any(r['S'] == TG for r in rows):
            continue
        offs = {r['Oid'] for r in rows if r['S'] == TG}
        out = []
        for r in rows:
            if r['S'] != TG or D(r['T']) < TODAY or not any(x['S'] == SRC and x['Oid'] == r['Oid'] for x in rows):
                out.append(r); continue
            if D(r['F']) < TODAY:
                out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1))))
        for r in rows:
            if r['S'] != SRC or r['Oid'] not in offs or D(r['T']) < TODAY: continue
            a = max(D(r['F']), TODAY)
            d = {b: (round(v * MULT, 2) if v is not None else None) for b, v in r['D'].items()}
            out.append(dict(r, S=TG, F=fmt(a), D=d, new=True, k=TG))
            changes.append(dict(L=r.get('L'), S=TG, F=fmt(a), T=r['T'], old={}, new=d, fac={'x': f'{SRC} × {MULT} (mini)'}))
        rows = out
    return rows


def derive_from(rows, changes, TG, SRC, MULT):
    """TG budoucí řádky (Praha) = nové SRC řádky × MULT (období převzata ze SRC)."""
    from reprice import TODAY
    out = []
    for r in rows:
        if r['S'] != TG or D(r['T']) < TODAY or r['Oid'] is not None:
            out.append(r); continue
        if D(r['F']) < TODAY:
            out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1))))
    oid2L = {None: 'PRG', 26: 'OSR'}
    for r in rows:
        if r['S'] != SRC or D(r['T']) < TODAY or r['Oid'] is not None: continue   # jen Praha
        a = max(D(r['F']), TODAY)
        d = {b: (round(v * MULT, 2) if v is not None else None) for b, v in r['D'].items()}
        old = next((x['D'] for x in rows if x['S'] == TG and x['Oid'] == r['Oid'] and D(x['F']) <= a <= D(x['T'])), {})
        out.append(dict(r, S=TG, F=fmt(a), D=d, new=True, L=oid2L.get(r['Oid']), k=TG))
        changes.append(dict(L=oid2L.get(r['Oid']), S=TG, F=fmt(a), T=r['T'], old=old, new=d, fac={'x': f'{SRC} × {MULT}'}))
    return out


# 20.10.2026 (večer): brokeři (DiscoverCars) promítají nové ceny se zpožděním – při 2 bězích denně by se změna sčítala
# (Bratislava IGAR: 39,54 → 57,74 → 78,55 €/den, přitom DC pořád ukazoval starou cenu). Jeden běh smí změnit cenu max. o ±25 %.
STEP_MAX = float(os.environ.get('STEP_MAX', '1.25'))
STEP_MIN = float(os.environ.get('STEP_MIN', '0.75'))


def step_cap(rows, changes, country):
    from reprice import TODAY
    live = defaultdict(list)
    for r in PLS[country]:
        live[(r['S'], r['Oid'])].append((D(r['F']), D(r['T']), r['D']))
    out = []; n = 0
    for r in rows:
        if not r.get('new') or D(r['T']) < TODAY:
            out.append(r); continue
        a = max(D(r['F']), TODAY)
        lv = next((d for f, t, d in live.get((r['S'], r['Oid']), []) if f <= a <= t), None)
        if not lv:
            out.append(r); continue
        d = dict(r['D']); ch = False
        for bnd in BANDS[:7]:
            o, v = lv.get(bnd), d.get(bnd)
            if o and v:
                nv = round(min(max(v, o * STEP_MIN), o * STEP_MAX), 2)
                if abs(nv - v) > 0.004: d[bnd] = nv; ch = True
        if ch:
            if d.get('21-') is not None and abs(r['D']['21-'] - 3 * r['D']['7-7']) < 0.05:
                d['21-'] = round(3 * d['7-7'], 2)
            d['1-1'] = max(d['1-1'], d['2-3']); n += 1
            out.append(dict(r, D=d))
        else:
            out.append(r)
    print(country, 'step_cap rows', n)
    return out


# Erik 20.10.2026: cena se má podle délky pronájmu řídit konkurencí (2–3, 4, 7, 10, 14 dní). Když cíl vyjde pod minimum,
# minimum dřív srovnalo všechna pásma na jednu cenu. Nově: tvar křivky €/den podle délky = křivka cílů z konkurence
# (cíl/den pro danou délku ÷ cíl/den pro 14 dní, medián za období), nejlevnější pásmo zůstává, kratší se zvednou.
CURVE_DURS = [('2-3', 3), ('4-6', 4), ('7-7', 7), ('8-13', 10), ('14-14', 14), ('15-20', 14)]
CURVE_MAX = 2.0


def _shapes():
    per = defaultdict(dict)   # (L,k,p) -> {du: t/den}
    for s in S:
        if s.get('t') and s['du'] in (3, 4, 7, 10, 14):
            per[(s['L'], s['k'], s['p'])][s['du']] = s['t'] / s['du']
    out = defaultdict(list)   # (L,k) -> [(date, {band: shape})]
    for (L, k, p), v in per.items():
        if 14 not in v or len(v) < 3: continue
        pd = ISO(p)
        if dt.date(2026, 12, 20) <= pd <= dt.date(2026, 12, 29): continue
        run = v[14]; vals = {}
        for du in (14, 10, 7, 4, 3):
            if du in v:
                run = max(run, v[du]); vals[du] = run
        # jen pásma, pro která konkurence nabízí danou délku (chybějící se doplní z Prahy / sousední délky)
        out[(L, k)].append((pd, {band: min(CURVE_MAX, vals[du] / v[14]) for band, du in CURVE_DURS if du in vals}))
    return out


SHAPES = _shapes()


def shape_for(L, k, a, b):
    res = {}
    for band, _ in CURVE_DURS:
        for key in ((L, k), (L, 'C')):   # jen konkurence na téže pobočce
            lst = SHAPES.get(key) or []
            inp = [sh[band] for pd, sh in lst if a <= pd <= b and band in sh] or [sh[band] for pd, sh in lst if band in sh]
            if inp:
                res[band] = st.median(inp); break
        else:
            res[band] = 1.0
    order = [bb for bb, _ in CURVE_DURS]
    for i in range(len(order) - 2, -1, -1):   # kratší pásmo nikdy levnější než delší
        res[order[i]] = max(res[order[i]], res[order[i + 1]])
    return res if any(v > 1.0 for v in res.values()) else None


def length_curve(rows, changes, country):
    from reprice import TODAY
    oid2L = {v[2]: L for L, v in LOC.items() if v[0] == country}
    order = [b for b, _ in CURVE_DURS]
    out = []
    for r in rows:
        L = oid2L.get(r['Oid']); k = SIPP2K.get(r['S'])
        a, b = D(r['F']), D(r['T'])
        if not L or not k or b < TODAY or (a >= dt.date(2026, 12, 24) and b <= dt.date(2026, 12, 27)) \
                or any(r['D'].get(x) is None for x in order):
            out.append(r); continue
        sh = shape_for(L, k, max(a, TODAY), b)
        if not sh:
            out.append(r); continue
        d = dict(r['D']); base = min(d[x] for x in order)
        for x in order:
            d[x] = round(max(d[x], base * sh[x]), 2)
        for i in range(1, len(order)):      # €/den s délkou neroste
            d[order[i]] = min(d[order[i]], d[order[i - 1]])
        if all(abs(d[x] - r['D'][x]) < 0.005 for x in order):
            out.append(r); continue
        if r['D'].get('21-') is not None and abs(r['D']['21-'] - 3 * r['D']['7-7']) < 0.05:
            d['21-'] = round(3 * d['7-7'], 2)
        d['1-1'] = max(d['1-1'], d['2-3'])
        if a < TODAY:
            out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1)))); a = TODAY
        out.append(dict(r, F=fmt(a), D=d, new=True))
        changes.append(dict(L=L, S=r['S'], F=fmt(a), T=r['T'], old=r['D'], new=d, fac={'x': 'křivka délky dle konkurence'}))
    return out


# Erik 20.10.2026: žádný vůz pod 35 € za 1 den (pásmo 1-1, €/den bez DPH, i po slevě z pravidel obsazenosti)
MIN_1DAY = 35.0


def min_1day(rows, changes, country):
    from reprice import TODAY
    out = []
    for r in rows:
        fl = math.ceil(MIN_1DAY / max_discount(country, r['S']) * 100) / 100
        v = r['D'].get('1-1')
        if D(r['T']) < TODAY or v is None or v >= fl:
            out.append(r); continue
        a = D(r['F'])
        if a < TODAY:
            out.append(dict(r, T=fmt(TODAY - dt.timedelta(days=1)))); a = TODAY
        d = dict(r['D']); d['1-1'] = fl
        out.append(dict(r, F=fmt(a), D=d, new=True))
        changes.append(dict(L=r.get('L'), S=r['S'], F=fmt(a), T=r['T'], old={'1-1': v}, new={'1-1': fl}, fac={'x': 'min 1 den 35 €'}))
    return out


def check_continuity(rows):
    issues = []
    grp = defaultdict(list)
    for r in rows:
        grp[(r['S'], r.get('O', r.get('Oid')))].append((D(r['F']), D(r['T'])))
    for key, lst in grp.items():
        lst.sort()
        for (a1, b1), (a2, b2) in zip(lst, lst[1:]):
            if a2 != b1 + dt.timedelta(days=1):
                issues.append(f'{key}: {fmt(b1)} -> {fmt(a2)}')
        for a, b in lst:
            if b < a: issues.append(f'{key}: neg {fmt(a)}-{fmt(b)}')
    return issues


if __name__ == '__main__':
    res = {}
    for c in ('CZ', 'SK'):
        rows, ch, tabs = build(c)
        rows = step_cap(rows, ch, c)
        rows = apply_floor(rows, ch, c)
        rows = length_curve(rows, ch, c)
        if c == 'CZ':
            rows = pgar_from_igar(rows, ch)
        rows = mini_from_edmr(rows, ch)
        rows = min_1day(rows, ch, c)
        iss = check_continuity(rows)
        print(c, 'rows', len(rows), 'changed', len(ch), 'continuity issues', len(iss), iss[:10])
        res[c] = dict(rows=rows, changes=ch, tabs=tabs, issues=iss)
    json.dump(res, open(f'{BASE}/out/stage2.json', 'w'), default=str)
