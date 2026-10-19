import json,glob,re,sys,os
D=os.environ.get('TR','/root/.claude/projects/-home-claude/e21c81fd-935d-5522-91a8-a1d53743c037/tool-results/')
PFX=sys.argv[1]; OUTF=sys.argv[2]
dec=json.JSONDecoder(); parts={}
for f in sorted(glob.glob(D+'*.txt')):
    try: t=json.load(open(f))[0]['text']
    except Exception: continue
    try: s,_=dec.raw_decode(t)
    except Exception: continue
    if not isinstance(s,str): continue
    m=re.match(re.escape(PFX)+r'P(\d+)/(\d+)#',s)
    if not m or '#END' not in s: continue
    parts[int(m[1])]=(int(m[2]),s[m.end():s.rindex('#END')])
n=next(iter(parts.values()))[0]; assert sorted(parts)==list(range(1,n+1)),sorted(parts)
txt=''.join(parts[i][1] for i in range(1,n+1)); json.dump(json.loads(txt),open(OUTF,'w')); print('ok',len(txt))
