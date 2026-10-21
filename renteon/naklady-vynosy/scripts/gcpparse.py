import subprocess,re,glob,sys
def num(s): return int(s.replace(' ','').replace('\xa0',''))
def parse(f):
    t=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    m=re.search(r'za období od (\d+)\. (\d+)\. (\d{4})',t); mesic=f"{m.group(3)}-{int(m.group(2)):02d}"
    rows=[]
    for line in t.splitlines():
        mm=re.match(r'^\s*\d+\.\s+(\d{10})\s+(\S+)\s+(.*)$',line)
        if not mm: continue
        toks=re.split(r'\s{2,}',mm.group(3).strip())
        pov,hav,pri,tot=[num(x) for x in toks[-4:]]
        assert pov+hav+pri==tot,(f,line)
        rows.append(dict(ps=mm.group(1),rz=mm.group(2).upper(),pov=pov,hav=hav,pri=pri,tot=tot))
    c=re.search(r'Celkem za pojistnou smlouvu\s+([\d -]+?)\s{2,}([\d -]+?)\s{2,}([\d -]+?)\s{2,}([\d -]+)',t)
    celk=num(c.group(4).strip())
    return mesic,rows,celk
if __name__=='__main__':
    for f in sorted(glob.glob(sys.argv[1]+'/gcp_*.pdf')):
        mesic,rows,celk=parse(f)
        print(f.split('/')[-1],mesic,len(rows),sum(r['tot'] for r in rows),celk)
