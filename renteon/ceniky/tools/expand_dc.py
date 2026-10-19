#!/usr/bin/env python3
"""19.10.2026: rozbalí komprimovaný DC sběr (sup + res[L,p,du,cw,comp]) do formátu pro reprice.py.
Použití: python3 tools/expand_dc.py data/DC.json   (přepíše na místě, už rozbalený soubor nechá)"""
import json, sys
p = sys.argv[1]; x = json.load(open(p))
if x.get('res') and isinstance(x['res'][0], list):
    sup = x['sup']
    x['res'] = [dict(L=L, p=pd, du=du, cw=cw,
                     comp={k: [[c[0], sup[c[1]] if isinstance(c[1], int) else c[1], c[2]] for c in v] for k, v in comp.items()})
                for L, pd, du, cw, comp in x['res']]
    json.dump(x, open(p, 'w')); print('rozbaleno', len(x['res']))
else:
    print('už rozbaleno')
