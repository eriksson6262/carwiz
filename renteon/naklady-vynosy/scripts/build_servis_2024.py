#!/usr/bin/env python3
"""Servis / opravy / pneu / mytí / STK – přijaté faktury RX Auto s.r.o., období 2024-01 .. 2025-08.

Zdroje: přílohy ze Spark (blob PDF -> raw2024/<blob>.txt, pdftotext -layout), skeny čteny vizuálně / OCR.
Mapa blob -> e-mail: blobmap2024.tsv (blob, attachment id, název souboru, message id).
Výstup: servis_2024.csv (mesic,pobocka,spz,kategorie,castka_bez_dph,dodavatel,doklad,datum,zdroj_email_id,poznamka)
Duplicity proti servis.csv a servis2.csv se vyřazují podle čísla dokladu.
"""
import csv, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from parse import num, parse_havex

# --- převzato ze servis_build.py (ten při importu přepisuje servis.csv, proto kopie) ---
SPZRE = re.compile(r'(?<![A-Z0-9])([0-9][A-Z][A-Z0-9]\s?[A-Z0-9]{4}|EL\s?\d{3}\s?[A-Z]{2})(?![A-Z0-9])')
AMT = re.compile(r'^(.*?)\s*(?:\|\s*)?(?:(-?[\d ]*\d,\d\d)\s*\|?\s*)?(-?[\d ]*\d,\d\d)\s*\|?\s*(0|12|21)\s*\|?\s*(-?[\d ]*\d,\d\d)\s*$')


def fdate(s):
    d, m, y = [int(x) for x in s.replace(' ', '').split('.')]
    return '%04d-%02d-%02d' % (y, m, d)


def spz_find(s):
    out = []
    for x in SPZRE.findall(s):
        x = x.replace(' ', '').upper()
        if (re.fullmatch(r'[0-9][A-Z][A-Z0-9]{5}', x) or x.startswith('EL')) and x not in out:
            out.append(x)
    return out


def cat_item(txt, default):
    t = txt.lower()
    if 'nadlimit' in t or 'ujeté' in t or 'najeté' in t:
        return 'ostatni', 'nadlimitní km'
    if 'spoluúčast' in t or 'spoluucast' in t or 'spouúčast' in t:
        return 'oprava', 'spoluúčast PU'
    if 'pokut' in t or 'přestup' in t:
        return 'pokuty', ''
    if 'znečiš' in t or 'čištění' in t or 'mytí' in t or 'tepov' in t:
        return 'myti', ''
    if re.search(r'\bstk\b', t) or 'emise' in t or 'dálnič' in t or 'známk' in t:
        return 'stk_znamky', ''
    if 'pneu' in t or 'přezut' in t or 'přezout' in t:
        return 'pneu', ''
    if 'náhradní vůz' in t or 'pronájem' in t or 'registr' in t or 'logistick' in t or 'manipulač' in t \
            or 'administrativ' in t or 'odtah' in t or 'přistavení' in t or 'dopravné' in t:
        return 'ostatni', ''
    if 'servis' in t or 'olej' in t or 'prohlídk' in t:
        return 'servis', ''
    return default or 'oprava', ''


D = '/tmp/claude-0/-home-claude/56f02949-6ccc-5729-9af0-15621bcf8687/scratchpad/naklady'
RAW = D + '/raw2024'
EUR = 24.3
OD, DO = '2024-01', '2025-08'

blob2msg = {}
for l in open(D + '/blobmap2024.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 4:
        blob2msg[p[0]] = p[3]

# ---- pobočky dle Renteonu (spz_map.txt: SPZ:YYYY-MM=P|O;...) ----
POB = {'P': 'PRG', 'O': 'OSR', 'B': 'BTS'}
spzmap = {}
for e in open(D + '/spz_map.txt').read().strip().split('|'):
    if ':' in e:
        s, h = e.split(':', 1)
        spzmap[s] = sorted(tuple(x.split('=')) for x in h.split(';') if '=' in x)


def pobocka(spz, mesic, default='PRG'):
    if re.fullmatch(r'[A-Z]{2}\d{3}[A-Z]{2}', spz or ''):
        return 'BTS'
    h = spzmap.get(spz)
    if not h:
        return default
    cur = h[0][1]
    for m, p in h:
        if m <= mesic:
            cur = p
    return POB.get(cur, default)


# ---- existující doklady (servis.csv, servis2.csv) ----
existing = set()
for fn in ('servis.csv', 'servis2.csv'):
    for r in csv.DictReader(open(f'{D}/{fn}', encoding='utf-8')):
        existing.add(r['doklad'].replace(' ', ''))

rows = []
stats = defaultdict(int)
skipped = []


def add(datum, spz, kat, castka, dod, doklad, msg, pozn, pob=None):
    mesic = datum[:7]
    if not (OD <= mesic <= DO):
        skipped.append((doklad, 'mimo období ' + datum))
        return
    if doklad.replace(' ', '') in existing:
        skipped.append((doklad, 'už v servis.csv/servis2.csv'))
        return
    spz = (spz or '').replace(' ', '').upper()
    rows.append(dict(mesic=mesic, pobocka=pob or pobocka(spz, mesic), spz=spz, kategorie=kat,
                     castka_bez_dph=round(castka, 2), dodavatel=dod, doklad=doklad, datum=datum,
                     zdroj_email_id=msg, poznamka=pozn))


# =====================================================================
# 1) HAVEX Mobility – přefakturace (Pajerová / Kořínek / Křívánková)
# =====================================================================
SKIP_WHO = ('Havlíčk', 'Jakubičk', 'Opov', 'Hrásk')   # pokuty / přefakturace pronájmu
SKIP_DOC = {'5/2025/548'}                              # stornováno (skartace, msg 50583)
SKIP_BLOB_MSG = {'50556'}                              # stará verze 5/2025/1459 (platí 50555)
# SPZ na dokladu překlepem / mimo standardní formát (ověřeno proti přiložené faktuře servisu)
SPZ_FIX = {'5/2024/454': '8H02982', '5/2024/871': '8H02982', '5/2024/1756': 'AA996AA',
           '5/2025/116': '1ADX814', '5/2025/149': '1ADP984'}
KEEP_ALL = {'5/2024/1936'}   # stejné číslo dokladu u dvou různých vozů (8H34329, 8H34285)
# více verzí téhož dokladu v různých e-mailech -> ponech nejnovější (nižší message id = novější)
newest = {}
for f in sorted(os.listdir(RAW)):
    if re.fullmatch(r'\d{13}-\w{6}\.txt', f):
        t = open(f'{RAW}/{f}', encoding='utf-8', errors='ignore').read()
        if 'HAVEX Mobility' in t and 'Faktura - daňový doklad' in t and 'RX Auto' in t[:3000]:
            dd = parse_havex(t.split('\f')[0])['doc']
            mm = blob2msg.get(f[:-4], '')
            if mm and mm not in SKIP_BLOB_MSG and (dd not in newest or int(mm) < int(newest[dd])):
                newest[dd] = mm
hv_seen = set()
for f in sorted(os.listdir(RAW)):
    if not re.fullmatch(r'\d{13}-\w{6}\.txt', f):
        continue
    key = f[:-4]
    t = open(f'{RAW}/{f}', encoding='utf-8', errors='ignore').read()
    if 'HAVEX Mobility' not in t or 'Faktura - daňový doklad' not in t:
        continue
    msg = blob2msg.get(key, '')
    page1 = t.split('\f')[0]
    d = parse_havex(page1)
    if d.get('zaklad') is None:
        d = parse_havex(t)
    m = re.search(r'vystavil\(a\):[^\n]*\n\s*(\S[^\n]*?)\s{2,}|vystavil\(a\):[^\n]*\n\s*(\S.*)', page1)
    who = ((m.group(1) or m.group(2)) if m else '').strip()
    if 'RX Auto' not in t[:3000]:
        carn = 'Carnetto' in t[:3000]
        if not carn:
            skipped.append((d['doc'], 'odběratel není RX'))
            continue
    else:
        carn = False
    if any(w in who for w in SKIP_WHO):
        skipped.append((d['doc'], 'vystavil ' + who))
        continue
    if d['doc'] in SKIP_DOC or msg in SKIP_BLOB_MSG:
        skipped.append((d['doc'], 'storno / stará verze'))
        continue
    if d['doc'] not in KEEP_ALL and newest.get(d['doc']) and msg != newest[d['doc']]:
        skipped.append((d['doc'], 'starší verze dokladu (platí msg ' + newest[d['doc']] + ')'))
        continue
    datum = fdate(d['duzp'] or d['vyst'])
    found = spz_find(page1.split('Název zdanitelného plnění')[-1].split('bez DPH')[0]) \
        if 'Název zdanitelného plnění' in page1 else []
    inv_spz = found[0] if found else ''
    if not inv_spz and d['doc'] in SPZ_FIX:
        inv_spz = SPZ_FIX[d['doc']]
    dkey = (d['doc'], ','.join(found), round(d['zaklad'], 2))
    if dkey in hv_seen:
        skipped.append((d['doc'], 'duplicitní e-mail'))
        continue
    hv_seen.add(dkey)
    # položky
    items, cur = [], None
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
    # úvodní text bez částky ("Fakturujeme Vám opravu vozidla X") připoj k první položce
    intro = ' '.join(i['desc'] for i in items if i['amt'] is None)
    items = [i for i in items if i['amt'] is not None]
    dod = f'HAVEX Mobility s.r.o. ({who})' if who else 'HAVEX Mobility s.r.o.'
    base_note = 'odběratel Carnetto RX s.r.o.' if carn else ''
    if not items or abs(sum(i['amt'] for i in items) - d['zaklad']) > 1:
        kat, extra = cat_item(' '.join(d['items']), '')
        if kat == 'pokuty' or 'dotankov' in ' '.join(d['items']).lower():
            skipped.append((d['doc'], 'pokuta/palivo'))
            continue
        add(datum, inv_spz, kat, d['zaklad'], dod, d['doc'], msg,
            '; '.join(x for x in [base_note, extra, 'položky nerozparsovány', ('více SPZ: ' + ','.join(found)) if len(found) > 1 else ''] if x))
        stats['HAVEX'] += 1
        continue
    first = True
    prev_kat = None
    for it in items:
        desc = it['desc']
        sp = spz_find(desc)
        spz = sp[0] if sp else inv_spz
        kat, extra = cat_item(desc + ' ' + (intro if len(items) == 1 else ''), '')
        if 'sleva' in desc.lower() and prev_kat:
            kat, extra = prev_kat, 'sleva k předchozí položce'
        prev_kat = kat
        if kat == 'pokuty' or 'dotankov' in desc.lower() or 'palivo' in desc.lower():
            skipped.append((d['doc'], 'položka pokuta/palivo: ' + desc[:40]))
            continue
        poz = '; '.join(x for x in [base_note, extra, desc[:90], 'pozor: stejné č. dokladu i u jiného vozu' if d['doc'] in KEEP_ALL else ''] if x)
        if it['dph'] == '0' and 'spoluúčast' not in poz.lower():
            poz += '; 0% DPH'
        add(datum, spz, kat, it['amt'], dod, d['doc'], msg, poz)
        if first:
            stats['HAVEX'] += 1
            first = False

# =====================================================================
# 2) Auto Palace Západ (Tuchoměřice, IČ 09339299) – mytí (souhrnné), servis
# =====================================================================
APZ = 'Auto Palace Západ s.r.o.'
ap = [  # doklad, datum, kat, spz, základ, msg, pozn
    ('3411103351', '2024-06-25', 'servis', '9AF5141', 6995.19, '51077', 'prohlídka s výměnou oleje, brzdová kapalina'),
    ('3411104917', '2024-09-19', 'servis', '9AS2776', 5836.26, '51076', 'servis výměny oleje Multivan (stornováno dobropisem 3454100240)'),
    ('3454100240', '2024-12-04', 'servis', '9AS2776', -5836.26, '51071', 'dobropis k 3411104917'),
    ('3411106450', '2024-11-20', 'servis', '9AS2776', 12079.21, '51075', 'prohlídka, převodový olej DSG, Haldex, brzdová kapalina'),
    ('3411106539', '2024-11-22', 'oprava', '9AS2776', 7858.26, '51073', 'přední brzdové destičky + čidlo'),
    ('3411106760', '2024-11-30', 'myti', '', 12186.05, '51072', 'mytí exteriéru 104x (souhrnná měsíční faktura, bez SPZ)'),
    ('3411107211', '2024-12-31', 'myti', '', 11242.81, '51070', 'mytí exteriéru 101x (souhrnná, bez SPZ)'),
    ('3511100529', '2025-01-31', 'myti', '', 4365.29, '51069', 'mytí exteriéru 40x (souhrnná, bez SPZ); upomínka msg 51060'),
    ('3511100972', '2025-02-28', 'myti', '', 8403.18, '51067', 'mytí exteriéru 77x (souhrnná, bez SPZ)'),
    ('3511101286', '2025-03-31', 'myti', '', 14724.38, '51065', 'mytí exteriéru 126x (souhrnná, bez SPZ)'),
    ('3511101654', '2025-04-30', 'myti', '', 21608.18, '51064', 'mytí exteriéru 209x (souhrnná, bez SPZ)'),
    ('3511101985', '2025-05-30', 'myti', '', 29574.84, '51059', 'mytí exteriéru 271x (souhrnná, bez SPZ)'),
    ('3511102107', '2025-06-13', 'servis', '8H58993', 4993.29, '51058', 'servis výměny oleje'),
    ('3511102227', '2025-06-30', 'myti', '', 21481.81, '51057', 'mytí exteriéru 220x (souhrnná, bez SPZ)'),
    ('3511102444', '2025-07-29', 'servis', '8H58993', 1237.26, '51056', 'prohlídka'),
    ('3511102464', '2025-07-31', 'myti', '', 25020.00, '50993', 'mytí exteriéru 242x (souhrnná, bez SPZ)'),
    ('3511102634', '2025-08-29', 'myti', '', 23305.62, '50987', 'mytí exteriéru 223x (souhrnná, bez SPZ)'),
]
for doc, dt, kat, spz, a, msg, pz in ap:
    add(dt, spz, kat, a, APZ, doc, msg, pz, pob='PRG')
    stats['Auto Palace Západ'] += 1
add('2025-08-29', '9AC0255', 'servis', 20193.31, 'Auto Palace Butovice s.r.o.', '4258306343', '50988',
    'servis + brzdové kotouče/destičky Hyundai i30; odběratel uveden s adresou Smetanova 240, Úvaly')
stats['Auto Palace Butovice'] += 1

# =====================================================================
# 3) Autoservis Simon – Simon Závěšický (Ostrava, IČ 02148374)
# =====================================================================
SIM = 'Simon Závěšický (Autoservis Simon)'
sim = [  # doklad, datum, spz, [(kat, základ, pozn)], msg
    ('BA 2420019', '2024-01-25', '5SL1756', [('oprava', 1172.00, 'oprava ostřikovačů + zimní směs')], '51136'),
    ('BA 2420139', '2024-03-19', '6AU6673', [('oprava', 1878.00, 'refakturace DPH – čelní sklo (0 % DPH)')], '51136'),
    ('BA 2420169', '2024-04-04', '6AU6673', [('oprava', 2388.43, 'refakturace výměny bočního skla')], '51136'),
    ('BA 2420226', '2024-04-18', '8H25483', [('pneu', 650.00, 'přehození kol')], '51136'),
    ('BA 2420227', '2024-04-18', '9AV2367', [('pneu', 1150.00, 'přehození kol + uskladnění')], '51136'),
    ('BA 2420258', '2024-04-24', '9AV2356', [('pneu', 1000.00, 'přehození kol + uskladnění')], '51136'),
    ('BA 2420269', '2024-04-30', '', [('pneu', 1000.00, 'přehození kol + uskladnění; SPZ na dokladu chybí')], '51142'),
    ('BA 2420281', '2024-05-03', '8AD5179', [('pneu', 977.50, 'přezutí ALU 17-18"')], '51141'),
    ('BA 2420311', '2024-05-24', '9AF5144', [('pneu', 495.87, 'přehození kol')], '51140'),
    ('BA 2420320', '2024-05-24', '8H25692', [('pneu', 1000.00, 'přehození kol + uskladnění')], '51139'),
    ('BA 2420324', '2024-05-27', '8H02901', [('pneu', 1000.00, 'přehození kol + uskladnění')], '51137'),
    ('BA 2420355', '2024-05-29', '8AD5179', [('stk_znamky', 3300.00, 'STK + emise')], '51138'),
    ('BA 2420400', '2024-06-05', '6AU6673', [('oprava', 19814.00, 'panty dveří, zpětné zrcátko, práce'),
                                             ('pneu', 700.00, 'přehození kol')], '51188'),
    ('BA 2420408', '2024-06-06', '9AV2367', [('myti', 500.00, 'čištění a mytí vozidla')], '51136'),
    ('BA 2420419', '2024-06-07', '9AC0255', [('pneu', 4386.97, '2x pneu 225/40 R18 + přezutí + geometrie')], '51136'),
    ('BA 2420437', '2024-06-11', '9AD5392', [('pneu', 1000.00, 'přehození kol + uskladnění')], '51136'),
    ('BA 2420509', '2024-07-03', '8H25487', [('pneu', 1000.00, 'přehození kol + uskladnění')], '51189'),
    ('BA 2420533', '2024-07-23', '8H25487', [('oprava', 1218.15, 'diagnostika, olej, práce')], '51187'),
    ('BA 2420536', '2024-07-23', '6AU6673', [('servis', 5757.27, 'olej, filtry, kontrola úniku kapalin')], '51186'),
    ('BA 2420541', '2024-07-25', '9AT2239', [('servis', 3542.29, 'olej, filtr, AdBlue, diagnostika')], '51185'),
    ('BA 2420542', '2024-07-25', '8H04095', [('ostatni', 500.00, 'vyřízení reklamace vozidla')], '51184'),
    ('BA 2420708', '2024-10-10', '4AV0818', [('oprava', 29795.94, 'výměna turbodmychadla Mini Countryman, klimatizace'),
                                             ('ostatni', 1800.00, 'odtah vozidla')], '51180'),
    ('BA 2421072', '2024-12-18', '8H25483', [('servis', 4782.80, 'servis výměny oleje')], '51175'),
]
for doc, dt, spz, parts, msg in sim:
    for kat, a, pz in parts:
        add(dt, spz, kat, a, SIM, doc, msg, pz, pob='OSR')
    stats['Simon Závěšický'] += 1

# =====================================================================
# 4) Pavel Rejdík – neplátce DPH (částka = celkem), Praha, bez SPZ
# =====================================================================
REJ = 'Pavel Rejdík (neplátce DPH)'
rej = [
    ('20', '2024-07-11', '51089', [('pneu', 40600, 'přezutí 28x celá kola + 14x pneu, uskladnění (znovu zasláno 8.8.2024, msg 51088)')]),
    ('26', '2024-08-15', '51087', [('oprava', 10600, 'brzdy Kodiaq, Multivan, 3008'), ('pneu', 4600, 'oprava pneu 5x, pneu Goodyear'),
                                   ('servis', 11200, 'olej Superb, Camaro + AGM baterie'), ('stk_znamky', 7000, 'příprava a STK Mini, Kodiaq')]),
    ('35', '2024-12-27', '51086', [('pneu', 44800, 'přezutí 48 vozů + oprava pneu + pneu Karoq'), ('oprava', 1700, 'stabilizátory Multivan')]),
    ('49', '2025-06-20', '51085', [('oprava', 13700, 'destičky BMW, turbohadice Boxer, pružiny Mercedes A, baterie Camaro'),
                                   ('pneu', 3900, 'pneu Multivan, Kodiaq'), ('servis', 4000, 'olej + filtry Mercedes A (odhad podílu z 6000)')]),
    ('50', '2025-06-20', '51084', [('oprava', 14500, 'přední brzdy Audi A5')]),
    ('51', '2025-08-03', '51083', [('stk_znamky', 9200, 'Kodiaq STK + destičky + olej'), ('stk_znamky', 4500, 'BMW STK + přívěs STK')]),
    ('52', '2025-08-03', '51082', [('pneu', 41100, 'přezutí 45 vozů + uskladnění')]),
]
for doc, dt, msg, parts in rej:
    for kat, a, pz in parts:
        add(dt, '', kat, a, REJ, doc, msg, pz, pob='PRG')
    stats['Pavel Rejdík'] += 1
# oprava podílu v dokladu 49 (Mercedes A: olej 2000 / pružiny 4000) – součet = 21600
# =====================================================================
# 5) Autoservis MIRO (Přítluky, neplátce DPH, CZK) – vozy BTS
# =====================================================================
MIRO = 'Autoservis MIRO (neplátce DPH)'
miro = [
    ('150101653', '2024-09-16', '54595', [('5SD0063', 'servis', 3786.00, 'servis vč. zaokrouhlení 0,80')]),
    ('150101674', '2024-10-23', '54006', [('AA674AA', 'servis', 3646.00, ''), ('AA667AA', 'servis', 3646.00, ''), ('AA835AA', 'servis', 3646.00, ''),
                                          ('AA995AA', 'servis', 5707.60, 'vč. baterie 1720'), ('8H04098', 'ostatni', 360.00, 'kódování klíče'),
                                          ('8H02857', 'pneu', 1280.00, 'pneu/přezutí'), ('8H02857', 'servis', 634.80, 'ventilek, těsnění, olej'),
                                          ('NR500LP', 'pneu', 1280.00, 'přezutí'), ('5SD0063', 'pneu', 1280.00, 'přezutí'),
                                          ('5SD0063', 'ostatni', 90.00, 'baterie klíče'), ('', 'pneu', 320.60, 'likvidace pneu + zaokrouhlení')]),
    ('150101821', '2025-05-07', '54005', [('AA428BP', 'servis', 1356.00, ''), ('8H02857', 'servis', 7119.00, 'vč. kapaliny do ostřikovačů'),
                                          ('AA667AA', 'servis', 4041.20, ''), ('AA674AA', 'servis', 3920.40, ''), ('NR500LP', 'pneu', 700.00, 'přezutí'),
                                          ('AA835AA', 'pneu', 700.00, 'přezutí'), ('AA995AA', 'servis', 2995.20, ''), ('AA542HT', 'servis', 3235.20, ''),
                                          ('', 'servis', 793.80, 'zbytek dokladu – položky ve skenu nečitelné (AA667AA/AA674AA kapaliny) + zaokrouhlení')]),
    ('150101881', '2025-08-29', '54009', [('8H02853', 'servis', 14419.40, 'servis + opravy 27.05.2025'),
                                          ('5SD0063', 'servis', 7764.60, 'servis + opravy 16.06.2025 vč. zaokrouhlení 0,80')]),
]
for doc, dt, msg, parts in miro:
    for spz, kat, a, pz in parts:
        add(dt, spz, kat, a, MIRO, doc, msg, ('sken – ruční přepis; ' + pz).strip('; '), pob='BTS')
    stats['Autoservis MIRO'] += 1

# =====================================================================
# 6) Ostatní dodavatelé (jednotlivé faktury)
# =====================================================================
O = [  # datum, spz, kat, základ, dodavatel, doklad, msg, pozn, pobočka
    ('2024-01-16', '9AP5401', 'servis', 4410.54, 'IMOFA spol. s r.o.', '91240015', '53395', 'servisní prohlídka Fiat 500 (hotovostní doklad, sken)', None),
    ('2024-01-25', '', 'servis', 8890.91, 'ABV AUTO KLADNO s.r.o.', '224600079', '51145', 'servisní prohlídka, klimatizace, brzdová kapalina (SPZ na dokladu není)', 'PRG'),
    ('2024-04-04', '9AS2776', 'servis', -7024.11, 'Autosalon Klokočka Centrum a.s.', '2302400994', '55372', 'dobropis servisu z 09/2023 (dokl. 2302303743) – nesprávný odběratel', None),
    ('2024-06-10', '9AY0542', 'servis', 10506.33, 'CARDION CARS a.s.', '124712504', '55293', 'Volvo XC90 servisní prohlídka (olej, filtry, práce)', None),
    ('2024-06-10', '9AY0542', 'pneu', 69.00, 'CARDION CARS a.s.', '124712504', '55293', 'lepení pneu', None),
    ('2024-06-10', '9AY0542', 'ostatni', 83107.32, 'CARDION CARS a.s.', '124712504', '55293', 'tažné zařízení + montáž, střešní nosiče, box THULE, nosič kol – výbava vozu', None),
    ('2024-06-17', '7H21349', 'oprava', 22332.05, 'CB Auto a.s.', 'FV2413103153', '55369', 'oprava brzd / servis Škoda (České Budějovice)', None),
    ('2024-09-11', '9AI1081', 'servis', 5322.40, 'IMOFA spol. s r.o.', '72241176', '55367', 'servis Fiat 500 (filtry, olej, brzdová kapalina)', None),
    ('2024-10-03', '7AD3511', 'servis', 8585.95, 'Olfin Car Palace s.r.o.', '213008573', '51181', 'servisní prohlídka Peugeot Partner (sken)', None),
    ('2024-10-03', '7AD3511', 'stk_znamky', 1942.15, 'Olfin Car Palace s.r.o.', '213008573', '51181', 'STK + emise (sken)', None),
    ('2025-01-21', '', 'pneu', 9173.55, 'Pneu-Kvalitně.cz', '25100380', '53244', '4x Imperial 235/45 R20; ODHAD základu = 11100 s DPH / 1,21 (faktura jen odkazem, PDF není)', 'PRG'),
    ('2025-04-16', '', 'pneu', 1261.00, 'NejenPneu (IČ 61589004)', '20251330', '53174', '1x pneu 225/55 R18', 'PRG'),
    ('2025-06-05', '7AD3511', 'oprava', 25831.41, 'Olfin Car Palace s.r.o.', '213009655', '51127', 'brzdy, rozvody + vodní čerpadlo, vstřikovač AdBlue (sken)', None),
    ('2025-06-27', '7AN4239', 'servis', 3825.31, 'Auto Sael s.r.o.', 'FA251275', '51166', 'klimatizace + chladicí kapalina', None),
    ('2025-07-21', '', 'pneu', 2707.44, 'ABA MEDIA s.r.o. (sklad-pneu.cz)', 'FV2501950', '52036', 'pneu R18 (3276 s DPH)', 'PRG'),
    ('2025-07-30', '1AXI446', 'oprava', 22766.96, 'AUTO JAROV, s.r.o.', '7050002772', '51886', 'výměna a lakování zadního nárazníku, držáky čidel – pravděpodobně PU (Kooperativa), plnění neověřeno', None),
    ('2025-07-31', '1AXI446', 'ostatni', 2700.00, 'AUTO JAROV, s.r.o.', '6515002387', '51886', 'náhradní vůz Škoda Scala 3 dny (PU Kooperativa)', None),
    ('2025-07-31', '', 'myti', round(237.80 * EUR, 2), 'CASEDI WASH s.r.o. (SK)', '252060', '54051', 'mytí 45x 07/2025; 237,80 € bez DPH × 24,3 Kč/€; odběratel RX Auto SK s.r.o.', 'BTS'),
    ('2025-08-01', '', 'pneu', 5117.36, 'nakup24.cz s.r.o. (vsenaauto)', '25P0136069', '51863', '4x Triangle 245/45 R18', 'PRG'),
    ('2025-08-12', '', 'pneu', 5130.58, 'nakup24.cz s.r.o. (vsenaauto)', '25P0137733', '51707', '4x Imperial 205/55 R17 celoroční', 'PRG'),
    ('2025-08-15', '9AS2776', 'servis', 4850.00, 'Autoservis Brožek – Tomáš Kopecký (neplátce DPH)', 'FA250070', '51126', 'plnění klimatizace (sken)', None),
    ('2025-08-28', '5AM3366', 'oprava', 9156.00, 'VIP motors s.r.o.', '251170 / 202520004', '968',
     'PU Generali 9507232: faktura 30455,82 − dobropis 6535,82 = 23920 bez DPH, pojišťovna uhradila 14764; zde podíl RX (doplatek 14179,20 s DPH − odpočet DPH)', None),
]
for dt, spz, kat, a, dod, doc, msg, pz, pob in O:
    add(dt, spz, kat, a, dod, doc, msg, pz, pob=pob)
    stats[dod] += 0
for doc in sorted({o[5] for o in O}):
    stats['ostatní dodavatelé (počet faktur)'] += 1

# ---------------------------------------------------------------------
rows.sort(key=lambda r: (r['mesic'], r['dodavatel'], r['doklad']))
out = D + '/servis_2024.csv'
with open(out, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=['mesic', 'pobocka', 'spz', 'kategorie', 'castka_bez_dph', 'dodavatel',
                                       'doklad', 'datum', 'zdroj_email_id', 'poznamka'])
    w.writeheader()
    w.writerows(rows)

if __name__ == '__main__':
    tot = sum(r['castka_bez_dph'] for r in rows)
    print(f'{out}: {len(rows)} řádků, {len({(r["dodavatel"].split(" (")[0], r["doklad"]) for r in rows})} dokladů, celkem {tot:,.2f} Kč')
    bym = defaultdict(float); byd = defaultdict(float); byk = defaultdict(float); byp = defaultdict(float)
    for r in rows:
        bym[r['mesic']] += r['castka_bez_dph']; byk[r['kategorie']] += r['castka_bez_dph']; byp[r['pobocka']] += r['castka_bez_dph']
        byd[re.sub(r' \(.*', '', r['dodavatel'])] += r['castka_bez_dph']
    print('měsíce:', ' '.join(f'{k}:{v:,.0f}' for k, v in sorted(bym.items())))
    print('dodavatelé:', '; '.join(f'{k}: {v:,.0f}' for k, v in sorted(byd.items(), key=lambda x: -x[1])))
    print('kategorie:', '; '.join(f'{k}: {v:,.0f}' for k, v in sorted(byk.items(), key=lambda x: -x[1])))
    print('pobočky:', '; '.join(f'{k}: {v:,.0f}' for k, v in sorted(byp.items())))
    sk = defaultdict(int)
    for d_, why in skipped:
        sk[why.split(' ')[0] + ' ' + (why.split(' ')[1] if len(why.split(' ')) > 1 else '')] += 1
    print('vyřazeno:', dict(sk))
