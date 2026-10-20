import sys
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.utils import get_column_letter as L

rows=list(csv.DictReader(open(sys.argv[1] if len(sys.argv)>1 else 'data/vynosy_flotila_v2.csv')))
F='Arial'; C25='E07B39'; C26='2F6DB5'
hdr=Font(name=F,bold=True,color='FFFFFF'); hfill=PatternFill('solid',fgColor='1F2937')
f=Font(name=F); fb=Font(name=F,bold=True); blue=Font(name=F,color='0000FF'); grey=Font(name=F,italic=True,color='6B7280')
thin=Border(bottom=Side(style='thin',color='D1D5DB'))
wb=Workbook()

# ---- Data
ds=wb.active; ds.title='Data'
dcols=[('mesic','Měsíc'),('pobocka','Pobočka'),('zeme','Země'),('mena','Měna'),('vynos_celkem','Výnos celkem bez DPH'),
 ('najem','Nájem'),('pojisteni','Pojištění'),('poplatky_bez_pokut','Poplatky bez pokut'),('skody','Škody'),('ostatni','Ostatní'),
 ('pokuty','Pokuty (přeúčtované)'),('zprac_pokut','Zpracování pokut'),('pocet_pokut','Počet pokut'),('smluv','Smluv'),('dni','Dní'),('vozidel','Ø vozidel')]
ds.append([h for _,h in dcols])
for r in rows:
    ds.append([r[k] if i<4 else (float(r[k]) if k=='vozidel' else int(r[k])) for i,(k,_) in enumerate(dcols)])
N=len(rows)+1
CL={k:L(i+1) for i,(k,_) in enumerate(dcols)}
# derived column: výnos bez pokut (formula)
ds.cell(1,17,'Výnos bez pokut')
for r in range(2,N+1): ds.cell(r,17,f'={CL["vynos_celkem"]}{r}-{CL["pokuty"]}{r}-{CL["zprac_pokut"]}{r}')
CL['vynos_bez_pokut']='Q'
for c in ds[1]: c.font=hdr; c.fill=hfill; c.alignment=Alignment(wrap_text=True,horizontal='center')
ds.row_dimensions[1].height=30
for row in ds.iter_rows(min_row=2,max_row=N):
    for c in row: c.font=blue if 5<=c.column<=16 else f
    for c in row[4:15]: c.number_format='#,##0'
    row[15].number_format='0.0'; row[16].number_format='#,##0'; row[16].font=f
for i,w in enumerate([10,9,7,7,14,12,12,14,11,11,13,13,9,8,8,10,14],1): ds.column_dimensions[L(i)].width=w
ds.freeze_panes='C2'
notes=['Zdroj: Renteon CZ (rxauto.s3) a SK (cwslovakia.s6), report Realizace po kancelářích – podle data vyúčtování, bez DPH; CZ v Kč, SK v €.',
 'Pokuty = položky dokladů typu dopravní pokuta / mýtné / parkování (typ služby 14) a poplatek za jejich zpracování, podle data dokladu; přiřazeno pobočce rezervace, doklady bez smlouvy pobočce dokladu. Odečteny z poplatků.',
 'Ø vozidel: report Stav flotily po kancelářích, flotila Pronájem vozového parku, průměr v měsíci. Staženo 20. 10. 2026; říjen 2026 jen do 20. 10.']
for i,t in enumerate(notes): ds.cell(N+2+i,1,t).font=grey
D=lambda col: f"Data!${CL[col]}$2:${CL[col]}${N}"

MES=['leden','únor','březen','duben','květen','červen','červenec','srpen','září','říjen','listopad','prosinec']
names={'PRG':'Praha (PRG)','OSR':'Ostrava (OSR)','BTS':'Bratislava (BTS)'}
cur={'PRG':'Kč','OSR':'Kč','BTS':'€'}
fields=[('vynos_bez_pokut','Výnos bez pokut'),('najem','Nájem'),('pojisteni','Pojištění'),('poplatky_bez_pokut','Poplatky bez pokut'),
        ('skody','Škody'),('pok','Pokuty vč. zprac.'),('smluv','Smluv'),('vozidel','Ø vozidel'),('nv','Výnos na vůz')]
NF=len(fields); IV=0; IVOZ=7; ISML=6

def cond(key,p,expr):
    return f'=IF(COUNTIFS({D("mesic")},{key},{D("pobocka")},"{p}")=0,"",{expr})'
def sif(col,key,p): return f'SUMIFS({D(col)},{D("mesic")},{key},{D("pobocka")},"{p}")'

for p in ['PRG','OSR','BTS']:
    ws=wb.create_sheet(p)
    ws['A1']=f"{names[p]} – výnos bez DPH a bez pokut ({cur[p]}), smlouvy a flotila po měsících"; ws['A1'].font=Font(name=F,bold=True,size=14)
    for col,t in [(1,'Měsíc'),(2,'Klíč 2025'),(3,'Klíč 2026')]:
        c=ws.cell(3,col,t); c.font=hdr; c.fill=hfill
    start=4
    for yi,y in enumerate(['2025','2026']):
        for fi,(k,t) in enumerate(fields):
            c=ws.cell(3,start+yi*NF+fi,f"{t} {y}"); c.font=hdr; c.fill=PatternFill('solid',fgColor=C25 if y=='2025' else C26)
            c.alignment=Alignment(wrap_text=True,horizontal='center')
    for m in range(12):
        r=4+m
        ws.cell(r,1,MES[m]).font=f
        ws.cell(r,2,f"2025-{m+1:02d}"); ws.cell(r,3,f"2026-{m+1:02d}")
        for yi in range(2):
            key=f"$B{r}" if yi==0 else f"$C{r}"; base=start+yi*NF
            for fi,(k,t) in enumerate(fields):
                c=ws.cell(r,base+fi)
                if k=='nv':
                    v=L(base+IV); z=L(base+IVOZ); c.value=f'=IF(OR({v}{r}="",{z}{r}=""),"",{v}{r}/{z}{r})'
                elif k=='pok':
                    c.value=cond(key,p,sif('pokuty',key,p)+'+'+sif('zprac_pokut',key,p))
                elif k=='vynos_bez_pokut':
                    c.value=cond(key,p,sif('vynos_celkem',key,p)+'-'+sif('pokuty',key,p)+'-'+sif('zprac_pokut',key,p))
                else:
                    c.value=cond(key,p,sif(k,key,p))
                c.font=f; c.number_format='0.0' if k=='vozidel' else '#,##0'; c.border=thin
    tr=17
    ws.cell(tr,1,'Leden–září').font=fb
    for yi in range(2):
        base=start+yi*NF
        for fi,(k,t) in enumerate(fields):
            col=L(base+fi); c=ws.cell(tr,base+fi)
            if k=='vozidel': c.value=f'=AVERAGE({col}4:{col}12)'
            elif k=='nv': c.value=f'={L(base+IV)}{tr}/{L(base+IVOZ)}{tr}/9'
            else: c.value=f'=SUM({col}4:{col}12)'
            c.font=fb; c.number_format='0.0' if k=='vozidel' else '#,##0'
    ws.cell(18,1,'Změna 2026/2025').font=fb
    for fi in range(NF):
        c=ws.cell(18,start+NF+fi,f'=IFERROR({L(start+NF+fi)}17/{L(start+fi)}17-1,"")'); c.number_format='+0.0%;-0.0%;0.0%'; c.font=fb
    ws.cell(19,1,'Výnos bez pokut = výnos celkem − přeúčtované pokuty − poplatek za zpracování. Výnos na vůz = výnos bez pokut / Ø vozidel. Říjen 2026 neúplný (do 20. 10.).').font=grey
    ws.column_dimensions['A'].width=16; ws.column_dimensions['B'].hidden=True; ws.column_dimensions['C'].hidden=True
    for i in range(4,4+2*NF): ws.column_dimensions[L(i)].width=12
    ws.row_dimensions[3].height=32; ws.freeze_panes='D4'

    # chart 1: bars výnos + lines vozidla, colour per year
    bar=BarChart(); bar.type='col'; bar.grouping='clustered'; bar.overlap=-10; bar.gapWidth=60
    bar.title=f"{names[p]}: výnos bez pokut ({cur[p]}) a Ø vozidel"; bar.y_axis.title=f"Výnos {cur[p]}"
    for yi,col in enumerate([C25,C26]):
        bar.add_data(Reference(ws,min_col=start+yi*NF+IV,min_row=3,max_row=15),titles_from_data=True)
        s=bar.series[-1]; s.graphicalProperties.solidFill=col; s.graphicalProperties.line.solidFill=col
    bar.set_categories(Reference(ws,min_col=1,min_row=4,max_row=15))
    line=LineChart()
    for yi,col in enumerate([C25,C26]):
        line.add_data(Reference(ws,min_col=start+yi*NF+IVOZ,min_row=3,max_row=15 if yi==0 else 13),titles_from_data=True)
        s=line.series[-1]; s.graphicalProperties.line.solidFill=col; s.graphicalProperties.line.width=38000
        s.marker.symbol='circle'; s.marker.size=7; s.marker.graphicalProperties.solidFill=col; s.marker.graphicalProperties.line.solidFill=col; s.smooth=False
    line.y_axis.axId=200; line.y_axis.title='Ø vozidel'; line.y_axis.crosses='max'; line.y_axis.majorGridlines=None
    bar+=line; bar.height=10; bar.width=26; bar.legend.position='b'
    ws.add_chart(bar,'A21')

    # chart 2: smlouvy po měsících (same colours)
    sm=BarChart(); sm.type='col'; sm.grouping='clustered'; sm.gapWidth=60; sm.title=f"{names[p]}: počet smluv"
    for yi,col in enumerate([C25,C26]):
        sm.add_data(Reference(ws,min_col=start+yi*NF+ISML,min_row=3,max_row=15),titles_from_data=True)
        s=sm.series[-1]; s.graphicalProperties.solidFill=col; s.graphicalProperties.line.solidFill=col
    sm.set_categories(Reference(ws,min_col=1,min_row=4,max_row=15)); sm.height=10; sm.width=18; sm.legend.position='b'
    ws.add_chart(sm,'Q21')

    # timeline breakdown
    t0=43
    ws.cell(t0-1,1,'Rozpad výnosu po měsících').font=Font(name=F,bold=True,size=12)
    th=['Měsíc','Nájem','Pojištění','Poplatky bez pokut','Škody','Ostatní','Pokuty vč. zprac.','Výnos celkem','Smluv']
    for i,h in enumerate(th): c=ws.cell(t0,1+i,h); c.font=hdr; c.fill=hfill
    months=sorted({r['mesic'] for r in rows})
    for j,mk in enumerate(months):
        r=t0+1+j; ws.cell(r,1,mk).font=f; key=f'$A{r}'
        for i,k in enumerate(['najem','pojisteni','poplatky_bez_pokut','skody','ostatni']):
            c=ws.cell(r,2+i,'='+sif(k,key,p)); c.number_format='#,##0'; c.font=f
        c=ws.cell(r,7,'='+sif('pokuty',key,p)+'+'+sif('zprac_pokut',key,p)); c.number_format='#,##0'; c.font=f
        c=ws.cell(r,8,'='+sif('vynos_celkem',key,p)); c.number_format='#,##0'; c.font=f
        c=ws.cell(r,9,'='+sif('smluv',key,p)); c.number_format='#,##0'; c.font=f
    last=t0+len(months)
    st=BarChart(); st.type='col'; st.grouping='stacked'; st.overlap=100; st.gapWidth=40
    st.title=f"{names[p]}: rozpad výnosu vč. vyčleněných pokut ({cur[p]})"
    st.add_data(Reference(ws,min_col=2,max_col=7,min_row=t0,max_row=last),titles_from_data=True)
    st.set_categories(Reference(ws,min_col=1,min_row=t0+1,max_row=last))
    for s,col in zip(st.series,['2F6DB5','2BA58F','E0B33A','D2555A','8B5CF6','9CA3AF']):
        s.graphicalProperties.solidFill=col; s.graphicalProperties.line.solidFill=col
    st.height=10; st.width=26; st.legend.position='b'
    ws.add_chart(st,f'K{t0}')

# ---- Souhrn
ss=wb.create_sheet('Souhrn',0)
ss['A1']='Výnosy, smlouvy a flotila – leden–září 2025 vs 2026'; ss['A1'].font=Font(name=F,bold=True,size=14)
ss['A2']='Výnos bez DPH a bez přeúčtovaných pokut (CZ v Kč, SK v €); pokuty vč. zpracování vyčleněny zvlášť. Hodnoty z listů poboček.'; ss['A2'].font=grey
h=['Pobočka','Měna','Výnos bez pokut 2025','Výnos bez pokut 2026','Změna výnosu','Smluv 2025','Smluv 2026','Změna smluv',
   'Ø vozidel 2025','Ø vozidel 2026','Výnos na vůz/měs. 2025','Výnos na vůz/měs. 2026','Změna výnosu na vůz',
   'Výnos na smlouvu 2025','Výnos na smlouvu 2026','Nájem 2025','Nájem 2026','Pojištění 2025','Pojištění 2026','Poplatky bez pokut 2025','Poplatky bez pokut 2026','Škody 2025','Škody 2026','Pokuty vč. zprac. 2025','Pokuty vč. zprac. 2026']
for i,t in enumerate(h,1):
    c=ss.cell(4,i,t); c.font=hdr; c.fill=hfill; c.alignment=Alignment(wrap_text=True,horizontal='center')
ss.row_dimensions[4].height=44
fidx={k:i for i,(k,_) in enumerate(fields)}
for j,p in enumerate(['PRG','OSR','BTS']):
    r=5+j
    ss.cell(r,1,names[p]).font=fb; ss.cell(r,2,cur[p]).font=f
    g=lambda yi,k: f"={p}!{L(4+yi*NF+fidx[k])}17"
    vals=[g(0,'vynos_bez_pokut'),g(1,'vynos_bez_pokut'),f'=D{r}/C{r}-1',g(0,'smluv'),g(1,'smluv'),f'=G{r}/F{r}-1',
          g(0,'vozidel'),g(1,'vozidel'),g(0,'nv'),g(1,'nv'),f'=L{r}/K{r}-1',f'=C{r}/F{r}',f'=D{r}/G{r}',
          g(0,'najem'),g(1,'najem'),g(0,'pojisteni'),g(1,'pojisteni'),g(0,'poplatky_bez_pokut'),g(1,'poplatky_bez_pokut'),g(0,'skody'),g(1,'skody'),g(0,'pok'),g(1,'pok')]
    for i,v in enumerate(vals):
        c=ss.cell(r,3+i,v); c.font=Font(name=F,color='000000' if v.startswith('=') and '!' not in v else '008000')
        c.number_format='+0.0%;-0.0%;0.0%' if i in (2,5,10) else ('0.0' if i in (6,7) else '#,##0')
for i,w in enumerate([18,7]+[12]*23,1): ss.column_dimensions[L(i)].width=w
ss.freeze_panes='C5'
ss['A9']='Pozn.: v 2025 se pokuty za celou flotilu fakturovaly převážně přes pobočku Ostrava (účty bez smlouvy); od září 2025 jsou u smluv pobočky rezervace.'; ss['A9'].font=grey
wb.save(sys.argv[2] if len(sys.argv)>2 else 'output/Vynosy_flotila.xlsx')
