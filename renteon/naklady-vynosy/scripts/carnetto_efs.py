import re,sys,json
D='/tmp/claude-0/-home-claude/56f02949-6ccc-5729-9af0-15621bcf8687/scratchpad/naklady/'
def num(s): return float(s.replace('\xa0','').replace(' ','').replace(',','.'))
def normspz(s):
    s=s.replace(' ','').upper().replace('9HO','9H0')
    s=re.sub(r'^1AR[1\[]','1ARI',s)
    return s
def parse_txt(path):
    L=open(path).read().splitlines(); items=[]; other=[]
    for i,l in enumerate(L):
        if 'Půjčov' not in l: continue
        m=re.search(r'Půjčov né (.*?) / (\S+)\s{2,}1\s+21\s+([\d ]+,\d\d)\s+([\d ]+,\d\d)\s+([\d ]+,\d\d)\s+([\d ]+,\d\d)',l)
        if not m: other.append(l.strip()); continue
        per=m.group(2)
        if per.endswith('-'):
            per+=L[i+1].strip()
        name=m.group(1)
        sm=re.search(r'((?:8H8|9H0|1A[A-Z])\s?[A-Z0-9 ]{4,6})$',name.replace('Octav ia','Octavia '))
        spz=normspz(sm.group(1)) if sm else ''
        model=name.replace('Octav ia','Octavia').split()[1] if len(name.split())>1 else name
        items.append(dict(spz=spz,model=model,obdobi=per,castka=num(m.group(5)),raw=name))
    t=open(path).read()
    zd=num(re.search(r'ZD zákl\.sazba\s+(-?[\d ]+,\d\d)',t).group(1))
    duzp=re.search(r'DUZP[^\n]*?(\d{2}\.\d{2}\.\d{4})',t).group(1)
    return items,other,zd,duzp
def parse_ocr(paths,mesic):
    items=[]
    for p in paths:
        for l in open(p):
            m=re.match(r'^(\S+)\s+((?:8H8|9H[O0]|1AR)\s+\S{4})\s+(\d+)/(\d+)/(\d{4})\s+(\d+)/(\d+)/(\d{4})\s+Ca\w+ RX s\.r\.o\.\s+([\d,]+\.\d\d)\s+\S+\s+(\d+)\s+([\d,]+\.\d\d)',l.strip())
            if m:
                g=m.groups()
                items.append(dict(spz=normspz(g[1]),model=g[0],obdobi=f"{int(g[3])}.{int(g[2])}.{g[4]}-{int(g[6])}.{int(g[5])}.{g[7]}",castka=float(g[10].replace(',','')),mesicni=float(g[8].replace(',','')),dny=int(g[9])))
            elif re.search(r'(8H8|9H[O0]|1AR)\s',l): print('UNPARSED',p,l.strip())
    return items
