#!/usr/bin/env python3
"""Stage 3: estimates after import + KONTROLA workbooks + IMPORT workbooks.
If a Renteon export template is available (argv TEMPLATE_CZ / TEMPLATE_SK env), its header sheet
and column order are copied; otherwise a reconstructed layout is used."""
import json, os, sys, datetime as dt, statistics as st
from collections import defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
sys.path.insert(0, os.path.dirname(__file__))
from reprice import BASE, D, ISO, fmt, CLASSES, SIPP2K, BANDS, DUR2BAND, LOC, rule_mult

RUN = os.environ.get('RUN_DATE', '2026-10-09')
OUT = f'{BASE}/out/xlsx'; os.makedirs(OUT, exist_ok=True)
st1 = json.load(open(f'{BASE}/out/stage1.json')); st2 = json.load(open(f'{BASE}/out/stage2.json'))
S = st1['S']; F = {tuple(k.split('|')): v for k, v in st1['F'].items()}
cz = json.load(open(f'{BASE}/data/CZ.json')); sk = json.load(open(f'{BASE}/data/SK.json'))
HDR = Font(bold=True, color='FFFFFF'); HFILL = PatternFill('solid', fgColor='305496')
GREEN = PatternFill('solid', fgColor='E2EFDA'); RED = PatternFill('solid', fgColor='FCE4D6'); YEL = PatternFill('solid', fgColor='FFF2CC')


def header(ws, cols, widths=None):
    ws.append(cols)
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=ws.max_row, column=i); cell.font = HDR; cell.fill = HFILL
        cell.alignment = Alignment(wrap_text=True, vertical='center')
        ws.column_dimensions[get_column_letter(i)].width = (widths[i - 1] if widths else max(9, len(str(c)) + 2))
    ws.freeze_panes = ws.cell(row=ws.max_row + 1, column=1)


# ---------- ratio lookup old->new per (L, SIPP, date, band)
def ratio_lookup(country):
    old = defaultdict(list); new = defaultdict(list)
    src = cz if country == 'CZ' else sk
    oid2L = {v[2]: L for L, v in LOC.items() if v[0] == country}
    for r in src['PL']:
        old[(oid2L.get(r['Oid']), r['S'])].append((D(r['F']), D(r['T']), r['D']))
    for r in st2[country]['rows']:
        new[(oid2L.get(r['Oid']), r['S'])].append((D(r['F']), D(r['T']), r['D']))
    def get(tab, L, s, d):
        for a, b, dd in tab.get((L, s), []):
            if a <= d <= b: return dd
    return lambda L, s, d, band: (get(old, L, s, d) or {}).get(band), lambda L, s, d, band: (get(new, L, s, d) or {}).get(band)


LK = {c: ratio_lookup(c) for c in ('CZ', 'SK')}


def band_for(du):
    return DUR2BAND.get(du) or ('21-' if du >= 21 else '4-6' if du == 5 else None)


def pos(price, comps):
    if price is None: return None
    return 1 + sum(1 for c in comps if c < price)


for s in S:
    L = s['L']; c = s['country']; band = band_for(s['du'])
    sipp = s['cwS'] or s['refS']
    s['ratio'] = None; s['dc_new'] = None
    if sipp and band:
        o = LK[c][0](L, sipp, ISO(s['p']), band); n = LK[c][1](L, sipp, ISO(s['p']), band)
        if o and n:
            s['ratio'] = n / o
            kb = F.get((L, s['k']))
            base = s['dc'] if s['dc'] else (kb['k'] * s['R'] + kb['b'] if kb and s['R'] else None)
            if base is not None and kb and s['R']:
                s['dc_new'] = base + kb['k'] * s['R'] * (s['ratio'] - 1)
    comps = [x[0] for x in s['comp']]
    s['pos_now'] = pos(s['dc'], comps); s['pos_new'] = pos(s['dc_new'], comps) if s['dc'] else None


# ---------- occupancy monthly
def occ_month(FA, office):
    res = {}
    for sipp, v in FA[str(office)].items():
        d0 = D(v['d0']); m = defaultdict(list)
        for i, (t, b) in enumerate(zip(v['T'], v['B'])):
            d = d0 + dt.timedelta(days=i)
            if t: m[d.strftime('%Y-%m')].append(b / t)
        res[sipp] = (max(v['T']) if v['T'] else 0, {k: round(100 * st.mean(x)) for k, x in m.items()})
    return res


NOTES = {
    'PRG': ['Cíl (Erik 19.10.2026): levnější smí být jen RENT PLUS a NUCarrentals – 3 % pod nejlevnějším ostatním konkurentem stejné velikosti, platí na DiscoverCars i CarTrawler (easyJet, Wizz Air); bere se nejpřísnější kanál.',
            'Nejlevnější konkurenti v Praze: DiscoverCars choice, RENT PLUS, NUCarrentals (téměř ve všech termínech).',
            'DC ≈ k·Renteon(CW-POA s DPH po pravidlech) + b; fit viz list Kalibrace. 21denní vzorky vyřazeny (pásmo 21- = 3× 7-7 dle Erika).',
            'Odhad DC po importu = DC + k·R·(nová/stará cena − 1). Pozice = pořadí mezi konkurenty (1 = nejlevnější).'],
    'OSR': ['Cíl (Erik 19.10.2026): nejlevnější všude, ale ne o moc – 3 % pod nejlevnějším konkurentem stejné velikosti, na DiscoverCars i CarTrawler (easyJet, Wizz Air); bere se nejpřísnější kanál.',
            'Minima CZ po slevě z obsazenosti (19.10.2026): E 5 / C 5,5 / I 6,5 / F 13 €/den bez DPH, GFAR 65 €.',
            'E = jako C (Ostrava nemá E flotilu). C/I od ledna bez flotily → beze změny.'],
    'BTS': ['Cíl: 5 % pod nejlevnějším konkurentem stejné velikosti (F = Full-size + Standard).',
            'E beze změny. F (FFAR) na DiscoverCars bez nabídky Carwiz → beze změny (jen 21- ×3).',
            'SK pravidla: −60 % do 70 % obsazenosti, +100 % od 85 %, Vánoce +300 % povinné 24.–27.12.',
            'SK ceník 25.–29.12. měl základ ~6× + nové pravidlo +300 % = dvojitá přirážka → 25.–27.12. srovnáno na 30.12., 28.–29.12. ponecháno.',
            'SK 21- pásmo dosud = 1× 7-7 (import v3 ze 7.10. se neprojevil) → nyní ×3 ve všech budoucích řádcích.'],
}


if cz.get('MODE') == 'fallback':
    for _L in NOTES:
        NOTES[_L].insert(0, 'NOUZOVÝ REŽIM: Renteon nebyl přihlášen – výchozí ceník = poslední import (12.10.), pravidla dle stavu 12.10., '
                            'Renteon cena R odvozena z DC Carwiz přes kalibraci 12.10. (R=(DC−b)/k), obsazenost neznámá; '
                            'u vyzvednutí do 14 dnů se nezlevňuje (možná přirážka z obsazenosti).')


def kontrola(L):
    country, office, oid = LOC[L]
    wb = Workbook(); ws = wb.active; ws.title = 'Souhrn'
    ws.append([f'KONTROLA {L} – běh {RUN} (DiscoverCars + Renteon CW-POA, čtení)']); ws['A1'].font = Font(bold=True, size=13)
    ws.append([])
    header(ws, ['Třída', 'Délka', 'Vzorků', 'Carwiz zobrazen', 'Ø DC teď €', 'Ø cíl €', 'Ø DC po importu €', 'Ø pozice teď', 'Ø pozice po', 'Ø faktor', 'Drazí než cíl o %'],
           [8, 7, 8, 10, 11, 10, 13, 11, 11, 9, 12])
    g = defaultdict(list)
    for s in S:
        if s['L'] == L: g[(s['k'], s['du'])].append(s)
    for (k, du), l in sorted(g.items()):
        dcs = [x['dc'] for x in l if x['dc']]; ts = [x['t'] for x in l if x['t']]
        dn = [x['dc_new'] for x in l if x['dc_new']]
        pn = [x['pos_now'] for x in l if x['pos_now']]; pp = [x['pos_new'] for x in l if x['pos_new']]
        fs = [x['f'] for x in l if x['f'] is not None]
        over = [x['dc'] / x['t'] - 1 for x in l if x['dc'] and x['t']]
        ws.append([k, du, len(l), len(dcs), round(st.mean(dcs), 1) if dcs else None, round(st.mean(ts), 1) if ts else None,
                   round(st.mean(dn), 1) if dn else None, round(st.mean(pn), 1) if pn else None, round(st.mean(pp), 1) if pp else None,
                   round(st.mean(fs), 2) if fs else None, round(100 * st.median(over), 1) if over else None])
    ws.append([]); ws.append(['Poznámky'])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    for n in NOTES[L]: ws.append([n])

    w2 = wb.create_sheet('Vzorky')
    header(w2, ['Vyzvednutí', 'Dní', 'Třída', 'Carwiz SIPP', 'DC Carwiz teď €', 'Renteon SIPP', 'Renteon CW-POA €', 'Obsaz. %', 'Pravidlo ×',
                '1. konk.', '€', '2. konk.', '€', '3. konk.', '€', '4. €', 'Budget €', 'Cíl €', 'Faktor', 'Nová/stará cena', 'DC po importu €', 'Pozice teď', 'Pozice po'],
           [11, 5, 6, 9, 10, 9, 10, 8, 8, 16, 8, 16, 8, 16, 8, 8, 9, 8, 7, 9, 10, 8, 8])
    for s in sorted([x for x in S if x['L'] == L], key=lambda x: (x['k'], x['p'], x['du'])):
        c = s['comp'] + [[None, None, None]] * 4
        row = [ISO(s['p']), s['du'], s['k'], s['cwS'], s['dc'], s['refS'], s['R'], s['u'], s.get('mult'),
               c[0][1], c[0][0], c[1][1], c[1][0], c[2][1], c[2][0], c[3][0], s['budget'],
               round(s['t'], 2) if s['t'] else None, round(s['f'], 3) if s['f'] is not None else None,
               round(s['ratio'], 3) if s['ratio'] else None, round(s['dc_new'], 2) if s['dc_new'] else None, s['pos_now'], s['pos_new']]
        w2.append(row)
        w2.cell(row=w2.max_row, column=1).number_format = 'DD.MM.YYYY'
        if s['dc'] is None: w2.cell(row=w2.max_row, column=5).fill = YEL
    w2.auto_filter.ref = w2.dimensions

    w3 = wb.create_sheet('Změny cen')
    header(w3, ['SIPP', 'Od', 'Do'] + [f'staré {b}' for b in BANDS] + [f'nové {b}' for b in BANDS] + ['Δ 7-7 %'], [8, 11, 11] + [8] * 16 + [8])
    for ch in st2[country]['changes']:
        if ch['L'] != L: continue
        o, n = ch['old'], ch['new']
        d77 = round(100 * (n['7-7'] / o['7-7'] - 1), 1) if o.get('7-7') else None
        w3.append([ch['S'], ch['F'], ch['T']] + [o.get(b) for b in BANDS] + [n.get(b) for b in BANDS] + [d77])
        if d77 is not None:
            w3.cell(row=w3.max_row, column=20).fill = GREEN if d77 < 0 else RED if d77 > 0 else PatternFill()
    w3.auto_filter.ref = w3.dimensions

    w4 = wb.create_sheet('Faktory období')
    header(w4, ['Třída', 'Období', '2-3', '4-6', '7-7', '8-13', '14-14', '15-20'], [7, 26, 8, 8, 8, 8, 8, 8])
    rows = defaultdict(dict)
    for key, v in st2[country]['tabs'][L].items():
        k, p, b = key.split('|'); rows[(k, p)][b] = round(v, 3)
    for (k, p), d in sorted(rows.items(), key=lambda x: (x[0][0], D(x[0][1].split('-')[0]))):
        w4.append([k, p] + [d.get(b) for b in ['2-3', '4-6', '7-7', '8-13', '14-14', '15-20']])

    w5 = wb.create_sheet('Obsazenost')
    FA = (cz if country == 'CZ' else sk)['FA']
    om = occ_month(FA, office)
    months = sorted({m for _, (_, d) in om.items() for m in d})
    header(w5, ['SIPP', 'Vozů (max)'] + months, [10, 10] + [9] * len(months))
    for sipp, (n, d) in om.items():
        w5.append([sipp, n] + [d.get(m) for m in months])
        for j, m in enumerate(months):
            v = d.get(m)
            if v is not None and v >= 95: w5.cell(row=w5.max_row, column=3 + j).fill = RED
            elif v is not None and v <= 50: w5.cell(row=w5.max_row, column=3 + j).fill = GREEN

    w6 = wb.create_sheet('Pravidla')
    header(w6, ['Id', 'Úprava %', 'Obsazenost od', 'do', 'Kategorie', 'Délky', 'Povinné', 'Období od', 'do', 'Platí do', 'Změněno'], [7, 9, 10, 8, 40, 8, 8, 12, 12, 18, 30])
    for r in (cz if country == 'CZ' else sk)['RULES']:
        w6.append([r['Id'], r['PriceAdjustmentPercentage'], r['UtilizationPercentageFrom'], r['UtilizationPercentageTo'],
                   'VŠE' if r['IsAllCarCategories'] else r['CarCategoriesText'], r['Durations'], 'ANO' if r['ForceApply'] else '',
                   r['PeriodFrom'], r['PeriodTo'], r['ValidTo'], r['Modification']])

    w7 = wb.create_sheet('Kalibrace')
    header(w7, ['Pobočka', 'Třída', 'k', 'b €', 'n', 'metoda', 'MAPE %'], [9, 7, 8, 8, 6, 8, 8])
    for (l, k), v in sorted(F.items()):
        if l == L: w7.append([l, k, v['k'], v['b'], v['n'], v['mode'], v['mape']])
    if L == 'OSR':
        w7.append([]); w7.append(['Koeficient Ostrava (třída|délka)', 'hodnota'])
        for key, v in sorted(st1['coef'].items()): w7.append([key, round(v, 3)])
    path = f'{OUT}/{RUN}_KONTROLA_{ {"PRG": "Praha", "OSR": "Ostrava", "BTS": "Bratislava"}[L] }.xlsx'.replace('{ ', '{').replace(' }', '}')
    path = f'{OUT}/{RUN}_KONTROLA_' + {"PRG": "Praha", "OSR": "Ostrava", "BTS": "Bratislava"}[L] + '.xlsx'
    wb.save(path); return path


def dparse(s):
    return D(s)


def import_wb(country):
    """Renteon export format: header sheet copied from the last export (template), sheet 'Ceny'
    with rows from TODAY on (like an export 'Datum od' TODAY)."""
    from reprice import TODAY
    rows = st2[country]['rows']
    tpl = os.environ.get(f'TEMPLATE_{country}')
    cols = ['ServiceName', 'Office', 'DateFrom', 'DateTo'] + BANDS + ['DiscountPercentage']
    if tpl and os.path.exists(tpl):
        wb = load_workbook(tpl)
        h = wb.worksheets[0]
        for row in h.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.strip().lower() in ('datum', 'dátum', 'datum od', 'dátum od'):
                    h.cell(row=c.row, column=c.column + 1).value = TODAY.strftime('%d.%m.%Y.')
        ws = wb['Ceny']; cols = [c.value for c in ws[1]]
        ws.delete_rows(2, ws.max_row)
    else:
        wb = Workbook(); h = wb.active; h.title = 'Ceník CW-PP'
        for kv in [(None,), ('datum', TODAY.strftime('%d.%m.%Y.')), (None,), ('Název', 'CW-PP', None, 'Kód', 'CW-PP'),
                   ('Ceny s DPH', 'False'), ('Datum od', TODAY.strftime('%d.%m.%Y.'))]:
            h.append(list(kv))
        ws = wb.create_sheet('Ceny'); ws.append(cols)
    officeName = {None: None, 26: 'OSR'}
    for r in sorted(rows, key=lambda r: (r['S'], D(r['F']), r['Oid'] or 0)):
        a, b = D(r['F']), D(r['T'])
        if b < TODAY: continue
        a = max(a, TODAY)
        rec = {'ServiceName': r['S'], 'Office': officeName.get(r['Oid'], r.get('O')), 'DateFrom': dt.datetime.combine(a, dt.time()),
               'DateTo': dt.datetime.combine(b, dt.time()), 'DiscountPercentage': r.get('disc')}
        rec.update({bb: r['D'].get(bb) for bb in BANDS})
        ws.append([rec.get(c) for c in cols])
        for j, c in enumerate(cols, 1):
            if c in ('DateFrom', 'DateTo'): ws.cell(row=ws.max_row, column=j).number_format = 'dd.MM.yyyy.'
    name = 'CZ_Praha+Ostrava' if country == 'CZ' else 'SK_Bratislava'
    path = f'{OUT}/{RUN}_IMPORT_CW-PP_{name}.xlsx'
    wb.save(path); return path


if __name__ == '__main__':
    out = [import_wb('CZ'), import_wb('SK')] + [kontrola(L) for L in ('PRG', 'OSR', 'BTS')]
    for p in out: print(p)
    json.dump([{k: v for k, v in s.items()} for s in S], open(f'{BASE}/out/stage3_samples.json', 'w'), default=str)
