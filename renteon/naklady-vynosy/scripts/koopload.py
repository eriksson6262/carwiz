import openpyxl,glob,sys,warnings,re,pandas as pd
warnings.filterwarnings('ignore')
def load(d):
    out=[]
    for f in sorted(glob.glob(d+'/koop_*_V*.xlsx')):
        m=re.search(r'koop_(\d+)_V(\d+b?)',f); mid,vyk=m.groups()
        ws=openpyxl.load_workbook(f,data_only=True).active
        rows=list(ws.iter_rows(values_only=True)); h=[str(x).replace('\n',' ') for x in rows[0]]
        for r in rows[1:]:
            if not r[0]: continue
            out.append(dict(zip(h,r))|{'email':mid,'vykaz':vyk,'soubor':f.split('/')[-1]})
    df=pd.DataFrame(out)
    df['od']=pd.to_datetime(df['Pojistné období OD'].str.replace(' ',''),format='%d.%m.%Y')
    df['do']=pd.to_datetime(df['Pojistné období DO'].str.replace(' ',''),format='%d.%m.%Y')
    df['rz']=df['Registrační značka'].fillna('').str.replace(' ','').str.upper()
    df['amt']=df['Předepsáno Kč'].astype(float)
    return df
