import sys, subprocess, re, json

AMT = re.compile(r'^(.*?)\s{2,}(-?[\d ]+,\d\d)\s*$')
def num(s): return float(s.replace(' ', '').replace(',', '.'))

def parse(path):
    t = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout
    L = [l.rstrip() for l in t.split('\n')]
    d = {'file': path, 'A': [], 'PU': [], 'other': []}
    for l in L:
        m = re.search(r'Datum vrácení vozu:\s*(\d\d\.\d\d\.\d{4})\s+(\d+)', l)
        if m: d['vraceno'], d['cislo'] = m.groups()
        m = re.search(r'Značka a typ:\s*(.*?)\s{2,}RZ:\s*(\S+)', l)
        if m: d['vuz'], d['rz'] = m.group(1).strip(), m.group(2)
        m = re.search(r'Stav km:\s*(\d+).*VIN:\s*(\S+)', l)
        if m: d['km'], d['vin'] = m.group(1), m.group(2).upper()
        m = re.search(r'Ujeté nadlimitní km - (\d+) km se sazbou ([\d,]+)', l)
        if m: d['km_over'] = int(m.group(1)); d['havex_rate'] = num(m.group(2))
        m = re.search(r'CELKEM K ÚHRADĚ.*?([\d ]+,\d\d)\s*$', l)
        if m: d['havex_total'] = num(m.group(1))
    dates = re.findall(r'^\s+(?:Praha\s+)?(\d\d\.\d\d\.\d{4})\s*$', t, re.M)
    d['dat_protokolu'] = dates[-1] if dates else ''
    sec = None; pu_hdr = 0
    for l in L:
        s = l.strip()
        if not s: continue
        if s.startswith('NEAKCEPTOVATELNÉ'): sec = 'A'; continue
        if s.startswith('Celková škoda k úhradě bez DPH,'): sec = 'after'; continue
        if s.startswith('Celková škoda k úhradě bez DPH'): sec = None; continue
        if s.startswith('POŠKOZENÍ ŘEŠENÁ JAKO PU'):
            pu_hdr += 1; sec = 'PU' if pu_hdr == 1 else None; continue
        if s.startswith('CELKEM K ÚHRADĚ'): sec = None; continue
        if sec in ('A', 'PU'):
            m = AMT.match(s)
            desc, amt = (m.group(1).strip(), num(m.group(2))) if m else (s, None)
            d[sec].append((desc, amt))
        elif sec == 'after':
            m = AMT.match(s)
            if m and not s.startswith('Ujeté nadlimitní') and not s.startswith('Zákaznická výhoda'):
                d['other'].append((m.group(1).strip(), num(m.group(2))))
            if s.startswith('Zákaznická výhoda') and m and num(m.group(2)) != 0:
                d['other'].append(('Zákaznická výhoda', num(m.group(2))))
    # SPU from HAVEX for check
    spu = re.search(r'Spoluúčast hrazená klientem\s+(\d+)\s+([\d ]+,\d\d)', t)
    d['havex_spu'] = num(spu.group(2)) if spu else 0
    d['pu_count'] = int(spu.group(1)) if spu else 0
    # clean A
    priced = [x for x, a in d['A'] if a is not None]
    clean = []
    for x, a in d['A']:
        if 'HRADÍ KLIENT' in x or 'Kč bez DPH' in x: continue
        if x.startswith('č. dílu'): x = 'Exteriér - Motor - Zakrytí - Poškozené, výměna (' + x + ')'
        if a is None and any(p.startswith(x) or p.rsplit(' - ',1)[0]==x.rsplit(' - ',1)[0] for p in priced): continue
        clean.append((x, a))
    d['A'] = clean
    d['PU'] = [(x, a) for x, a in d['PU'] if a is not None]
    d['A_sum'] = sum(a for _, a in d['A'] if a)
    d['km_over'] = d.get('km_over', 0)
    chk = d['A_sum'] + d['havex_spu'] + round(d['km_over'] * d.get('havex_rate', 0) + 1e-9 + 0.5 - 0.5) + sum(a for _, a in d['other'])
    d['check_diff'] = round(d['havex_total'] - chk, 2)
    return d

if __name__ == '__main__':
    out = [parse(p) for p in sys.argv[2:]]
    json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
    for d in out:
        print(d['rz'], d['cislo'], d['vraceno'], d['dat_protokolu'], 'A', d['A_sum'], 'PU', [a for _, a in d['PU']],
              'spuH', d['havex_spu'], 'km', d['km_over'], 'other', d['other'], 'tot', d['havex_total'], 'diff', d['check_diff'])
