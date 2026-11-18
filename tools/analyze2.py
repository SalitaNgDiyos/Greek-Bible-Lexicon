import sys,pickle,re,unicodedata,collections,difflib
W=sys.argv[1]
L=pickle.load(open(W+'/lsj.pkl','rb')); E=pickle.load(open(W+'/epv.pkl','rb'))
def k1(s):
    s=unicodedata.normalize('NFD',s.strip())
    s=''.join(ch for ch in s if ch not in '̄̆^_')
    s=re.sub(r'[\d\s,.]+$','',s)
    s=s.replace('B','β') if re.match(r'^B',s) else s
    return unicodedata.normalize('NFC',s).replace('ς','σ').lower()
def k2(s):
    s=unicodedata.normalize('NFD',k1(s))
    return ''.join(ch for ch in s if not unicodedata.combining(ch))
I1=collections.defaultdict(list); I2=collections.defaultdict(list)
for tid,(s,t,n) in L.items():
    I1[k1(s)].append(tid); I2[k2(s)].append(tid)
LABELS=['Part of Speech','Thayer Definition','LSJ Definition','Definition','Related Word','TDNT','NT Occurrences','OT (LXX) Occurrences','BDB Definition','Hebrew','English Name','Pronunciation']
labre=re.compile(r'^(%s):'%'|'.join(re.escape(x) for x in LABELS),re.M)
def sections(t):
    out={}; ms=list(labre.finditer(t))
    for i,m in enumerate(ms):
        out.setdefault(m.group(1),t[m.end():ms[i+1].start() if i+1<len(ms) else len(t)].strip())
    return out
def sig(t):
    t=re.sub(r'HYPERLINK "[^"]*"','',t)
    return re.sub(r'[\W_]+','',unicodedata.normalize('NFC',t)).lower()
def variants(w):
    out=[]
    a=k2(w)
    subs=[('γινωσκ','γιγνωσκ'),('γινομ','γιγνομ'),('γεινωσκ','γιγνωσκ')]
    for x,y in subs:
        if x in a: out.append(a.replace(x,y))
    for x,y in [('ομαι','ω'),('ω','ομαι'),('υω','υμι'),('αω','ημι'),('εω','ημι'),('οω','ωμι'),('ως','ος'),('ως','ης'),('ως','υς'),('εως','υς'),('ον','ος'),('ως','ων'),('οτερον','ος'),('οτερος','ος'),('οτατος','ος'),('εστερος','ης'),('εστατος','ης'),('ιζω','ω')]:
        if a.endswith(x): out.append(a[:-len(x)]+y)
    return out
rows=[]
for g,(tid,t) in sorted(E.items(),key=lambda x:int(x[0][1:])):
    head=t.split('\n',1)[0]; lem=re.split(r' \(',head)[0].strip()
    S=sections(t)
    pos=S.get('Part of Speech','')
    m=re.match(r'Form of (\S+)',lem)
    how='exact'
    if m: lem=m.group(1); how='form-of'
    lem=lem.split(' / ')[0].strip()
    cands=I1.get(k1(lem)) or I2.get(k2(lem)) or []
    if not cands:
        how='variant'
        for v in variants(lem):
            cands=I1.get(k1(v)) or I2.get(k2(v)) or []
            if cands: how='variant:'+v; break
    if not cands: how='none'
    has='LSJ Definition' in S
    best=None;ratio=None
    if cands:
        es=sig(S.get('LSJ Definition','')) if has else ''
        sc=[]
        for c in cands:
            ls=sig(L[c][1]); 
            if has:
                # how much of the LSJ entry is present in our section
                sm=difflib.SequenceMatcher(None,es,ls,autojunk=False) if len(ls)<20000 else None
                cov=(sum(b.size for b in sm.get_matching_blocks())/max(1,len(ls))) if sm else len(es)/max(1,len(ls))
            else: cov=0
            sc.append((cov,len(ls),c))
        sc.sort(reverse=True); best=sc[0][2]; ratio=sc[0][0]
    rows.append(dict(g=g,lemma=lem,pos=pos,has=has,lsj_len=len(S.get('LSJ Definition','')),
        thayer='Thayer Definition' in S, other=('Definition' in S) or ('BDB Definition' in S),
        cands=[L[c][0] for c in cands], best=L[best][0] if best else None, best_len=len(L[best][1]) if best else 0, cov=ratio,
        proper='proper' in pos.lower() or (lem[:1].isupper()), how=how, form_of=t.split('\n',1)[0].startswith('Form of')))
pickle.dump(rows,open(W+'/rows.pkl','wb'))
C=collections.Counter()
for r in rows:
    if r['has']:
        C['has LSJ: full (>=95%)' if r['cov'] is not None and r['cov']>=0.95 else ('has LSJ: partial' if r['cov'] is not None else 'has LSJ: no LSJ headword match')]+=1
    else:
        C[('no LSJ, LSJ entry exists' if r['cands'] else 'no LSJ, not in LSJ')+(' (proper name)' if r['proper'] else '')]+=1
for k,v in sorted(C.items()): print(v,k)
