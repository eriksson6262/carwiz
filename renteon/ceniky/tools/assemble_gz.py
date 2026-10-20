#!/usr/bin/env python3
"""20.10.2026: složí výstupy javascript_tool s prefixem PFX (PFXP1/n#<base64 gzip>#END) z tool-results do JSON souboru.
Použití: TR=<adresář tool-results> python3 assemble_gz.py PFX výstup.json"""
import json, glob, re, sys, os, base64, gzip
D = os.environ['TR'].rstrip('/') + '/'
PFX, OUTF = sys.argv[1], sys.argv[2]
dec = json.JSONDecoder(); parts = {}
for f in sorted(glob.glob(D + '*.txt')):
    try: t = json.load(open(f))[0]['text']
    except Exception: continue
    try: s, _ = dec.raw_decode(t)
    except Exception: continue
    if not isinstance(s, str): continue
    m = re.match(re.escape(PFX) + r'P(\d+)/(\d+)#', s)
    if not m or '#END' not in s: continue
    parts[int(m[1])] = (int(m[2]), s[m.end():s.rindex('#END')])
n = next(iter(parts.values()))[0]; assert sorted(parts) == list(range(1, n + 1)), sorted(parts)
b = ''.join(parts[i][1] for i in range(1, n + 1))
txt = gzip.decompress(base64.b64decode(b)).decode()
json.dump(json.loads(txt), open(OUTF, 'w')); print('ok', PFX, len(txt))
