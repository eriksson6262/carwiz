#!/usr/bin/env python3
"""Carwiz CW-PP repricing v3 (9.10.2026) – computes factors from DiscoverCars samples
and Renteon CW-POA availability, applies them to the LIVE CW-PP pricelist read from Renteon.
Input: data/CZ.json, data/SK.json, data/DC.json  -> output: out/result.json
"""
import json, statistics as st, datetime as dt, sys, os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda s: dt.datetime.strptime(s.strip('.'), '%d.%m.%Y').date()
ISO = lambda s: dt.date.fromisoformat(s)
fmt = lambda d: d.strftime('%d.%m.%Y.')

TODAY = dt.date.today()           # first repriced pickup day
WIN_END = dt.date(2027, 2, 28)         # repricing window end (existing period boundary)
XMAS = (dt.date(2026, 12, 24), dt.date(2026, 12, 27))
CLASSES = {'E': ['EDAR', 'EDMR', 'EWMR'],
           'C': ['CDAR', 'CDMR', 'CFAR', 'CFMR', 'CKMR', 'CWAR'],
           'I': ['IDAR', 'IGAR', 'IGMR', 'IWAR', 'IFAR'],
           'F': ['FDAR', 'FFAR', 'FWAR'],
           # Erik 12.10.2026: nové skupiny jen pro Prahu – GFAR = premium (konkurence P/U/G automaty),
           # LFAR (BMW X4) = také proti premium (luxury pool na DC = S-třída apod., nesrovnatelné), dodávky = VAN (2. písmeno V): automaty proti automatickým vanům,
           # PGAR = IGAR × 1,10, SVMR = SVAR × 0,95 (build.derive_from).
           'PREM': ['GFAR'], 'PREML': ['LFAR'], 'VANP': ['PVAR'], 'VANA': ['SVAR']}
NEW_K = {'PREM', 'PREML', 'VANP', 'VANA'}
COMPKEY = {'VANP': 'VANA', 'PREML': 'PREM'}
SIPP2K = {s: k for k, l in CLASSES.items() for s in l}
BANDS = ['1-1', '2-3', '4-6', '7-7', '8-13', '14-14', '15-20', '21-']
BMIN = {'1-1': 1, '2-3': 2, '4-6': 4, '7-7': 7, '8-13': 8, '14-14': 14, '15-20': 15, '21-': 21}
BMAX = {'1-1': 1, '2-3': 3, '4-6': 6, '7-7': 7, '8-13': 13, '14-14': 14, '15-20': 20, '21-': 21}
DUR2BAND = {3: '2-3', 4: '4-6', 7: '7-7', 10: '8-13', 14: '14-14'}
LOC = {'PRG': ('CZ', 25, None), 'OSR': ('CZ', 26, 26), 'BTS': ('SK', 128, None)}
VAT = {'CZ': 1.21, 'SK': 1.23}


def rule_mult(country, u):
    if u is None:
        return 1.0
    if country == 'CZ':
        return 0.7 if u < 51 else 0.85 if u < 71 else 1.0 if u < 86 else 1.15 if u < 95 else 1.5
    return 0.4 if u < 71 else 1.0 if u < 85 else 2.0


FALLBACK = False
PRG_MODE = os.environ.get('PRG_MODE', 'excl')   # 'excl' (od 19.10.2026) | 'rank3' (dřívější cíl ≈3. místo)
PRG_ALLOWED_CHEAPER = {'RENT PLUS', 'NUCARRENTALS'}
PRG_UNDER = float(os.environ.get('PRG_UNDER', '0.97'))
OSR_MODE = os.environ.get('OSR_MODE', 'target')   # Erik 19.10.2026 (odpoledne): Ostrava nejlevnější všude, ale ne o moc; 'flat' = plošně OSR_MAX_F
OSR_UNDER = float(os.environ.get('OSR_UNDER', '0.97'))
OSR_MAX_F = float(os.environ.get('OSR_MAX_F', '0.90'))   # Erik 19.10.2026


def load():
    global FALLBACK
    cz = json.load(open(f'{BASE}/data/CZ.json'))
    FALLBACK = cz.get('MODE') == 'fallback'
    sk = json.load(open(f'{BASE}/data/SK.json'))
    dc = json.load(open(f'{BASE}/data/DC.json'))
    return cz, sk, dc


def overlaps_xmas(p, du):
    a = p; b = p + dt.timedelta(days=du)
    return a <= XMAS[1] and b >= XMAS[0]


def build_samples(cz, sk, dc):
    ra = {}
    for src in (cz, sk):
        for r in src['RA']:
            ra[(r['o'], r['p'], r['du'])] = r['m']
    S = []
    for r in dc['res']:
        L = r['L']; country, office, _ = LOC[L]
        m = ra.get((office, r['p'], r['du']), {})
        for k in CLASSES:
            if k in NEW_K and L != 'PRG':
                continue
            if k in NEW_K:
                cw = {s: v for s, v in r['cw'].items() if s in CLASSES[k]}
            else:
                cw = {s: v for s, v in r['cw'].items() if s[0] == k}
            cwS = min(cw, key=cw.get) if cw else None
            pool = list(r['comp'].get(COMPKEY.get(k, k), []))
            if k == 'F' and L != 'PRG':
                pool += r['comp'].get('S', [])
            pool.sort(key=lambda x: x[0])
            seen = set(); pp = []
            for x in pool:
                if x[1] in seen: continue
                seen.add(x[1]); pp.append(x)
            # Renteon reference SIPP: Carwiz SIPP shown, else cheapest class SIPP in Renteon
            refS = cwS
            if refS is None or refS not in m:
                cands = [s for s in CLASSES[k] if s in m and s[2] == 'A'] or [s for s in CLASSES[k] if s in m]
                refS = min(cands, key=lambda s: m[s][0]) if cands else None
            R, u = (m[refS][0], m[refS][1]) if refS in m else (None, None)
            if not pp and cwS is None:
                continue
            S.append(dict(L=L, country=country, p=r['p'], du=r['du'], k=k, cwS=cwS,
                          dc=cw.get(cwS) if cwS else None, refS=refS, R=R, u=u,
                          comp=[[round(x[0], 2), x[1], x[2]] for x in pp[:6]],
                          budget=next((x[0] for x in pp if 'budget' in x[1].lower()), None)))
    return S


def fit(S):
    """DC = k*R + b per location x class (least squares, excl. Xmas & 13.11 4-day)."""
    res = {}
    grp = defaultdict(list)
    for s in S:
        if s['dc'] and s['R']:
            p = ISO(s['p'])
            if overlaps_xmas(p, s['du']): continue
            if p == dt.date(2026, 11, 13) and s['du'] == 4: continue
            if s['du'] >= 21: continue   # 21- band is fixed at 3x 7-7 (Erik 7.10.)
            grp[(s['L'], s['k'])].append((s['R'], s['dc']))
    for key, pts in grp.items():
        n = len(pts)
        if n >= 8:
            mx = st.mean(x for x, _ in pts); my = st.mean(y for _, y in pts)
            sxx = sum((x - mx) ** 2 for x, _ in pts)
            k = sum((x - mx) * (y - my) for x, y in pts) / sxx if sxx else 0
            b = my - k * mx
            ok = 0.8 <= k <= 2.6 and -30 <= b <= 60
        else:
            ok = False
        if not ok:
            k = st.median(y / x for x, y in pts) if pts else 1.3; b = 0.0
        resid = [y - (k * x + b) for x, y in pts]
        res[key] = dict(k=round(k, 4), b=round(b, 2), n=n, mode='lin' if ok else 'ratio',
                        mape=round(st.mean(abs(e) / y for e, (_, y) in zip(resid, pts)) * 100, 1) if pts else None)
    return res


def targets(S):
    # Prague / Bratislava direct
    for s in S:
        c = [x[0] for x in s['comp']]
        s['t'] = None
        if s['L'] == 'PRG' and c:
            if PRG_MODE == 'excl':
                # Erik 19.10.2026: v Praze smí být levnější jen RENT PLUS a NUCarrentals
                cx = [x[0] for x in s['comp'] if x[1].upper() not in PRG_ALLOWED_CHEAPER]
                t = PRG_UNDER * cx[0] if cx else None
            elif len(c) >= 3:
                t = max(0.97 * c[2], min(c[1] + 1, c[2] - 0.5))
            elif len(c) == 2:
                t = c[1]
            else:
                t = c[0]
            s['t'] = t
        elif s['L'] == 'BTS' and c:
            s['t'] = 0.95 * c[0]
    # Ostrava = Prague target x coefficient (min over dates of (Budget-10%)/Prague target)
    prg = {(s['p'], s['du'], s['k']): s['t'] for s in S if s['L'] == 'PRG' and s['t']}
    ratios = defaultdict(list)
    for s in S:
        if s['L'] == 'OSR' and s['budget'] and prg.get((s['p'], s['du'], s['k'])):
            if overlaps_xmas(ISO(s['p']), s['du']): continue
            ratios[(s['k'], s['du'])].append(0.9 * s['budget'] / prg[(s['p'], s['du'], s['k'])])
    coef = {}
    for key, v in ratios.items():
        v = sorted(v)
        # lowest ratio, but ignore the single most extreme outlier when we have enough points
        coef[key] = v[1] if len(v) >= 6 else v[0]
    for s in S:
        if s['L'] == 'OSR' and OSR_MODE == 'target':
            s['t'] = OSR_UNDER * s['comp'][0][0] if s['comp'] else None
            continue
        if s['L'] == 'OSR':
            if not s['comp']:      # no competitor offer for this date/length -> no target
                continue
            pt = prg.get((s['p'], s['du'], s['k']))
            cf = coef.get((s['k'], s['du']))
            if pt and cf:
                s['t'] = pt * cf
                if s['comp']:   # must stay the cheapest at the airport (Budget, Hertz, Thrifty)
                    s['t'] = min(s['t'], 0.97 * s['comp'][0][0])
            elif s['comp']:
                s['t'] = 0.95 * s['comp'][0][0]
    return coef


def factors(S, F):
    for s in S:
        s['f'] = None
        kb = F.get((s['L'], s['k']))
        if not (s['t'] and s['R'] and kb) or s['du'] >= 21:
            continue
        k, b = kb['k'], kb['b']
        dcn = s['dc'] if s['dc'] else k * s['R'] + b
        s['dc_used'] = dcn
        m = rule_mult(s['country'], s['u'])
        if s['refS'] == 'GFAR':   # GFAR: bez slev, +100 % od 51 %
            m = 2.0 if (s['u'] or 0) >= 51 else 1.0
        s['mult'] = m
        teff = s['t'] * (m if m > 1 else 1)
        f = 1 + (teff - dcn) / (k * s['R'])
        if m > 1:
            f = min(f, 1.0)
        # nouzový režim (bez obsazenosti z Renteonu): v nejbližších 14 dnech může být DC zvýšená přirážkou
        # z obsazenosti -> v tomto okně jen zdražovat/ponechat, nezlevňovat
        if FALLBACK and s['u'] is None and ISO(s['p']) < TODAY + dt.timedelta(days=14):
            f = max(f, 1.0)
        # Erik 19.10.2026: Ostrava trochu snížit (potřebujeme víc rezervací) -> plošně OSR_MAX_F (−10 %),
        # cíl pozice se v Ostravě dočasně nepoužívá (jsme 30–50 % pod nejlevnějším konkurentem)
        if s['L'] == 'OSR' and OSR_MODE == 'flat':
            f = OSR_MAX_F
        s['f_raw'] = f
        s['f'] = max(0.5, min(2.0, f))


def period_rows(PL, oid, sipps):
    return [r for r in PL if r['Oid'] == oid and r['S'] in sipps]


def apply(PL, S, L, coef_osr_e_as_c=True):
    """Return new PL rows (list) for whole pricelist, with repriced rows for location L."""
    country, office, oid = LOC[L]
    # periods (from any repriced SIPP, e.g. first class SIPP present)
    out_log = []
    # sample factors per class, period, band
    samp = defaultdict(list)
    for s in S:
        if s['L'] != L or s['f'] is None: continue
        samp[(s['k'], ISO(s['p']), s['du'])].append(s['f'])
    new = []
    changed = {}
    # helper to compute factor for class k, period (a,b), band
    def fac(k, a, b, band, allf):
        durs = [d for d, bb in DUR2BAND.items() if bb == band]
        if band == '15-20':
            durs = [14, 21]
        v = [f for (kk, p, du), fl in samp.items() if kk == k and a <= p <= b and du in durs for f in fl]
        return st.mean(v) if v else None, len(v)
    for k in CLASSES:
        kk = k
        if L == 'OSR' and k == 'E': kk = 'C'
        if L == 'BTS' and k == 'E': continue
        # medians per band across window
        med = {}
        for band in BANDS[1:7]:
            durs = [14, 21] if band == '15-20' else [d for d, bb in DUR2BAND.items() if bb == band]
            v = [f for (c, p, du), fl in samp.items() if c == kk and du in durs for f in fl]
            med[band] = st.median(v) if v else 1.0
        changed[k] = dict(med=med, periods={})
    return samp, changed


def expand(x):
    if x.get('res') and isinstance(x['res'][0], list):
        sup = x['sup']
        x['res'] = [dict(L=L, p=pd, du=du, cw=cw,
                         comp={k: [[c[0], sup[c[1]] if isinstance(c[1], int) else c[1], c[2]] for c in v] for k, v in comp.items()})
                    for L, pd, du, cw, comp in x['res']]
    return x


# Erik 19.10.2026: Carwiz se prodává i přes CarTrawler (easyJet, Wizz Air) – cíle musí platit i tam.
# Každý kanál má vlastní kalibraci DC≈k·R+b; pro vzorek (pobočka, datum, délka, třída) se bere nejnižší faktor.
CHANNELS = [c for c in os.environ.get('CHANNELS', 'DC,CT,WZ,RC').split(',') if c]

if __name__ == '__main__':
    cz, sk, dc = load()
    dc = expand(dc)
    S = build_samples(cz, sk, dc)
    F = fit(S)
    coef = targets(S)
    factors(S, F)
    for s in S: s['ch'] = 'DC'
    extra = {}
    for ch in CHANNELS:
        if ch == 'DC' or not os.path.exists(f'{BASE}/data/{ch}.json'): continue
        Sx = build_samples(cz, sk, expand(json.load(open(f'{BASE}/data/{ch}.json'))))
        Fx = fit(Sx); targets(Sx); factors(Sx, Fx)
        for key, v in sorted(Fx.items()): print(ch, key, v)
        for s in Sx:
            if s['f'] is not None:
                extra.setdefault((s['L'], s['p'], s['du'], s['k']), []).append((s['f'], ch))
    for s in S:
        alt = extra.get((s['L'], s['p'], s['du'], s['k']), [])
        if s['f'] is not None: alt = alt + [(s['f'], 'DC')]
        if alt:
            f, ch = min(alt)
            s['f_dc'] = s['f']; s['f'] = f; s['ch'] = ch
    json.dump(dict(S=S, F={f'{a}|{b}': v for (a, b), v in F.items()},
                   coef={f'{a}|{b}': v for (a, b), v in coef.items()}),
              open(f'{BASE}/out/stage1.json', 'w'), default=str)
    for key, v in sorted(F.items()): print(key, v)
    print('coef OSR', {k: round(v, 3) for k, v in sorted(coef.items())})
