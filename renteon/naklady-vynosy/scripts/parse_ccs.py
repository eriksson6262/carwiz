import re, glob, os, csv, sys
from collections import defaultdict, Counter

D = sys.argv[1]
OUT = sys.argv[2]

TX = re.compile(r'^(\d\d\.\d\d\.\d\d)\s+(\d\d\.\d\d)\s+(\S+)\s+(.*?)\s{2,}(\d)\s+(.+?)\s+(-?[\d.]+)\s+(?:(-?[\d.]+)\s+)?(-?[\d.]+)\s+(-?[\d.]+)\s+(Kč|EU\w*)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)(\*+)?\s*\S*$')
CARD = re.compile(r'^\s*7079\d+\s+(\d{12})\b')

OSR = ['mošnov', 'ostrava', 'rychvald', 'hrabová', 'f.místek', 'frýdek', 'místek', 'havířov', 'karviná', 'opava', 'bohumín',
       'orlová', 'třinec', 'nový jičín', 'n.jičín', 'chlebovice', 'stará ves n.ondř', 'kopřivnice', 'příbor', 'studénka', 'bílovec', 'poruba', 'vítkovice', 'petřvald',
       'šenov', 'paskov', 'brušperk', 'sedlnice', 'ostr', 'svinov', 'martinov', 'hlučín', 'frenštát', 'fulnek', 'klimkovice',
       'mar.hory', 'zábřeh,', 'plesná', 'krmelín', 'vratimov', 'kunčice', 'stará bělá', 'dobrá', 'český těšín', 'bruntál',
       'krnov', 'frýdlant n.ostr', 'odry', 'jablunkov', 'stonava', 'albrechtice', 'kozmice', 'ludgeřovice', 'baška']
PRG = ['pha', 'praha', 'středokluky', 'benátky', 'letiště', 'ruzyně', 'hostivice', 'jesenice', 'čestlice', 'průhonice',
       'zdiby', 'úvaly', 'černošice', 'řevnice', 'beroun', 'kladno', 'mělník', 'brandýs', 'čelákovice', 'říčany', 'dobříš',
       'mnichovice', 'kralupy', 'roztoky', 'buštěhrad', 'jinočany', 'rudná', 'chýně', 'tuchoměřice', 'kněževes', 'horoměřice',
       'modletice', 'nupaky', 'zeleneč', 'mstětice', 'jirny', 'ořech', 'třebotov', 'dobřichovice', 'unhošť', 'velké přílepy',
       'odolena voda', 'klecany', 'líbeznice', 'bořanovice', 'statenice', 'hovorčovice', 'větrušice', 'chrášťany', 'zbuzany']

def product(name):
    n = name.lower()
    if n.startswith('nafta') or 'diesel' in n: return 'nafta'
    if n.startswith('natural') or 'benz' in n or n.startswith('ba ') or 'super' in n or 'verva 100' in n: return 'benzín'
    if 'adblu' in n or 'aditiv' in n or 'additiv' in n: return 'AdBlue'
    if 'myt' in n or 'mytí' in n: return 'mytí'
    if 'olej' in n: return 'oleje'
    if 'dálni' in n or 'mýto' in n or 'znám' in n or 'vigne' in n: return 'dálniční poplatek'
    if 'popl' in n or 'eko' in n: return 'poplatek CCS'
    if 'sleva' in n: return 'sleva CCS'
    if 'lpg' in n or 'cng' in n or 'pb láhev' in n: return 'plyn'
    if 'autokosm' in n: return 'autokosmetika'
    if 'nápl' in n or 'kapal' in n: return 'provozní náplně'
    return 'ostatní'

def region(stat, misto):
    if stat in ('SR', 'Slov'): return 'BTS'
    m = misto.lower()
    if any(k in m for k in OSR): return 'OSR'
    if any(k in m for k in PRG): return 'PRG'
    return None

rows = []
checks = []
for f in sorted(glob.glob(os.path.join(D, '2*.txt'))):
    base = os.path.basename(f)[:-4]
    per, mid = base.split('_')
    txt = open(f, encoding='utf-8').read().splitlines()
    doklad = None
    for l in txt:
        m = re.search(r'Číslo dokladu:\s+(\S+)', l)
        if m and not m.group(1).endswith('SR'):
            doklad = m.group(1); break
    card = None; cname = None; card_tot = {}
    in_annex = False
    for i, l in enumerate(txt):
        if 'Příloha k daň.dokl' in l:
            in_annex = True; card = None; cname = ''
            continue
        if in_annex:
            mc = CARD.match(l)
            if mc:
                card = mc.group(1)[-4:]
                # name: lines between this annex header and card line
                cands = [x.strip() for x in txt[max(0, i-6):i] if 'KARTA' in x.upper() and 'Příloha' not in x]
                cname = cands[-1] if cands else ''
                continue
            m = TX.match(l)
            if m and card:
                (d, t, stat, misto, ink, name, qty, foreign, ubez, us, cur, celk, bez, dph, pct, star) = m.groups()
                dd, mm, yy = d.split('.')
                datum = f'20{yy}-{mm}-{dd}'
                celk = float(celk); bez = float(bez)
                note = ''
                bez_out = bez
                if stat in ('SR', 'Slov'):
                    # SK: Kč celkem obsahuje SK DPH 23 %, CCS ji v CZ dokladu vykazuje jako 0 %
                    ub, usd = float(ubez), float(us)
                    ratio = ub / usd if usd else 1
                    bez_out = round(celk * ratio, 2)
                    note = f'SK, zaplaceno {celk:.2f} Kč vč. SK DPH ({foreign} EUR); bez DPH přepočteno poměrem jedn. cen'
                rows.append(dict(mesic=datum[:7], datum=datum, pobocka=region(stat, misto), spz=cname, karta4=card,
                                 misto=(misto.strip() or 'CCS účet') + ('' if stat == 'ČR' else f' ({stat})'),
                                 produkt=product(name), produkt_orig=name.strip(), mnozstvi=float(qty),
                                 castka_bez_dph=bez_out, castka_ccs_bez=bez, celkem=celk, doklad=doklad,
                                 zdroj_email_id=mid, poznamka=note, per=per))
    tot = None
    for l in txt:
        m = re.search(r'Celkem za všechny karty bez DPH \(Kč\):\s+([\d.]+)', l)
        if m: tot = float(m.group(1))
    tot_all = None
    for l in txt:
        m = re.search(r'Celkem za všechny karty \(Kč\):\s+([\d.]+)', l)
        if m: tot_all = float(m.group(1))
    s_bez = round(sum(r['castka_ccs_bez'] for r in rows if r['per'] == per), 2)
    s_all = round(sum(r['celkem'] for r in rows if r['per'] == per), 2)
    checks.append((per, doklad, tot, s_bez, tot_all, s_all))

# default branch per card per period (majority of known CZ rows), else overall per card, else PRG
cnt = defaultdict(Counter); cnt_all = defaultdict(Counter)
for r in rows:
    if r['pobocka']:
        cnt[(r['per'], r['karta4'])][r['pobocka']] += 1
        cnt_all[r['karta4']][r['pobocka']] += 1
for r in rows:
    if not r['pobocka']:
        c = cnt.get((r['per'], r['karta4'])) or cnt_all.get(r['karta4'])
        if r['karta4'] == '0000' or not c:
            r['pobocka'] = 'PRG'; extra = 'pobočka default PRG (poplatek účtu)' if r['karta4'] == '0000' else 'pobočka default PRG'
        else:
            r['pobocka'] = c.most_common(1)[0][0]; extra = 'pobočka podle karty (místo mimo PRG/OSR)'
        r['poznamka'] = (r['poznamka'] + '; ' if r['poznamka'] else '') + extra
    if r['produkt'] == 'ostatní' or r['produkt'] in ('oleje', 'provozní náplně'):
        r['poznamka'] = (r['poznamka'] + '; ' if r['poznamka'] else '') + f'CCS položka: {r["produkt_orig"]}'

cols = ['mesic', 'datum', 'pobocka', 'spz', 'karta4', 'misto', 'produkt', 'mnozstvi', 'castka_bez_dph', 'doklad', 'zdroj_email_id', 'poznamka']
rows.sort(key=lambda r: (r['datum'], r['karta4']))
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows: w.writerow(r)

print('CHECKS per doklad (period, doklad, CCS bez DPH, parsed bez DPH, CCS celkem, parsed celkem):')
for c in checks:
    print(c, 'OK' if c[2] is not None and abs(c[2] - c[3]) < 0.05 and abs(c[4] - c[5]) < 0.05 else 'DIFF')
print('rows', len(rows))
print('unmatched products:', Counter(r['produkt_orig'] for r in rows if r['produkt'] == 'ostatní'))
print('unknown places:', Counter(r['misto'] for r in rows if 'pobočka podle karty' in r['poznamka'] or 'default PRG' in r['poznamka']).most_common(60))
