import sys,re,subprocess
def num(s): return float(s.replace('\xa0','').replace(' ','').replace(',','.'))
def parse_pages(path):
    t=subprocess.run(['pdftotext','-layout',path,'-'],capture_output=True,text=True).stdout
    pages=t.split('\f'); out=[]
    for p in pages:
        if not p.strip(): continue
        m=re.search(r'(?:Variabilní symbol|Evidenční číslo daňového dokladu):\s*(?:VFA)?(\d{8,})',p)
        vs=m.group(1) if m else None
        od=re.search(r'Odběratel\s*\n(?:.*\n){0,2}?\s{20,}(\S.*?)\s*\n',p)
        odb='Carnetto' if 'Carnetto' in p else ('RX Auto' if 'RX Auto' in p or '06044310' in p else '?')
        sup='EURO FLEET SERVIS' if 'EURO FLEET' in p else ('AUTOCENTRUM' if 'AUTOCENTRUM' in p else '?')
        duzp=re.search(r'DUZP[^\n]*?(\d{2}\.\d{2}\.\d{4})',p) or re.search(r'zdaniteln[^\n]*?(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})',p)
        vyst=re.search(r'Datum vystavení[^\n]*?(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})',p)
        z0=re.search(r'ZD 0 %\s+(-?[\d ]+,\d\d)',p); z21=re.search(r'ZD zákl\.sazba\s+(-?[\d ]+,\d\d)',p)
        tot=re.search(r'Celkem k úhradě\s+(-?[\d ]+,\d\d)',p)
        items=[]
        mm=re.search(r'Fakturujeme Vám:?\s*\n(.*?)(Daňová rekapitulace|Rekapitulace)',p,re.S)
        if mm: items=[re.sub(r'\s{2,}',' | ',l.strip()) for l in mm.group(1).splitlines() if l.strip()]
        out.append(dict(vs=vs,odb=odb,sup=sup,duzp=duzp.group(1) if duzp else '',vyst=vyst.group(1) if vyst else '',
          z0=num(z0.group(1)) if z0 else 0,z21=num(z21.group(1)) if z21 else 0,tot=num(tot.group(1)) if tot else None,items=items,
          spz=sorted(set(x.replace(' ','') for x in re.findall(r'\b([0-9][A-Z][A-Z0-9]\s?[A-Z0-9]{4})\b',p)))))
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        for d in parse_pages(f):
            if not d['vs'] and not d['items']: continue
            print(d['vs'],d['odb'],d['sup'],d['duzp'],'z0',d['z0'],'z21',d['z21'],'tot',d['tot'],'|',' / '.join(d['items'])[:120])
