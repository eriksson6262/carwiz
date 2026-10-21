"""Pojisteni flotily RX Auto za 2024 (+ GCP/D.A.S. 2025 pred zacatkem pojisteni.csv).
Vystup: pojisteni_2024.csv (stejne sloupce jako pojisteni.csv, bez radku uz v pojisteni.csv dle pojistovna+smlouva+mesic+spz)
        pojisteni_2025-01_koop_v55.csv (Kooperativa 2025-01 z vykazu 55, ktery v pojisteni.csv chybi - k rucnimu posouzeni)
Zdroje (raw2024/, raw/):
  Kooperativa inkasni skupina 6667100466: koop_<emailid>_V<vykaz>.xlsx (DETAIL_PREDPIS), mesic = mesic zacatku poj. obdobi (20.-19.)
  Generali CP RS 4785635732: gcp_<emailid>.pdf (Vyuctovani plateb, mesicni) -> parse gcpparse.py
  D.A.S. PS 4111639: odvozeno (ctvrtletni predpis 1300 Kc/vuz, 2 vozy), predpisy pred 11/2025 v poste nejsou
Pouziti: python3 scripts/pojisteni_2024.py <pracovni slozka naklady>
"""
import sys,os,glob,re,warnings,openpyxl,pandas as pd
warnings.filterwarnings('ignore')
BASE=sys.argv[1] if len(sys.argv)>1 else '.'
sys.path.insert(0,os.path.join(BASE,'scripts'))
import gcpparse
COLS=['mesic','spz','castka','pojistovna','smlouva','druh','zdroj_email_id','soubor','poznamka']

# ---------- Kooperativa ----------
def koop_load(dirs):
    out=[];seen=set()
    for d in dirs:
        for f in sorted(glob.glob(d+'/koop_*_V*.xlsx')):
            mid,vyk=re.search(r'koop_(\d+)_V(\d+b?)',f).groups()
            if vyk in seen: continue
            seen.add(vyk)
            rows=list(openpyxl.load_workbook(f,data_only=True).active.iter_rows(values_only=True))
            h=[str(x).replace('\n',' ') for x in rows[0]]
            for r in rows[1:]:
                if r[0]: out.append(dict(zip(h,r))|{'email':mid,'vykaz':vyk})
    df=pd.DataFrame(out)
    df['od']=pd.to_datetime(df['Pojistné období OD'].str.replace(' ',''),format='%d.%m.%Y')
    df['do']=pd.to_datetime(df['Pojistné období DO'].str.replace(' ',''),format='%d.%m.%Y')
    df['rz']=df['Registrační značka'].fillna('').str.replace(' ','').str.upper()
    df['amt']=df['Předepsáno Kč'].astype(float)
    df['mesic']=df.od.dt.strftime('%Y-%m')
    df['druh']=df['Kód pojistného produktu'].map({'KPH':'HAV','KPO':'POV'}).fillna('jine')
    df['vykaz_n']=df.vykaz.str.extract(r'(\d+)')[0].astype(int)
    df['key']=df.rz.where(df.rz!='','VIN:'+df.VIN.fillna(''))
    return df
def koop_rows(df):
    """Stejna logika jako u pojisteni.csv (overeno na 2025-02/03/06: shodne pocty i soucty)."""
    res=[]
    for (m,key,druh),g in df.sort_values(['vykaz_n','od']).groupby(['mesic','key','druh'],sort=True):
        rz=g.rz.iloc[0]; ps=','.join(dict.fromkeys(g['Číslo PS'].astype(str)))
        per=list(dict.fromkeys(f"{r.od:%d.%m.}-{r.do:%d.%m.%Y}" for r in g.itertuples()))
        neg=g.loc[g.amt<0,'amt'].sum()
        prov=g['Provozovatel název'].dropna().iloc[0] if g['Provozovatel název'].notna().any() else ''
        parts=['obdobi '+', '.join(per)]
        if neg<0: parts.append(f'vc. storna/vratky {neg:.0f} Kc')
        parts.append(f'provozovatel {prov}')
        if not rz: parts.append(f"bez RZ, VIN {g.VIN.iloc[0]}")
        parts.append(f'PS {ps}')
        res.append(dict(mesic=m,spz=rz,castka=float(g.amt.sum()),pojistovna='Kooperativa',smlouva='inkasni skupina 6667100466',druh=druh,
            zdroj_email_id=';'.join(dict.fromkeys(g.email)),
            soubor=';'.join(f'DETAIL_PREDPIS_6667100466_VYKAZ_{v}.xlsx' for v in dict.fromkeys(g.vykaz)),poznamka='; '.join(parts)))
    return pd.DataFrame(res,columns=COLS)

# ---------- Generali CP ----------
def gcp_rows(files):
    res=[]
    for f in files:
        mid=re.search(r'gcp_(\d+)',f).group(1)
        mesic,rows,celk=gcpparse.parse(f)
        assert sum(r['tot'] for r in rows)==celk,(f,celk)
        for r in rows:
            vr='; obsahuje vratku' if r['tot']<0 or min(r['pov'],r['hav'],r['pri'])<0 else ''
            for druh,k,pref in (('HAV','hav',''),('POV','pov',''),('jine','pri','pripojisteni (doplnky) ')):
                if r[k]==0: continue
                res.append(dict(mesic=mesic,spz=r['rz'],castka=float(r[k]),pojistovna='Generali CP',smlouva='RS 4785635732',druh=druh,
                    zdroj_email_id=mid,soubor='Vyuctovani plateb k pojistne smlouve 4785635732.pdf',
                    poznamka=f"{pref}vyuctovani za {mesic}; podsmlouva {r['ps']}{vr}"))
    return pd.DataFrame(res,columns=COLS)

# ---------- D.A.S. ----------
def das_rows():
    res=[]
    for q in (['2025-05','2025-06','2025-07'],['2025-08','2025-09','2025-10']):
        for i,m in enumerate(q):
            for spz in ('1AFK853','1AHL028'):
                res.append(dict(mesic=m,spz=spz,castka=433.34 if i==2 else 433.33,pojistovna='D.A.S. (Generali CP)',smlouva='PS 4111639',druh='jine',
                    zdroj_email_id='1014',soubor='',poznamka=f"pravni ochrana vozidla+ridice; ctvrtletni pojistne 1300 Kc/vuz rozpocteno na mesice ({q[0]} az {q[-1]}); "
                    "ODVOZENO - predpis v poste neni: smlouva sjednana 04/2025 (e-mail M. Vajgl 17.4.2025, prvni platba 2600 Kc), ctvrtleti 1.5./1.8./1.11./1.2. dle pozdejsich predpisu"))
    return pd.DataFrame(res,columns=COLS)

if __name__=='__main__':
    raw=os.path.join(BASE,'raw'); raw24=os.path.join(BASE,'raw2024')
    kdf=koop_load([raw,raw24])
    koop=koop_rows(kdf[kdf.mesic.str[:4]=='2024'])
    koop_v55=koop_rows(kdf[(kdf.mesic=='2025-01')&(kdf.vykaz=='55')])
    gcp=gcp_rows(sorted(glob.glob(raw24+'/gcp_*.pdf')))
    gcp=gcp[(gcp.mesic.str[:4]=='2024')|((gcp.mesic>='2025-01')&(gcp.mesic<'2025-07'))]
    out=pd.concat([koop,gcp,das_rows()],ignore_index=True)
    ex=pd.read_csv(os.path.join(BASE,'pojisteni.csv'),dtype=str,keep_default_na=False)
    exk=set(zip(ex.pojistovna,ex.smlouva,ex.mesic,ex.spz))
    dup=[(r.pojistovna,r.smlouva,r.mesic,r.spz) in exk for r in out.itertuples()]
    print('vyrazeno (uz v pojisteni.csv):',sum(dup))
    out=out[[not d for d in dup]].sort_values(['pojistovna','mesic','spz','druh'],kind='stable')
    out.to_csv(os.path.join(BASE,'pojisteni_2024.csv'),index=False,columns=COLS)
    koop_v55.to_csv(os.path.join(BASE,'pojisteni_2025-01_koop_v55.csv'),index=False,columns=COLS)
    print(out.groupby(['mesic','pojistovna']).castka.sum().unstack().round(0).to_string())
    print('vozu (SPZ) celkem:',out[out.spz!=''].spz.nunique(),'| po mesicich:',out[out.spz!=''].groupby('mesic').spz.nunique().to_dict())
    print('Koop 2025-01 z V55 (mimo pojisteni.csv):',koop_v55.castka.sum(),len(koop_v55))
