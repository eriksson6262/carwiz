#!/usr/bin/env python3
"""KONKURENCE workbook from data/DC.json: per vzorek × třída – Carwiz (min za SIPP) + 6 nejlevnějších konkurentů."""
import json, os, sys, datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Font
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.environ.get('RUN_DATE')
SRC = os.environ.get('SRC', 'DC')   # DC = DiscoverCars, CT = CarTrawler (cars.easyjet.com)
sys.path.insert(0, os.path.dirname(__file__))
from reprice import expand
dc = expand(json.load(open(f'{BASE}/data/{SRC}.json')))
wb = Workbook(); ws = wb.active; ws.title = {'CT': 'CarTrawler easyJet', 'WZ': 'CarTrawler Wizz Air', 'RC': 'Rentalcars'}.get(SRC, 'DiscoverCars')
hdr = ['Pobočka', 'Vyzvednutí', 'Dní', 'Skupina', 'Carwiz SIPP', 'Carwiz €'] + sum([[f'{i}. konk.', 'SIPP', '€'] for i in range(1, 7)], [])
ws.append([{'CT': 'CarTrawler – easyJet (cars.easyjet.com, clientID 512111)', 'WZ': 'CarTrawler – Wizz Air (cars.wizzair.com, clientID 602653)', 'RC': 'Rentalcars.com (Booking)'}.get(SRC, 'DiscoverCars') + f' – ceny celkem s DPH a marží brokera, běh {RUN} (automaty, bez dodávek; VANA = automatické dodávky; PREM = P/U/G)'])
ws.append(hdr)
for c in ws[2]: c.font = Font(bold=True)
for r in sorted(dc['res'], key=lambda x: (x['L'], x['p'], x['du'])):
    for k in ['E', 'C', 'I', 'F', 'S', 'PREM', 'VANA']:
        comp = r['comp'].get(k, [])
        cw = {s: v for s, v in r['cw'].items() if (s[0] == k if len(k) == 1 else (s in ('GFAR', 'LFAR') if k == 'PREM' else s[1] == 'V'))}
        if not comp and not cw: continue
        cs = min(cw, key=cw.get) if cw else None
        row = [r['L'], dt.date.fromisoformat(r['p']), r['du'], k, cs, cw.get(cs) if cs else None]
        for x in comp[:6]: row += [x[1], x[2], x[0]]
        ws.append(row); ws.cell(row=ws.max_row, column=2).number_format = 'DD.MM.YYYY'
ws.auto_filter.ref = f'A2:{ws.cell(row=ws.max_row, column=len(hdr)).coordinate}'
ws.freeze_panes = 'A3'
p = f'{BASE}/out/xlsx/{RUN}_KONKURENCE_' + {'CT': 'CarTrawler', 'WZ': 'CarTrawler_Wizzair', 'RC': 'Rentalcars'}.get(SRC, 'DiscoverCars') + '.xlsx'; wb.save(p); print(p)
