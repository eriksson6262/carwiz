import csv, re, os, sys
from collections import defaultdict

BASE = '/tmp/claude-0/-home-claude/56f02949-6ccc-5729-9af0-15621bcf8687/scratchpad/naklady'
RAW = BASE + '/raw_servis2'
OUT = BASE + '/servis2.csv'

def num(s):
    return float(s.replace(' ', '').replace('\xa0', '').replace(',', '.'))

rows = []
def add(mesic, pob, spz, kat, castka, dod, dok, datum, eid, pozn):
    rows.append(dict(mesic=mesic, pobocka=pob, spz=spz, kategorie=kat, castka_bez_dph=round(castka, 2),
                     dodavatel=dod, doklad=dok, datum=datum, zdroj_email_id=eid, poznamka=pozn))

# ---------------- Auto Palace: existing servis.csv rows ----------------
existing = set()
with open(BASE + '/servis.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'Auto Palace' not in r['dodavatel']:
            continue
        existing.add(r['doklad'])
        spz = '' if r['spz'] == 'FLOTILA' else r['spz']
        castka = float(r['castka_bez_dph'])
        pozn = r['poznamka']
        if r['doklad'] == '3511103705':
            castka = 5000.0
            pozn = ('PU Generali 9860705 (9AS2776): oprava 68 001,02 bez DPH, Generali hradí 63 002 (krycí dopis v e-mailu 41419), '
                    'RX nese spoluúčast 5 000 bez DPH (+ DPH z celé opravy, odpočitatelné); součet řádku ≠ základ faktury')
        add(r['mesic'], 'PRG', spz, r['kategorie'], castka, r['dodavatel'], r['doklad'], r['datum'], r['zdroj_email_id'],
            pozn + '; už v servis.csv')

# new Auto Palace invoice found
add('2025-09', 'PRG', '', 'myti', 22745.46, 'Auto Palace Západ s.r.o.', '3511102865', '2025-09-30', '50985',
    'mytí exteriéru program 1, 220x (souhrnná měsíční faktura, bez SPZ)')

# ---------------- Pavel Rejdík (neplátce DPH, částky = celkem) ----------------
RD = 'Pavel Rejdík (IČO 68270305)'
rej = [
    ('57', '2025-10-22', '42258', [
        ('oprava', 4700, 'chladič EGR + výměna – Ford'),
        ('oprava', 2500, 'zadní brzdové destičky – Peugeot 3008'),
        ('oprava', 6700, 'přední brzdové destičky + vyřízení STK + přezutí – BMW X1 (nedělitelná položka)'),
        ('servis', 4700, 'vyřízení STK + přezutí – BMW X4 (nedělitelná položka)'),
        ('oprava', 3300, 'přetěsnění + kryt rozvodů – Octavia'),
    ], 21900, 'opravená verze faktury 57 (původní z 22.10.2025, e-mail 42591, byla 18 600 bez položky Octavia – nahrazena)'),
    ('64', '2025-12-26', '41208', [
        ('pneu', 11200, 'přezutí celá kola + uskladnění 14x'),
        ('pneu', 16800, 'přezutí pneumatiky + uskladnění 12x'),
        ('pneu', 7500, 'přezutí celá kola 15x'),
        ('pneu', 400, 'oprava pneu 2x'),
        ('oprava', 7980, 'Kodiaq STK + brzdové destičky (nedělitelná položka)'),
        ('pneu', 5000, 'přezutí pneumatiky 5x'),
        ('pneu', 6000, 'přezutí pneu nad 20" 3x'),
    ], 54880, ''),
]
for dok, dat, eid, items, total, extra in rej:
    assert abs(sum(i[1] for i in items) - total) < 0.01, dok
    for kat, c, popis in items:
        add(dat[:7], 'PRG', '', kat, c, RD, dok, dat, eid,
            '; '.join(x for x in [popis, 'bez SPZ (jen model)', 'neplátce DPH – částka = celkem', extra] if x))

# ---------------- Šimon Závěšický / SIMO CAR PLUS s.r.o. ----------------
SD = 'SIMO CAR PLUS s.r.o. (Šimon Závěšický, Autoservis Simon)'
simon = {  # doklad: email id
    '7102500273': '37450', '7102500280': '24362', '7102500360': '24362', '7102500361': '24362', '7102500535': '24362',
    '7102500767': '41087', '7102500768': '41087', '7102500769': '41087', '7102500770': '41087', '7102500771': '41087',
    '7102500772': '41087', '7102500773': '41087', '7102500774': '41087', '7102500775': '41087',
    '7102600005': '40862', '8102600003': '40862',
    '7102600242': '24362', '7102600243': '24362', '7102600244': '37449', '7102600245': '37448',
    '7102600246': '24363', '7102600247': '24363', '7102600550': '24363', '7102600551': '24363', '7102600552': '24363',
    '7102600553': '24363', '7102600554': '24363', '7102600555': '24363', '7102600556': '24363',
    '7102600621': '24363', '7102600622': '24363', '7102600623': '24363', '7102600646': '24363',
}
PNEU = re.compile(r'přezut|přehozen|vyvážen|uskladn|pneu|R1[0-9]C?\b|tracmax|kontrola kola', re.I)
SERV = re.compile(r'olej|[05]W-?\d0|filtr|zátka|kroužek|výpustní|ostřikov|směs|STK|diagnost|spotřební|antifreeze|chladící kapal|adblue|klimatiz|dobíjení bat|vyřízení servisu', re.I)
LAB = re.compile(r'mechanická práce', re.I)
ITEM = re.compile(r'^\s*(\d{1,2})\s+(.+?)\s{2,}([\d,]+)\s+(Kus|litr|Hodina|Služba)\s+([\d ]+,\d{2})\s+([\d,]+)\s+([\d ]+,\d{2})\s+([\d ]+,\d{2})\s+(21|0)\s+([\d ]+,\d{2})\s+([\d ]+,\d{2})\s*$')

files = {re.search(r'_(\d{10})\.txt$', fn).group(1): fn for fn in os.listdir(RAW)
         if fn.startswith('sim_') and fn.endswith('.txt') and re.search(r'_(\d{10})\.txt$', fn)}
problems = []
for dok, eid in simon.items():
    t = open(os.path.join(RAW, files[dok]), encoding='utf-8').read()
    d = re.search(r'Datum uskutečnění zdaň\. plnění:\s+(\d+)\.(\d+)\.(\d{4})', t)
    datum = f'{d.group(3)}-{int(d.group(2)):02d}-{int(d.group(1)):02d}'
    m = re.search(r'Dodací list č\. \d+ - ([0-9A-Z]+)', t)
    spz_inv = m.group(1) if m else ''
    m2 = re.search(r'Poznámka: ([0-9A-Z]{7}) ', t)
    if not spz_inv and m2:
        spz_inv = m2.group(1)
    base = sum(num(x) for x in re.findall(r'^\s*(?:21|0)\s+-?[\d ]+,\d{2}\s+(-?[\d ]+,\d{2})\s+-?[\d ]+,\d{2}\s*$', t, re.M))
    if dok == '8102600003':
        add(datum[:7], 'OSR', '6AU6673', 'pneu', -6080.0, SD, dok, datum, eid,
            'dobropis k fakt. 7102500772 – pneu 215/75 R16C Tracmax 4x (chybně 0 % DPH), nahrazeno fakturou 7102600005')
        continue
    items = []
    for line in t.splitlines():
        mm = ITEM.match(line)
        if mm:
            items.append((mm.group(2).strip(), num(mm.group(8))))
    s = sum(c for _, c in items)
    if abs(s - base) > 0.02:
        problems.append((dok, s, base))
    # per-item SPZ (storage of other cars on 7102500770)
    groups = defaultdict(lambda: [0.0, []])
    lab = 0.0
    cat_parts = defaultdict(float)
    tmp = []
    for name, c in items:
        rz = re.search(r'RZ:\s*([0-9A-Z ]+)\)', name)
        spz = rz.group(1).replace(' ', '') if rz else spz_inv
        if LAB.search(name):
            lab += c; continue
        if PNEU.search(name): k = 'pneu'
        elif re.search(r'geometri|hřídel', name, re.I): k = 'oprava'
        elif SERV.search(name): k = 'servis'
        else: k = 'oprava'
        if k != 'pneu':
            cat_parts[k] += c
        tmp.append((spz, k, name, c))
    labk = None
    if lab:
        labk = max(cat_parts, key=cat_parts.get) if cat_parts else 'pneu'
        tmp.append((spz_inv, labk, 'mechanická práce', lab))
    for spz, k, name, c in tmp:
        g = groups[(spz, k)]; g[0] += c; g[1].append(name)
    for (spz, k), (c, names) in groups.items():
        pozn = ', '.join(dict.fromkeys(names))
        if labk and k == labk and len({kk for (_, kk) in groups}) > 1:
            pozn += ' (práce přiřazena převažující kategorii)'
        if dok == '7102600005':
            pozn += '; náhrada za položku pneu z fakt. 7102500772 (DPH 21 %)'
        if dok == '7102500772' and k == 'pneu':
            pozn += '; pneu 6 080 dobropisováno 8102600003 a refakturováno 7102600005'
        add(datum[:7], 'OSR', spz, k, c, SD, dok, datum, eid, pozn)

if problems:
    print('SUM MISMATCH', problems)

rows.sort(key=lambda r: (r['dodavatel'][:4], r['mesic'], r['doklad']))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['mesic', 'pobocka', 'spz', 'kategorie', 'castka_bez_dph', 'dodavatel', 'doklad', 'datum', 'zdroj_email_id', 'poznamka'])
    w.writeheader(); w.writerows(rows)

# verification of sums per invoice vs base
print(len(rows), 'rows')
