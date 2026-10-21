import re, csv, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from parse import num, parse_havex

D = '/tmp/claude-0/-home-claude/56f02949-6ccc-5729-9af0-15621bcf8687/scratchpad/naklady'
man = [l.split('\t') for l in open(D + '/manifest.tsv').read().split('\n') if l.strip()]

notes = {}
for l in open(D + '/notes.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 2:
        notes[p[0]] = dict(cat=p[1], popis=p[2] if len(p) > 2 else '', spz=p[3] if len(p) > 3 else '')

SKIP = {'9225', '3572', '11559', '11685', '12282', '37483', '40412', '907'}
SPZ_OVR = {'12950': '8H60849', '12954': '8H59128', '3587': '1ADU564', '3589': '1ADU920', '11424': '8H61717',
           '11561': '1AEA721', '11676': '8H61698', '12788': '8H60729', '13181': '1ADP444', '13579': '8H60903',
           '13593': '1ADP958', '45370': '1ADY382', '45372': '1AEB387', '45373': '1ADT423', '3594': '1AEM506',
           '11421': '8H59281', '40226': '8H60784', '40876': '8H83702', '41016': '8H83709', '3561': '1ADT489',
           '3562': '1ADT489', '8639': '1ADT489', '3554': '1ADU564', '42284': '9AF6992', '3591': '8H83658',
           '12506': '8AX9962', '13173': '9AH1342', '12993': '5SJ5242', '45434': '8H84808'}
SPZ_OVR_DOC = {('40872', '5/2025/2255'): '8H83593', ('40872', '5/2025/2263'): '8H83717',
               ('40971', '5/2025/2253'): '8H83687'}

SPZRE = re.compile(r'(?<![A-Z0-9])([0-9][A-Z][A-Z0-9]\s?[A-Z0-9]{4}|EL\s?\d{3}\s?[A-Z]{2})(?![A-Z0-9])')
AMT = re.compile(r'^(.*?)\s*(?:\|\s*)?(?:(-?[\d ]*\d,\d\d)\s*\|?\s*)?(-?[\d ]*\d,\d\d)\s*\|?\s*(0|12|21)\s*\|?\s*(-?[\d ]*\d,\d\d)\s*$')


def fdate(s):
    d, m, y = [int(x) for x in s.replace(' ', '').split('.')]
    return '%04d-%02d-%02d' % (y, m, d)


def spz_norm(s):
    return s.replace(' ', '').upper()


def spz_find(s):
    out = []
    for x in SPZRE.findall(s):
        x = spz_norm(x)
        if re.fullmatch(r'\d{7}', x) or re.fullmatch(r'\d[A-Z]\d{5}', x) and False:
            continue
        if re.fullmatch(r'[0-9][A-Z][A-Z0-9]{5}', x) or x.startswith('EL'):
            if x not in out:
                out.append(x)
    return out


def cat_item(txt, default):
    t = txt.lower()
    if 'nadlimit' in t or 'ujeté' in t or 'najeté' in t:
        return 'ostatni', 'nadlimitní km'
    if 'spoluúčast' in t or 'spoluucast' in t:
        return 'oprava', 'spoluúčast PU'
    if 'pokut' in t or 'přestup' in t:
        return 'pokuty', ''
    if 'znečiš' in t or 'čištění' in t or 'mytí' in t or 'tepov' in t:
        return 'myti', ''
    if re.search(r'\bstk\b', t) or 'emise' in t:
        return 'stk_znamky', ''
    if 'dálnič' in t or 'známk' in t:
        return 'stk_znamky', ''
    if 'pneu' in t or 'přezut' in t or 'přezout' in t:
        return 'pneu', ''
    if 'náhradní vůz' in t or 'pronájem' in t or 'orv' in t or 'registr' in t or 'technick' in t and 'průkaz' in t \
            or 'logistick' in t or 'manipulač' in t or 'administrativ' in t or 'odtah' in t and default == 'ostatni':
        return 'ostatni', ''
    if 'servis' in t and default in ('', None):
        return 'servis', ''
    if any(w in t for w in ('oprav', 'poškoz', 'odřen', 'disk', 'retuš', 'lak', 'škod', 'kolo', 'nárazník', 'sklo')) and default in ('', None):
        return 'oprava', ''
    return default or 'oprava', ''


rows = []
seen = set()
counts = defaultdict(int)
skipped = []


def add(mesic, spz, kat, castka, dod, doklad, datum, msg, soubor, pozn, nodedup=False):
    key = (doklad, spz, round(castka, 2), kat)
    if key in seen and not nodedup:
        return False
    seen.add(key)
    rows.append(dict(mesic=mesic, spz=spz, kategorie=kat, castka_bez_dph=round(castka, 2), dodavatel=dod,
                     doklad=doklad, datum=datum, zdroj_email_id=msg, soubor=soubor, poznamka=pozn))
    return True


# ---------- HAVEX ----------
havex_docs = set()
for key, msg, *_ in man:
    p = f'{D}/txt2/{key}.txt'
    if not os.path.exists(p):
        continue
    t = open(p, encoding='utf-8', errors='ignore').read()
    if 'HAVEX Mobility' not in t or ('Faktura - daňový doklad' not in t and 'Opravný daňový doklad' not in t):
        continue
    if 'RX Auto' not in t[:3000]:
        continue  # subcontractor invoices addressed to HAVEX
    if msg in SKIP:
        skipped.append((msg, 'skip list'))
        continue
    page1 = t.split('\f')[0]
    d = parse_havex(page1)
    if not d.get('zaklad') and d.get('zaklad') != 0:
        d2 = parse_havex(t)
        if d2.get('zaklad') is not None:
            d = d2
    if d.get('zaklad') is None:
        skipped.append((msg, 'no total ' + key))
        continue
    m = re.search(r'vystavil\(a\):[^\n]*\n\s*(\S[^\n]*?)\s{2,}|vystavil\(a\):[^\n]*\n\s*(\S.*)', page1)
    who = ((m.group(1) or m.group(2)) if m else '').strip()
    if 'Havlíčk' in who:
        skipped.append((msg, 'pokuta Havlíčková'))
        continue
    duzp = d['duzp'] or d['vyst']
    datum = fdate(duzp)
    mesic = datum[:7]
    nt = notes.get(msg, {})
    default = nt.get('cat', '')
    if default == 'SKIP':
        skipped.append((msg, 'notes skip'))
        continue
    inv_spz = SPZ_OVR_DOC.get((msg, d['doc'])) or SPZ_OVR.get(msg) or nt.get('spz') or ''
    found = spz_find(page1.split('Název zdanitelného plnění')[-1].split('bez DPH')[0]) if 'Název zdanitelného plnění' in page1 else []
    if not inv_spz:
        inv_spz = found[0] if len(found) == 1 else (','.join(found) if found else '')
    # split items
    items = []
    cur = None
    for it in d['items']:
        mm = AMT.match(it)
        if mm and mm.group(3):
            if cur:
                items.append(cur)
            cur = dict(desc=mm.group(1).strip(' |'), amt=num(mm.group(3)), dph=mm.group(4))
        else:
            if cur:
                cur['desc'] += ' ' + it.strip(' |')
            else:
                cur = dict(desc=it.strip(' |'), amt=None, dph='')
    if cur:
        items.append(cur)
    items = [i for i in items if i['amt'] is not None]
    tot_items = sum(i['amt'] for i in items)
    dkey = (d['doc'], inv_spz, round(d['zaklad'], 2))
    if dkey in havex_docs:
        skipped.append((msg, 'duplicate doc ' + d['doc']))
        continue
    havex_docs.add(dkey)
    sup = 'HAVEX Mobility s.r.o.' + (f' ({who})' if who else '')
    soubor = f'blob-{key}.pdf'
    if not items or abs(tot_items - d['zaklad']) > 1:
        kat, extra = cat_item(' '.join(d['items']) + ' ' + nt.get('popis', ''), default)
        poz = '; '.join(x for x in [nt.get('popis', ''), extra, 'položky nerozparsovány' if items else ''] if x)
        if add(mesic, inv_spz if inv_spz and ',' not in inv_spz else (inv_spz.split(',')[0] if inv_spz else ''), kat,
               d['zaklad'], sup, d['doc'], datum, msg, soubor, poz + ('; více SPZ: ' + inv_spz if ',' in inv_spz else '')):
            counts['HAVEX'] += 1
        continue
    first = True
    for it in items:
        sp = spz_find(it['desc'])
        spz = sp[0] if len(sp) == 1 and not SPZ_OVR.get(msg) else (inv_spz if inv_spz and ',' not in inv_spz else (sp[0] if sp else inv_spz.split(',')[0] if inv_spz else ''))
        if 'Kořínek' in who and default and default != 'SKIP' and ('servis' in it['desc'].lower() or len(items) == 1):
            kat, extra = default, nt.get('popis', '')
        else:
            kat, extra = cat_item(it['desc'] + ' ' + (nt.get('popis', '') if len(items) == 1 else ''), default)
        poz = '; '.join(x for x in [extra, it['desc'][:80]] if x)
        if it['dph'] == '0' and 'spoluúčast' not in poz:
            poz += '; 0% DPH'
        if add(mesic, spz, kat, it['amt'], sup, d['doc'], datum, msg, soubor, poz, nodedup=True) and first:
            counts['HAVEX'] += 1
            first = False

# ---------- manual rows (ACJ/EFS, Auto Palace, Cardion, vignettes, transport, Alza) ----------
M = []
def r(mesic, spz, kat, amt, dod, doc, datum, msg, key, pozn):
    M.append((mesic, spz, kat, amt, dod, doc, datum, msg, f'blob-{key}.pdf' if key else '', pozn))

ACJ = 'AUTOCENTRUM Jičín s.r.o.'
EFS = 'EURO FLEET SERVIS s.r.o.'
r('2026-07', '8H82929', 'oprava', 10645.04, ACJ, '2211263318', '2026-07-23', '534', '1792538461341-fyawnm', 'lakování nárazníku (též msg 27453, 777)')
r('2026-07', '8H82916', 'oprava', 7544.98, ACJ, '2211263413', '2026-07-29', '534', '1792538472437-qrbbdh', 'oprava vozu (též msg 26000, 773)')
r('2026-08', '1ADX066', 'oprava', 4999.33, ACJ, '2211263697', '2026-08-18', '534', '1792538479365-zpxte2', 'PU: faktura 9083,33 bez DPH, pojišťovna 4084; RX hradí rozdíl (≈spoluúčast 5000)')
r('2026-08', '1ADX064', 'oprava', 3983.16, ACJ, '2211263901', '2026-08-31', '534', '1792538481102-wcnkbt', 'výměna pneu + oprava nárazníku (též msg 3552/5474)')
r('2026-09', '1ADX066', 'oprava', 4999.72, ACJ, '2211264017', '2026-09-09', '534', '1792538481824-g6zrt0', 'PU: faktura 36441,72 bez DPH, pojišťovna 31442; RX hradí rozdíl (≈spoluúčast)')
r('2026-09', '1ADX039', 'oprava', 4999.58, ACJ, '2211264283', '2026-09-30', '738', '1792538543616-fhqtvu', 'PU: faktura 42772,58 bez DPH, pojistné plnění 37773 (krycí dopis), spoluúčast 5000')
r('2026-07', '8H82866', 'oprava', 2144.46, ACJ, '2211263436', '2026-07-30', '25971', '1792538533549-73ku2e', 'drobné opravy; odběratel Carnetto RX s.r.o.')
r('2026-07', '8H82921', 'oprava', 1429.64, ACJ, '2211263399', '2026-07-29', '26006', '1792538539747-ktt9h5', 'drobné opravy; odběratel Carnetto RX s.r.o.')
r('2026-07', '8H82919', 'oprava', 2144.46, ACJ, '2211263138', '2026-07-10', '29243', '1792538541981-e3qsoo', 'drobné opravy vozu EFS')
r('2026-07', '8H82873', 'oprava', 5100.68, ACJ, '2211263087', '2026-07-08', '29244', '1792538542735-pgpx5m', 'oprava vozu; odběratel Carnetto RX s.r.o.')
r('2025-11', '8H60661', 'oprava', 2732.40, ACJ, '2211255082', '2025-11-20', '41872', '1792538655094-labqdg', 'chybějící ovladač nezávislého topení + diagnostika')
r('2025-09', '8H60643', 'ostatni', 7692.10, ACJ, '2211254011', '2025-09-23', '42377', '1792538655849-f6x2lv', 'chybějící klíč Kodiaq (nový klíč + programování)')
# přezutí 19.11.2025 (sken, OCR)
prez = [('2111251685', '8H82921', 1498.99), ('2111251684', '8H82945', 1498.99), ('2111251683', '8H82922', 1498.99),
        ('2111251682', '8H82915', 1498.74), ('2211255030', '8H82934', 1498.39), ('2211255029', '8H82937', 1498.39),
        ('2211255028', '8H82919', 1498.39), ('2211255027', '8H82913', 1498.39), ('2211255026', '8H82939', 1498.39),
        ('2211255040', '8H82914', 1499.15), ('2211255039', '8H82942', 1499.15), ('2211255038', '8H82916', 1499.15),
        ('2211255037', '8H82873', 1499.15), ('2211255035', '8H82938', 1499.15), ('2211255034', '8H82866', 1499.15),
        ('2211255033', '8H82929', 1499.15), ('2211255032', '8H82946', 1499.15)]
for doc, spz, a in prez:
    r('2025-11', spz, 'pneu', a, ACJ, doc, '2025-11-19', '41882', '1792538661174-b4xmim', 'přezutí dodaných vozů, sken – OCR' + ('; SPZ dle VIN (e-mail 41616)' if doc in ('2211255037', '2211255038') else ''))
# EFS spoluúčasti / odtah
r('2025-12', '8H82922', 'oprava', 2600.00, EFS, '3900250109', '2025-12-12', '12265', '1792538654377-oe8jhq', 'přefakturace odtahu Kamiq z Drážďan')
efs = [('3900260168', '8H82927', 18061.40, '2026-06-30', '630', '1792538777886-ya81tq', True),
       ('3900260193', '8H82934', 5000, '2026-06-30', '30989', '1792538840626-pk2n8c', False),
       ('3900260202', '8H82873', 5000, '2026-07-10', '30324', '1792538838105-44zls5', True),
       ('3900260203', '8H82919', 5000, '2026-07-10', '29901', '1792538839189-on8f1q', False),
       ('3900260220', '8H82946', 5000, '2026-07-27', '26520', '1792538843704-s7uxqg', False),
       ('3900260221', '8H82922', 18917.00, '2026-07-27', '26519', '1792538860931-amli03', True),
       ('3900260229', '8H82929', 5000, '2026-07-31', '25455', '1792538870952-olowse', True),
       ('3900260229', '8H82921', 5000, '2026-07-31', '25455', '1792538870952-olowse', True),
       ('3900260257', '8H82916', 5000, '2026-08-06', '23999', '1792538882400-5l0w5w', False),
       ('3900260261', '8H82866', 10000, '2026-07-31', '2931', '1792538394141-xy5val', True),
       ('3900260263', '8H82938', 5000, '2026-08-11', '2931', '1792538394141-xy5val', True),
       ('3900260269', '8H82866', 5000, '2026-08-13', '2931', '1792538394141-xy5val', True),
       ('3900260285', '8H82938', 5000, '2026-08-27', '2931', '1792538394141-xy5val', True),
       ('3900260312', '8H82939', 5000, '2026-08-31', '83', '1792538395834-zyr9it', True),
       ('3900260313', '9H03551', 1000, '2026-09-09', '83', '1792538395834-zyr9it', True),
       ('3900260325', '1ARK464', 5000, '2026-09-22', '10805', '1792538482711-32djk9', True),
       ('3900260332', '8H85919', 5000, '2026-09-29', '7180', '1792538483546-6hfw3s', True)]
for doc, spz, a, dt, msg, key, carn in efs:
    pz = 'spoluúčast PU (0% DPH)'
    if doc == '3900260168':
        pz += '; oprava 364372,64 − dobropis 3145 kryta pojistným plněním 343167'
    if doc == '3900260261':
        pz += '; 2 PU á 5000'
    if carn:
        pz += '; odběratel Carnetto RX s.r.o.'
    r(dt[:7], spz, 'oprava', a, EFS, doc, dt, msg, key, pz)
r('2026-08', '8H82938', 'oprava', 2959.00, EFS, '3900260285', '2026-08-27', '2931', '1792538394141-xy5val', 'nesouvisející poškození; odběratel Carnetto RX s.r.o.')

# Auto Palace Tuchoměřice / Západ (AutoBinck) – mytí fakturované měsíčně, servis
AP = 'Auto Palace Tuchoměřice s.r.o.'
APZ = 'Auto Palace Západ s.r.o.'
myti = [('3511103228', '2025-10-31', 17886.20, '41869', '1792538977634-krv4ve', 173),
        ('3511103611', '2025-11-28', 14370.99, '41679', '1792538965764-3cxk45', 139),
        ('3511103819', '2025-12-31', 11602.48, '41075', '1792538964184-xx9kii', 101),
        ('3611100220', '2026-01-31', 6777.69, '39331', '1792538998892-sov7z5', 59),
        ('3611100434', '2026-02-27', 9907.03, '36913', '1792538962879-8t425j', 89),
        ('3611100745', '2026-03-31', 13641.53, '8643', '1792538929076-cf518a', 125),
        ('3611101154', '2026-04-30', 14732.85, '8643', '1792538922099-m2b5yl', 135),
        ('3611101719', '2026-06-30', 32630.53, '2664', '1792538908328-qoy39c', 299),
        ('3611101938', '2026-07-31', 38337.15, '2664', '1792538914920-y3h7ws', 349),
        ('3611102099', '2026-08-31', 42998.10, '2664', '1792538904160-8az1vn', 394),
        ('3611102294', '2026-09-30', 37868.88, '2664', '1792538919019-blk1w2', 347)]
for doc, dt, a, msg, key, n in myti:
    dod = APZ if doc.startswith('35') else AP
    r(dt[:7], 'FLOTILA', 'myti', a, dod, doc, dt, msg, key, f'mytí exteriéru {n}x (souhrnná měsíční faktura, bez SPZ)')
r('2025-10', '8H34355', 'servis', 4863.57, APZ, '3511103219', '2025-10-31', '41867', '1792538970529-r8zgzo', 'servis výměny oleje')
r('2025-10', '1ADX026', 'servis', 5296.69, APZ, '3511103204', '2025-10-31', '41868', '1792538973899-v0vkk8', 'prohlídka s výměnou oleje')
r('2025-11', '9AS2776', 'servis', 5897.57, APZ, '3511103261', '2025-11-05', '41866', '1792538969498-ce7n2b', 'servis výměny oleje Multivan')
r('2026-03', '8H85045', 'servis', 4987.28, AP, '3611100471', '2026-03-05', '8643', '1792538934307-er7vo8', 'servis výměny oleje')
r('2025-12', '9AS2776', 'oprava', 0.0, APZ, '3511103705', '2025-12-11', '40820', '1792539053653-wtlt43', 'PU Generali: oprava 68001,02 bez DPH hradí pojišťovna, RX dluží spoluúčast + DPH – výše spoluúčasti v e-mailech neuvedena')

# Cardion Cars (Autorion) – Volvo XC90 (VIN YV1LFK2V6P1992353)
CC = 'CARDION CARS a.s. (Autorion)'
r('2026-08', '9AY0542', 'oprava', 7946.37, CC, '1133264106', '2026-08-19', '5785', '1792538938205-5okx8l', 'Volvo XC90: výměna ventilu CBVM, diagnostika, lepení pneu')
r('2026-10', '1ADZ301', 'servis', 22322.13, CC, '1133264981', '2026-10-14', '2654', '1792538937365-vo13px', 'Volvo XC90 (týž VIN jako 9AY0542): servis CSC, brzdové destičky, geometrie, silentblok')

# Transport vozů (Machytransport)
MT = 'Radek Macháček – autodoprava (Machytransport)'
r('2025-11', 'FLOTILA', 'ostatni', 55400.00, MT, '25479', '2025-11-26', '3584', '1792539214214-rzse4s', 'transport vozů Jičín→Stehelčeves, EFS→Bratislava, Bratislava→HAVEX Zličín (upomínka msg 12124)')
r('2026-04', 'FLOTILA', 'ostatni', 70000.00, MT, '26130', '2026-04-21', '38116', '1792539209359-tad712', 'transport 20 vozů Jičín→Letiště Bratislava (přepracovaná fa, nahrazuje 38139)')

# Dálniční známky
EUR, HUF = 24.5, 0.0625
r('2026-07', '7AU5420', 'stk_znamky', 2570, 'SFDI (edalnice.gov.cz)', 'EDAZ-7AU5420', '2026-07-23', '7422', '1792539108315-t9nm4l', 'CZ roční známka (osvobozeno od DPH); SPZ mimo flotilu?')
r('2026-07', '8AD5179', 'stk_znamky', 2570, 'SFDI (edalnice.gov.cz)', 'EDAZ-8AD5179', '2026-07-10', '7424', '1792539108986-o7u4dw', 'CZ roční známka; SPZ mimo flotilu?')
r('2026-06', '2TM3559', 'stk_znamky', 2570, 'SFDI (edalnice.gov.cz)', 'EDAZ-2TM3559', '2026-06-30', '7595', '1792539109610-7krsz7', 'CZ roční známka; SPZ mimo flotilu?')
r('2026-06', '9AH6067', 'stk_znamky', round(9.60 * EUR, 2), 'ASFINAG', '400056879772', '2026-06-12', '8080', '1792539110534-7s0brw', '9,60 EUR vč. AT DPH (nenárokovatelné), kurz 24,5 odhad')
r('2026-06', '8H84178', 'stk_znamky', round(28.60 * EUR, 2), 'ASFINAG', '400056835562', '2026-06-11', '8085', '1792539111299-ws8woh', '28,60 EUR vč. AT DPH (známka + úsekové mýto), kurz 24,5 odhad')
r('2026-07', '9H03559', 'stk_znamky', round(8.10 * EUR, 2), 'NDS (eznamka.sk)', '2613613241', '2026-07-30', '6746', '1792539105244-tvmvr9', 'SK 1denní 8,10 EUR vč. SK DPH, kurz 24,5 odhad')
r('2026-07', 'AOQP713', 'stk_znamky', round(8.10 * EUR, 2), 'NDS (eznamka.sk)', '2613159707', '2026-07-13', '7316', '1792539106327-0h9t4u', 'SK 1denní, maďarská SPZ (mimo flotilu?), kurz 24,5 odhad')
r('2026-07', '1AHL028', 'stk_znamky', round(10.80 * EUR, 2), 'NDS (eznamka.sk)', '2612896260', '2026-07-03', '7575', '1792539107254-rn7fyc', 'SK 10denní 10,80 EUR, kurz 24,5 odhad')
r('2026-07', '8H84243', 'stk_znamky', round(5550 * HUF, 2), 'Nemzeti Útdíj (HU)', '2026-0920439-HWB', '2026-07-30', '6744', '1792539103964-zaj9iu', 'HU 1denní 5550 HUF vč. HU DPH, kurz 0,0625 odhad')
r('2026-07', '9H03559', 'stk_znamky', round(5550 * HUF, 2), 'Nemzeti Útdíj (HU)', '2026-0916713-HWB', '2026-07-30', '6748', '1792539104480-yxcpaz', 'HU 1denní 5550 HUF vč. HU DPH, kurz 0,0625 odhad')

# Alza – jen položky pro auta
r('2026-08', 'FLOTILA', 'ostatni', 2775.18, 'Alza.cz a.s.', '4027637401', '2026-08-03', '6519', '1792539151457-gg9lf5', 'startovací zdroj (booster)')
r('2026-08', 'FLOTILA', 'ostatni', 2778.83, 'Alza.cz a.s.', '4027855687', '2026-08-05', '6517', '1792539150841-yrlldq', '2x autosedačka (DPH 12 %)')

for x in M:
    if add(*x):
        counts[x[4]] += 1

rows.sort(key=lambda r: (r['mesic'], r['dodavatel'], r['doklad'], r['spz']))
with open(D + '/servis.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['mesic', 'spz', 'kategorie', 'castka_bez_dph', 'dodavatel', 'doklad', 'datum',
                                      'zdroj_email_id', 'soubor', 'poznamka'])
    w.writeheader()
    for r_ in rows:
        w.writerow(r_)

print('rows', len(rows))
for k, v in sorted(counts.items()):
    print('docs', k, v)
print('skipped', skipped)
