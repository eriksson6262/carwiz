# Sloučí TSV z CZ a SK Renteonu, vyloučí e-maily klientů se škodou/pokutou, vytvoří xlsx. Spouštět ve složce s daty.
import re, openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
bad=set()
for f in ['renteon_vyloucene_CZ.txt','renteon_vyloucene_SK.txt']:
    bad|={l.strip() for l in open(f,encoding='utf-8') if l.strip()}
rows={}
for f in ['renteon_kontakty_CZ_raw.tsv','renteon_kontakty_SK_raw.tsv']:
    for l in open(f,encoding='utf-8-sig'):
        p=l.rstrip('\n').split('\t')
        if len(p)<11: continue
        inst,nm,em,ph,off,n,last,num,ag,proxy,ns=p
        if em in bad: continue
        o=rows.get(em)
        if not o:
            rows[em]=dict(nm=nm,em=em,ph=ph,inst={inst},off=set(filter(None,off.split('/'))),n=int(n),last=last,num=num,ag=set(filter(None,ag.split('/'))),proxy=proxy,ns=ns)
        else:
            o['inst'].add(inst);o['off']|=set(filter(None,off.split('/')));o['n']+=int(n);o['ag']|=set(filter(None,ag.split('/')))
            o['nm']=o['nm'] or nm; o['ph']=o['ph'] or ph
            if last>o['last']: o['last'],o['num']=last,num
            if ns: o['ns']=ns
ok=re.compile(r'^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)*\.[a-z]{2,}$')
fake=re.compile(r'^x+@|@x+\.|noreply|no-reply|test@|@test\.|@example|nomail|@mail\.com$')
def note(o):
    e=o['em']
    if not ok.match(e) or fake.search(e): return 'podezřelý e-mail'
    if o['proxy']: return 'e-mail brokera (proxy)'
    return ''
out=sorted(rows.values(),key=lambda o:o['last'],reverse=True)
wb=openpyxl.Workbook();ws=wb.active;ws.title='Kontakty'
ws.append(['Jméno','E-mail','Telefon','Renteon','Pobočky','Počet pronájmů','Poslední pronájem','Poslední smlouva','Broker/agentura','Poznámka','Nechce průzkumy'])
for o in out:
    ws.append([o['nm'],o['em'],o['ph'],'/'.join(sorted(o['inst'])),'/'.join(sorted(o['off'])),o['n'],o['last'],o['num'],'/'.join(sorted(o['ag'])),note(o),o['ns']])
for c in ws[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='1F4E78')
for i,w in enumerate([28,36,18,9,12,10,13,15,22,22,12],1): ws.column_dimensions[get_column_letter(i)].width=w
ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
wb.save('Kontakty_klientu_bez_skod_a_pokut.xlsx')
print(len(out),'kontaktů')
