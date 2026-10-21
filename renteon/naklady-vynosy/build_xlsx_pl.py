import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L
F=Font(name='Arial',size=10); B=Font(name='Arial',size=10,bold=True); BL=Font(name='Arial',size=10,color='0000FF'); G=Font(name='Arial',size=10,color='008000')
H=PatternFill('solid',fgColor='DDE4EE'); NF='#,##0;(#,##0);-'
def num(v):
    try: return float(v)
    except: return v
def sheet(wb,name,rows,hdr):
    ws=wb.create_sheet(name); ws.append(hdr)
    for r in rows: ws.append([num(r[k]) if k not in('mesic','spz','model','sipp','pobocka','poznamka','doklad','obdobi','vin','kategorie','zdroj_email_id') else r[k] for k in hdr])
    for c in ws[1]: c.font=B; c.fill=H
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font=BL if isinstance(c.value,(int,float)) else F
            if isinstance(c.value,(int,float)): c.number_format=NF
    for i,h in enumerate(hdr,1): ws.column_dimensions[L(i)].width=max(10,len(h)+2)
    ws.freeze_panes='A2'; return ws
wb=Workbook(); S=wb.active; S.title='Souhrn'
pl=list(csv.DictReader(open('pl_pobocky.csv'))); hp=list(pl[0].keys())
D=sheet(wb,'Data',pl,hp); n=len(pl)+1
col={h:L(i+1) for i,h in enumerate(hp)}
S['A1']='Náklady vs výnosy půjčovny 09/2025–10/2026 (Kč bez DPH)'; S['A1'].font=Font(name='Arial',size=12,bold=True)
br=['PRG','OSR','BTS','HAVEX_ZF']; names={'PRG':'Praha','OSR':'Ostrava','BTS':'Bratislava','HAVEX_ZF':'HAVEX zpětná fakt.'}
S.append([]); S.append(['Položka']+[names[b] for b in br]+['Celkem'])
for c in S[3]: c.font=B; c.fill=H
items=[('Výnos Renteon','vynos_renteon'),('Výnos Vyfakturuj / HAVEX','vynos_vyfakturuj'),('Výnosy celkem','vynos_celkem'),('Leasing (kalendáře)','leasing'),('Leasing (odhad)','leasing_odhad'),('Carnetto – půjčovné EFS','carnetto_leasing'),('Pojištění','pojisteni'),('Carnetto – pojištění ČGP','carnetto_pojisteni'),('Servis','servis'),('Opravy','opravy'),('Ostatní','ostatni'),('Náklady celkem','naklady_celkem'),('Výsledek','vysledek')]
for t,k in items:
    r=S.max_row+1; S.cell(r,1,t).font=B if k in('vynos_celkem','naklady_celkem','vysledek') else F
    for j,b in enumerate(br,2):
        c=S.cell(r,j,f"=SUMIFS(Data!${col[k]}$2:${col[k]}${n},Data!$B$2:$B${n},\"{b}\")"); c.font=G; c.number_format=NF
    c=S.cell(r,6,f"=SUM(B{r}:E{r})"); c.number_format=NF; c.font=B
r=S.max_row+1; S.cell(r,1,'Marže').font=B
for j in range(2,7):
    c=S.cell(r,j,f"=IF({L(j)}6=0,0,{L(j)}{r-1}/{L(j)}6)"); c.number_format='0.0%;(0.0%);-'; c.font=F
S.column_dimensions['A'].width=28
for j in range(2,7): S.column_dimensions[L(j)].width=16
au=list(csv.DictReader(open('pl_auta.csv'))); sheet(wb,'Auta',au,list(au[0].keys()))
cm=list(csv.DictReader(open('carnetto_mesice.csv'))); sheet(wb,'Carnetto',cm,list(cm[0].keys()))
cd=list(csv.DictReader(open('carnetto.csv'))); sheet(wb,'Carnetto detail',cd,list(cd[0].keys()))
P=wb.create_sheet('Poznámky')
for t in ['Zdroje: Renteon (výnosy po pobočkách a vozech), Vyfakturuj RX Auto + RX Auto SK, Spark (HAVEX kalendáře, EFS, Kooperativa, Generali, D.A.S., servisy).',
 'Carnetto RX: půjčovné EURO FLEET SERVIS (11/2025–09/2026, 11 faktur) a pojištění flotily ČGP 6287974108 (04–09/2026) – přefakturováno na RX Auto, rozpis po SPZ z faktur/vyúčtování.',
 'Faktury EFS i vyúčtování ČGP za 10/2026 zatím nepřišly – říjen je v nákladech podhodnocen.',
 'Bratislava přepočtena kurzem 24,3 Kč/€ (předpoklad).',
 'Leasing starších smluv bez platebního kalendáře = odhad z HAVEX přehledu zápůjček (pro rata).',
 'HAVEX_ZF = vozy se zpětnou fakturací HAVEX Mobility: výnos z Vyfakturuj vs leasing těch vozů.',
 'Chybí: palivo/DKV, mzdy, nájmy poboček, provize brokerů, franšíza, IT. Servisní faktury ve schránce až od 09/2025.',
 'Modrá = vstupní data, zelená = odkaz na list Data, černá = výpočet.']:
    P.append([t]); P.cell(P.max_row,1).font=F
P.column_dimensions['A'].width=140
wb.save('Naklady_vs_vynosy_2025-2026.xlsx')
