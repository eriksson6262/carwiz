import csv, collections, re
W0,W1='2025-09','2026-10'
EUR=24.3
inW=lambda m: W0<=m<=W1
norm=lambda s: re.sub(r'^(\d[A-Z])O(\d)',r'\g<1>0\2',(s or '').replace(' ','').upper())
# --- branch maps
cz={}
for r in csv.DictReader(open('renteon_mapa_aut.csv'),delimiter=';'):
    runs=[x.split('=') for x in r['pobocky'].split(',') if '=' in x]
    cz[norm(r['spz'])]={'model':r['model'],'sipp':r['sipp'],'runs':runs,'od':r['od'],'do':r['do']}
sk=set(norm(x) for x in open('sk_auta.txt').read().split())
czrev=set(); skrev=set()
for r in csv.DictReader(open('renteon_auta.csv'),delimiter=';'): czrev.add((r['mesic'],norm(r['spz'])))
for r in csv.DictReader(open('renteon_sk_auta.csv'),delimiter=';'): skrev.add((r['mesic'],norm(r['spz'])))
def branch(s,m):
    if s in sk and not ((m,s) in czrev and (m,s) not in skrev): return 'BTS'
    c=cz.get(s)
    if c and c['od']<=m<=c['do']:
        o=c['runs'][0][1]
        for a,b in c['runs']:
            if a<=m: o=b
        return {'P':'PRG','O':'OSR'}.get(o,'PRG')
    if s in sk: return 'BTS'
    if c:  # mimo aktivní období v Renteonu – vezmi poslední známou pobočku
        o=c['runs'][-1][1] if m>c['do'] else c['runs'][0][1]
        return {'P':'PRG','O':'OSR'}.get(o,'PRG')
    return 'PRG'
# --- costs per (m, spz, cat)
cost=collections.defaultdict(float); src_rows=[]
def addc(m,s,cat,v,seg=None):
    if not inW(m): return
    s=norm(s); b=seg or (branch(s,m) if s and s!='FLOTILA' else 'PRG')
    cost[(m,b,s,cat)]+=v
for fn,est in [('leasing.csv',False),('leasing_odhad_bez_pk.csv',True)]:
    for r in csv.DictReader(open(fn)):
        zf='zpětná' in r['typ']
        cat=('leasing_odhad' if est else 'leasing')
        addc(r['mesic'],r['spz'],cat,float(r['castka_bez_dph']),'HAVEX_ZF' if zf else None)
for r in csv.DictReader(open('pojisteni.csv')):
    if 'Carnetto' in (r['poznamka'] or '') : continue
    addc(r['mesic'],r['spz'],'pojisteni',float(r['castka']))
catmap={'oprava':'opravy','servis':'servis','pneu':'servis','myti':'ostatni','stk_znamky':'ostatni','ostatni':'ostatni'}
for r in csv.DictReader(open('servis.csv')):
    if r['kategorie']=='pokuty': continue
    addc(r['mesic'],r['spz'],catmap.get(r['kategorie'],'ostatni'),float(r['castka_bez_dph']))
# --- Carnetto RX: náklady přefakturované na RX Auto (EFS půjčovné, pojištění flotily ČGP 6287974108)
import os
unalloc=collections.defaultdict(float)
if os.path.exists('carnetto.csv'):
    for r in csv.DictReader(open('carnetto.csv')):
        cat='carnetto_leasing' if r['kategorie']=='leasing' else 'carnetto_pojisteni'
        if norm(r['spz']): addc(r['mesic'],r['spz'],cat,float(r['castka_bez_dph']))
        elif inW(r['mesic']): unalloc[(r['mesic'],cat)]+=float(r['castka_bez_dph'])
# --- revenue per car
rev=collections.defaultdict(float)
for r in csv.DictReader(open('renteon_auta.csv'),delimiter=';'):
    m=r['mesic']
    if inW(m): s=norm(r['spz']); rev[(m,branch(s,m) if (m,s) not in czrev or s not in sk else ('BTS' if (m,s) in skrev else branch(s,m)),s,'renteon')]+=float(r['total'])
for r in csv.DictReader(open('renteon_sk_auta.csv'),delimiter=';'):
    m=r['mesic']
    if inW(m): rev[(m,'BTS',norm(r['spz']),'renteon')]+=float(r['total'])*EUR
for r in csv.DictReader(open('vyfakturuj_auta.csv'),delimiter=';'):
    m=r['mesic']
    if not inW(m) or r['druh']!='najem': continue
    s=r['spz']
    if s=='GA': rev[(m,'OSR','GLOBAL ASSISTANCE','vyfakturuj')]+=float(r['castka']); continue
    s=norm(s); b=branch(s,m) if s else 'PRG'
    rev[(m,b,s or '(bez SPZ)','vyfakturuj')]+=float(r['castka'])
for r in csv.DictReader(open('havex_vynos_auta.csv'),delimiter=';'):
    m=r['mesic']
    if inW(m): rev[(m,'HAVEX_ZF',norm(r['spz']) or '(bez SPZ)','havex')]+=float(r['castka'])
# položky Carnetto bez SPZ: rozpočet rovným dílem na vozy s výnosem a bez leasingu v daném měsíci
haslease={(m,s) for (m,b,s,c) in cost if c.startswith('leasing') or c=='carnetto_leasing'}
for (m,cat),v in unalloc.items():
    tgt=sorted({(b,s) for (mm,b,s,t) in rev if mm==m and t!='havex' and s not in ('GLOBAL ASSISTANCE','(bez SPZ)') and (m,s) not in haslease})
    for b,s in tgt: cost[(m,b,s,cat)]+=v/len(tgt)
    if not tgt: cost[(m,'PRG','',cat)]+=v
# --- branch revenue from official monthly dataset (Renteon bez pokut + VF), SK EUR->CZK
brev={}
for r in csv.DictReader(open('../vynosy/vynosy_flotila_v5.csv')):
    m=r['mesic']
    if not inW(m): continue
    k=EUR if r['pobocka']=='BTS' else 1
    brev[(m,r['pobocka'])]=(float(r['vynos_renteon'])*k, float(r['vf_celkem'])*k, float(r['vozidel']))
hv=collections.defaultdict(float)
for (m,b,s,t),v in rev.items():
    if t=='havex': hv[m]+=v
months=sorted({m for m,_ in brev})
CATS=['leasing','leasing_odhad','carnetto_leasing','pojisteni','carnetto_pojisteni','servis','opravy','ostatni']
out=[]
for m in months:
    for b in ['PRG','OSR','BTS','HAVEX_ZF']:
        c={k:0.0 for k in CATS}
        for (mm,bb,s,cat),v in cost.items():
            if mm==m and bb==b: c[cat]+=v
        if b=='HAVEX_ZF': ren,vf,voz=0,hv[m],0
        else: ren,vf,voz=brev[(m,b)]
        nak=sum(c.values()); vyn=ren+vf
        out.append(dict(mesic=m,pobocka=b,vynos_renteon=round(ren),vynos_vyfakturuj=round(vf),vynos_celkem=round(vyn),
            **{k:round(c[k]) for k in CATS},naklady_celkem=round(nak),vysledek=round(vyn-nak),vozidel=round(voz,1)))
w=csv.DictWriter(open('pl_pobocky.csv','w'),fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
# per car
cars=collections.defaultdict(lambda:collections.defaultdict(float)); cb=collections.defaultdict(collections.Counter)
for (m,b,s,cat),v in cost.items(): cars[s][cat]+=v; cb[s][b]+=1
for (m,b,s,t),v in rev.items(): cars[s]['v_'+t]+=v; cb[s][b]+=1
rows=[]
for s,d in cars.items():
    if not s: s2='(bez SPZ)'
    vyn=d['v_renteon']+d['v_vyfakturuj']+d['v_havex']; nak=sum(d[k] for k in CATS)
    info=cz.get(s,{})
    rows.append(dict(spz=s or '(bez SPZ)',model=info.get('model','') ,sipp=info.get('sipp',''),pobocka=cb[s].most_common(1)[0][0],
        vynos_renteon=round(d['v_renteon']),vynos_vyfakturuj=round(d['v_vyfakturuj']),vynos_havex=round(d['v_havex']),vynos_celkem=round(vyn),
        leasing=round(d['leasing']+d['leasing_odhad']+d['carnetto_leasing']),leasing_odhad=round(d['leasing_odhad']),carnetto=round(d['carnetto_leasing']+d['carnetto_pojisteni']),pojisteni=round(d['pojisteni']+d['carnetto_pojisteni']),servis_opravy=round(d['servis']+d['opravy']+d['ostatni']),
        naklady_celkem=round(nak),vysledek=round(vyn-nak),
        poznamka=('Carnetto RX (EFS půjčovné / ČGP)' if d['carnetto_leasing']+d['carnetto_pojisteni'] else ('bez leasingu v datech' if vyn>0 and not d['leasing']+d['leasing_odhad'] and s not in ('GLOBAL ASSISTANCE','') else ''))))
rows.sort(key=lambda r:r['vysledek'])
w=csv.DictWriter(open('pl_auta.csv','w'),fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
# summary
T=collections.defaultdict(lambda:collections.defaultdict(float))
for r in out:
    for k in ['vynos_celkem','naklady_celkem','vysledek']+CATS: T[r['pobocka']][k]+=r[k]
for b,d in T.items(): print(b,{k:round(v/1e6,2) for k,v in d.items()})
print('aut',len(rows),'ztratovych',sum(1 for r in rows if r['vysledek']<0 and r['spz']!='(bez SPZ)'))
# Carnetto měsíční souhrn
cm=collections.defaultdict(lambda:{'pujcovne':0.0,'pojisteni':0.0,'v1':set(),'v2':set()})
for r in csv.DictReader(open('carnetto.csv')):
    x=cm[r['mesic']]; v=float(r['castka_bez_dph'])
    if r['kategorie']=='leasing': x['pujcovne']+=v; x['v1'].add(r['spz'] or r['vin'])
    else: x['pojisteni']+=v; x['v2'].add(r['spz'] or r['vin'])
w=csv.writer(open('carnetto_mesice.csv','w')); w.writerow(['mesic','pujcovne','pojisteni','celkem','vozu_pujcovne','vozu_pojisteni'])
for m in sorted(cm): x=cm[m]; w.writerow([m,round(x['pujcovne'],2),round(x['pojisteni'],2),round(x['pujcovne']+x['pojisteni'],2),len(x['v1']),len(x['v2'])])
