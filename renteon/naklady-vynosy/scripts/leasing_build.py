import json, re, csv, os, sys, datetime as dt, calendar
from collections import defaultdict

D = sys.argv[1]
pk = json.load(open(os.path.join(D, 'pk_parsed.json')))
xl = json.load(open(os.path.join(D, 'xlsx_vozy.json')))
xmap = {}
for o in xl:
    xmap.setdefault(o['smlouva'], o)

# registry: contract -> (email_id, date, category, att_id, att_name)
reg = {}
for line in open(os.path.join(D, 'registry.tsv'), encoding='utf-8'):
    eid, edate, cat, atts = line.rstrip('\n').split('\t')
    for a in atts.split(','):
        aid, name = a.split(':', 1)
        reg[name[:7]] = dict(eid=eid, edate=edate, cat=cat, aid=aid, name=name)

def d(s):
    dd, mm, yy = s.split('.')
    return dt.date(int(yy), int(mm), int(dd))

def typ_for(c):
    r = reg[c]; n = r['name']; cat = r['cat']
    firma = (xmap.get(c, {}).get('firma') or '')
    fl = firma.lower()
    if 'GALKIN' in n.upper() or 'GLACIES' in n.upper() or cat == 'glacies' or 'glacies' in fl:
        return 'Glacies'
    if cat.startswith('zpetna') or 'k fakt' in n or 'k faktuaci' in n or 'k faturaci' in n:
        return 'zpětná fakturace – prodloužení' if ('prodlou' in n or 'prodlou' in fl) else 'zpětná fakturace'
    if 'Maďar' in n or 'Maďr' in n or 'maďar' in fl:
        return 'napřímo – Maďarsko'
    if 'prodlou' in n or 'prodlou' in fl:
        return 'prodloužení'
    return 'napřímo'

rows = []
smlouvy = []
for c, v in sorted(pk.items()):
    r = reg[c]
    t = typ_for(c)
    konec = d(v['konec']).isoformat() if v['konec'] else ''
    amts = []
    for row in v['rows']:
        du = d(row['duzp'])
        amt = round(row['zaklad'] + row['nul'], 2)
        amts.append(amt)
        rows.append(dict(mesic=du.strftime('%Y-%m'), spz=v['rz'], castka_bez_dph=amt, dodavatel='HAVEX Mobility s.r.o.',
                         typ=t, smlouva=c, stredisko=v['stredisko'] or '', konec_smlouvy=konec,
                         zdroj_email_id=r['eid'], soubor='PK %s.pdf (att %s)' % (r['name'], r['aid'])))
    x = xmap.get(c)
    zac = x['zacatek'] if x and x['zacatek'] else (d(v['rows'][0]['duzp']).isoformat() if v['rows'] else '')
    smlouvy.append(dict(smlouva=c, spz=v['rz'], dodavatel='HAVEX Mobility s.r.o.', typ=t, zacatek=zac, konec=konec,
                        mesicni_splatka_bez_dph=max(amts) if amts else 0, pocet_radku=len(amts), zdroj_email_id=r['eid']))

# EURO FLEET SERVIS - RX Auto invoices
efs_email = {'3900250104': '41607', '3900250114': '41085', '3900260012': '40418', '3900260029': '39688',
             '3900260073': '38740', '3900260097': '37707', '3900260135': '35062', '3900260190': '31480', '3900260249': '24858'}
num = r'-?\d{1,3}(?:[  ]\d{3})*,\d{2}'
item = re.compile(r'Půjčov\s*né\s+Škoda\s+(\w+)\s+([0-9A-Z]{3}\s?[0-9A-Z]{4})\s*/\s*([0-9.]+)\s*-\s*([0-9.]*)\s+1\s+21\s+(' + num + r')\s+(' + num + r')\s+(' + num + r')\s+(' + num + ')')
def n(s): return float(s.replace(' ', '').replace(' ', '').replace(',', '.'))
efs_by_spz = defaultdict(list)
efs_check = {}
for vs, eid in efs_email.items():
    t = open(os.path.join(D, 'efs', vs + '.txt'), encoding='utf-8').read()
    duzp = re.search(r'DUZP \(DPPD,DUP\)\s+([0-9.]+)', t).group(1)
    m = d(duzp).strftime('%Y-%m')
    tot = 0
    for it in item.finditer(t):
        spz = it.group(2).replace(' ', '').upper()
        amt = n(it.group(7)); tot += amt
        rows.append(dict(mesic=m, spz=spz, castka_bez_dph=amt, dodavatel='EURO FLEET SERVIS s.r.o.', typ='EFS nájem (Škoda %s)' % it.group(1),
                         smlouva='EFS-' + spz, stredisko='', konec_smlouvy='', zdroj_email_id=eid, soubor='VFA%s Faktura.pdf' % vs))
        efs_by_spz[spz].append((m, amt, eid, it.group(3), it.group(4)))
    zd = n(re.search(r'ZD zákl\.sazba\s+(' + num + ')', t).group(1))
    efs_check[vs] = (round(tot, 2), zd)
for spz, lst in sorted(efs_by_spz.items()):
    lst.sort()
    smlouvy.append(dict(smlouva='EFS-' + spz, spz=spz, dodavatel='EURO FLEET SERVIS s.r.o.', typ='EFS nájem',
                        zacatek=d(lst[0][3]).isoformat(), konec=d(lst[-1][4]).isoformat() if lst[-1][4] else '',
                        mesicni_splatka_bez_dph=max(a for _, a, _, _, _ in lst), pocet_radku=len(lst), zdroj_email_id=lst[0][2]))

cols = ['mesic', 'spz', 'castka_bez_dph', 'dodavatel', 'typ', 'smlouva', 'stredisko', 'konec_smlouvy', 'zdroj_email_id', 'soubor']
rows.sort(key=lambda r: (r['mesic'], r['spz'], r['smlouva']))
with open(os.path.join(D, 'leasing.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
scols = ['smlouva', 'spz', 'dodavatel', 'typ', 'zacatek', 'konec', 'mesicni_splatka_bez_dph', 'pocet_radku', 'zdroj_email_id']
with open(os.path.join(D, 'leasing_smlouvy.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, scols); w.writeheader(); w.writerows(smlouvy)

# ---- estimate for xlsx contracts without PK
P0, P1 = dt.date(2024, 1, 1), dt.date(2026, 10, 31)
est = []; est_contracts = []
pk_spz_months = {(r['spz'], r['mesic']) for r in rows}
overlap = 0
for o in xl:
    c = o['smlouva']
    if c in pk or not o['zacatek'] or not o['cena']:
        continue
    try:
        z = dt.date.fromisoformat(o['zacatek'][:10])
        k = dt.date.fromisoformat(o['konec'][:10]) if o['konec'] and o['konec'][:4].isdigit() else P1
    except Exception:
        continue
    pozn = str(o.get('pozn') or '')
    mu = re.search(r'ukon[čc]en[oa]?\s*(?:dohodou\s*)?k\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', pozn, re.I)
    if mu:
        k = min(k, dt.date(int(mu.group(3)), int(mu.group(2)), int(mu.group(1))))
    s, e = max(z, P0), min(k, P1)
    if s > e:
        continue
    cena = float(o['cena'])
    fl = (o['firma'] or '').lower()
    t = 'Glacies' if 'glacies' in fl else ('prodloužení' if 'prodlou' in fl else ('zpětná fakturace' if (o['zpet'] not in (None, 0, '0', '')) else 'napřímo/neurčeno'))
    spz = (o['rz'] or '').replace(' ', '').upper()
    y, m = s.year, s.month
    nrows = 0
    while dt.date(y, m, 1) <= e:
        dim = calendar.monthrange(y, m)[1]
        ms, me = max(s, dt.date(y, m, 1)), min(e, dt.date(y, m, dim))
        days = (me - ms).days + 1
        amt = round(cena * days / dim, 2)
        mes = '%04d-%02d' % (y, m)
        if (spz, mes) in pk_spz_months:
            overlap += 1
        est.append(dict(mesic=mes, spz=spz, castka_bez_dph=amt, dodavatel='HAVEX Mobility s.r.o.', typ='ODHAD z xlsx: ' + t,
                        smlouva=c, stredisko='', konec_smlouvy=k.isoformat(), zdroj_email_id='12548',
                        soubor='2026_Přehled zápůjček_smlouvy_k fakturaci_final do 31.08.2026.xlsx'))
        nrows += 1
        m += 1
        if m == 13: y, m = y + 1, 1
    est_contracts.append(dict(smlouva=o['smlouva_raw'], spz=spz, dodavatel='HAVEX Mobility s.r.o.', typ='ODHAD z xlsx: ' + t,
                              zacatek=o['zacatek'][:10], konec=k.isoformat(), mesicni_splatka_bez_dph=cena, pocet_radku=nrows, zdroj_email_id='12548',
                              poznamka=(o['firma'] or '') + (' | ' + pozn if pozn and pozn != 'None' else '')))
est.sort(key=lambda r: (r['mesic'], r['spz']))
with open(os.path.join(D, 'leasing_odhad_bez_pk.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(est)
with open(os.path.join(D, 'leasing_odhad_bez_pk_smlouvy.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, scols + ['poznamka']); w.writeheader(); w.writerows(est_contracts)

# ---- summary
months = ['%04d-%02d' % (y, m) for y in (2025, 2026) for m in range(1, 13) if '2025-07' <= '%04d-%02d' % (y, m) <= '2026-10']
agg = defaultdict(float); types = set()
for r in rows:
    if r['mesic'] in months:
        tt = r['typ'] if r['dodavatel'].startswith('HAVEX') else 'EFS'
        agg[(r['mesic'], tt)] += r['castka_bez_dph']; types.add(tt)
eagg = defaultdict(float)
for r in est:
    eagg[r['mesic']] += r['castka_bez_dph']
types = sorted(types)
print('mesic;' + ';'.join(types) + ';CELKEM_doklady;ODHAD_bez_PK')
for mo in months:
    vals = [agg[(mo, t)] for t in types]
    print(mo + ';' + ';'.join('%.0f' % v for v in vals) + ';%.0f;%.0f' % (sum(vals), eagg[mo]))
print('PK contracts', len(pk), 'EFS cars', len(efs_by_spz))
print('cars PK', len({v['rz'] for v in pk.values()}), 'cars all', len({r['spz'] for r in rows}))
print('EFS check', efs_check)
print('estimate contracts', len(est_contracts), 'cars', len({e['spz'] for e in est_contracts}), 'overlap months', overlap)
print('rows', len(rows), 'est rows', len(est))
