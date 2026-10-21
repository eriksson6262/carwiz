import sys,csv,re,glob,subprocess,collections
sys.path.insert(0,'scripts')
from carnetto_efs import parse_txt,parse_ocr,D
from gcpparse import parse as gparse
EMAIL={'3900250105':41576,'3900250115':41084,'3900260013':40417,'3900260030':39687,'3900260074':38739,'3900260098':37703,
       '3900260136':34926,'3900260191':623,'3900260250':24858,'3900260308':17275,'3900260351':5841}
rows=[]; chk=[]
def mes(obd):
    m=re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$',obd) or re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',obd)
    return f"{m.group(3)}-{int(m.group(2)):02d}"
for f in ['3900250105','3900250115','3900260013','3900260030','3900260074','3900260098','3900260136','3900260191','3900260250']:
    it,oth,zd,duzp=parse_txt(D+'efs/'+f+'.txt')
    for x in it:
        model=re.sub(r'1A\w*$','',x['model']); spz=x['spz']; extra=''
        if spz=='9H05900': spz='8H85900'; extra='; na faktuře uvedeno 9H0 5900 (překlep, od 07/2026 i v GČP 8H8 5900)'
        rows.append(dict(mesic=mes(x['obdobi']),spz=spz,vin='',kategorie='leasing',castka_bez_dph=f"{x['castka']:.2f}",doklad=f"EFS {f}",
            obdobi=x['obdobi'],zdroj_email_id=EMAIL[f],poznamka=f"EURO FLEET SERVIS, půjčovné Škoda {model}; DUZP {duzp}{extra}"))
    chk.append((f,duzp,len(it),round(sum(x['castka'] for x in it),2),zd))
ZD={'3900260308':716379.35,'3900260351':726778.67}
for f,ps,duzp in [('3900260308',['scan/aug300-2.txt','scan/aug300-3.txt'],'31.08.2026'),('3900260351',['scan/s351-2.txt','scan/s351-3.txt'],'30.09.2026')]:
    it=parse_ocr([D+p for p in ps],None)
    for x in it:
        rows.append(dict(mesic=mes(x['obdobi']),spz=x['spz'],vin='',kategorie='leasing',castka_bez_dph=f"{x['castka']:.2f}",doklad=f"EFS {f}",
            obdobi=x['obdobi'],zdroj_email_id=EMAIL[f],poznamka=f"EURO FLEET SERVIS, půjčovné Škoda {x['model'].replace('Kamig','Kamiq').replace('Karog','Karoq').replace('Kodiag','Kodiaq').rstrip('qg')+'q' if x['model'][:3] in ('Kam','Kar','Kod') else x['model']}; DUZP {duzp}; sken – rozpis z přílohy RAYNET (OCR), měs. nájem {x['mesicni']:.2f} × {x['dny']} dní"))
    chk.append((f,duzp,len(it),round(sum(x['castka'] for x in it),2),ZD[f]))
GEM={'2218':2218,'2216':2216,'2211':2211,'2208':2208,'2204':2204,'2202':2202}
for f in sorted(glob.glob(D+'rawcarn/gcp_*.pdf')):
    eid=re.search(r'gcp_(\d+)',f).group(1)
    m,rs,celk=gparse(f)
    t=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    p=re.search(r'za období od (\d+\. \d+\. \d{4}) do (\d+\. \d+\. \d{4})',t); obd=(p.group(1)+'-'+p.group(2)).replace(' ','')
    k=re.search(r'ke dni (\d+\. \d+\. \d{4})',t).group(1).replace(' ','')
    cnt=collections.Counter(r['ps'] for r in rs); seen=collections.Counter()
    for r in rs:
        seen[r['ps']]+=1
        isvin=len(r['rz'])==17
        note=f"GČP flotila Carnetto, PS vozidla {r['ps']}; POV {r['pov']} / HAV {r['hav']} / připojištění {r['pri']} Kč (pojištění bez DPH)"
        if cnt[r['ps']]>1: note+=f"; {seen[r['ps']]}. řádek stejné PS ve vyúčtování (alikvota/doplatek)"
        if isvin: note+="; vozidlo uvedeno jen VIN (počátek 15.6.2026 – pravděpodobně Karoq 9H03544, půjčovné od 15.6.2026)"
        rows.append(dict(mesic=m,spz='' if isvin else r['rz'],vin=r['rz'] if isvin else '',kategorie='pojisteni',castka_bez_dph=f"{r['tot']:.2f}",
            doklad=f"GČP vyúčtování PS 6287974108 ke dni {k}",obdobi=obd,zdroj_email_id=GEM[eid],poznamka=note))
    chk.append(('GCP '+eid,m,len(rs),sum(r['tot'] for r in rs),celk))
rows.sort(key=lambda r:(r['mesic'],r['kategorie'],r['spz'] or r['vin']))
with open(D+'carnetto.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=['mesic','spz','vin','kategorie','castka_bez_dph','doklad','obdobi','zdroj_email_id','poznamka']); w.writeheader(); w.writerows(rows)
for c in chk: print(*c,'OK' if abs(c[3]-c[4])<0.01 else 'DIFF')
s=collections.defaultdict(float); n=collections.defaultdict(set)
for r in rows: s[(r['mesic'],r['kategorie'])]+=float(r['castka_bez_dph']); n[(r['mesic'],r['kategorie'])].add(r['spz'] or r['vin'])
for k in sorted(s): print(k,round(s[k],2),len(n[k]))
allv=set(r['spz'] or r['vin'] for r in rows); L=set(r['spz'] for r in rows if r['kategorie']=='leasing'); P=set(r['spz'] or r['vin'] for r in rows if r['kategorie']=='pojisteni')
print('vozu celkem',len(allv),'leasing',len(L),'pojisteni',len(P),'jen leasing',sorted(L-P),'jen pojisteni',sorted(P-L))
