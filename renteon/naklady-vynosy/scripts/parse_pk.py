import sys, os, re, glob, subprocess, json
D=sys.argv[1]
TR='/root/.claude/projects/-home-claude/56f02949-6ccc-5729-9af0-15621bcf8687/tool-results'
marker=os.path.getmtime(os.path.join(D,'marker'))
files=[f for f in glob.glob(TR+'/mcp-remote-devices-blob-*.pdf') if os.path.getmtime(f)>=marker-1 or f.endswith('wdm786.pdf')]
num=r'-?\d{1,3}(?:[  ]\d{3})*,\d{2}'
rowre=re.compile(r'^\s*(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d+)\s+('+num+r')\s+('+num+r')\s+('+num+r')\s+('+num+r')\s*$')
def n(s): return float(s.replace(' ','').replace(' ','').replace(',','.'))
out={}
for f in sorted(files):
    t=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    m=re.search(r'daňový doklad č\.\s*(\d{7})',t)
    if not m or 'Platební kalendář' not in t: continue
    c=m.group(1)
    rz=re.search(r'RZ:\s*([0-9A-Z ]+?)\s{2,}',t) or re.search(r'RZ:\s*(\S+)',t)
    st=re.search(r'Středisko:\s*(\S+)',t)
    end=re.search(r'Datum ukončení smlouvy[^:]*:\s*(\d{1,2}\.\d{1,2}\.\d{4})',t)
    vyst=re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})\s+Datum převzetí',t)
    rows=[]; bad=[]; seen=set()
    for line in t.splitlines():
        mm=rowre.match(line)
        if mm:
            k=(mm.group(1),mm.group(2),mm.group(4),mm.group(6))
            if k in seen: continue
            seen.add(k)
            rows.append(dict(duzp=mm.group(1),splat=mm.group(2),ks=int(mm.group(3)),zaklad=n(mm.group(4)),dph=n(mm.group(5)),nul=n(mm.group(6)),celkem=n(mm.group(7))))
        elif re.match(r'^\s*\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}\.\d{1,2}\.\d{4}',line): bad.append(line)
    tot=re.search(r'Uživatel uhradí splátky celkem:\s*('+num+')',t)
    open(os.path.join(D,'txt',c+'.txt'),'w').write(t)
    out[c]=dict(file=os.path.basename(f),rz=rz.group(1).replace(' ','').upper() if rz else None,stredisko=st.group(1) if st else None,konec=end.group(1) if end else None,vystaveni=vyst.group(1) if vyst else None,rows=rows,bad=bad,total=n(tot.group(1)) if tot else None)
json.dump(out,open(os.path.join(D,'pk_parsed.json'),'w'),ensure_ascii=False,indent=1)
# checks
for c,v in sorted(out.items()):
    s=round(sum(r['celkem'] for r in v['rows']),2)
    flag='' if v['total'] is not None and abs(s-v['total'])<0.05 else ' MISMATCH total=%s sum=%s'%(v['total'],s)
    if flag or v['bad'] or not v['rz'] or not v['rows']: print(c,v['rz'],v['stredisko'],len(v['rows']),flag,v['bad'][:2])
print('parsed',len(out))
