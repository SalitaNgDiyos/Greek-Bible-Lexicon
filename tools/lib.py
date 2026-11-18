import sys,pickle,sqlite3,zlib,re,collections,shutil,csv,unicodedata
sys.path.insert(0,'py'); import conv; from conv import parse,emit,esc
from rtf import rtf_text
OUT=sys.argv[1]; CSVF=sys.argv[2]
_a=open('py/analyze2.py').read()
exec(_a[_a.index('def k1'):_a.index('I1=')]); exec(_a[_a.index('LABELS='):_a.index('def sig')])
src='epv/epv-thayer-kjv_2026-10-30_v3.dct.twm'

R=pickle.load(open('rows.pkl','rb')); E=pickle.load(open('epv.pkl','rb'))
l=sqlite3.connect('file:in/Liddell.dct.twm?mode=ro',uri=True); l.text_factory=bytes
LS=collections.defaultdict(list); LT={}
for tid,s,d in l.execute("select t.id,t.subject,c.data from topics t join content c on c.topic_id=t.id"):
    x=zlib.decompress(d).decode('latin1'); s=s.decode()
    LS[s].append(tid); LT[tid]=(s,x)
e=sqlite3.connect(OUT); e.text_factory=bytes
EP={};META={}
for tid,sb in e.execute("select id,subject from topics"): EP.setdefault(sb.decode(),tid)
for tid,d in e.execute("select t.id,c.data from topics t join content c on c.topic_id=t.id where t.content_type='meta'"):
    m=re.search(rb'id=(\d+)',d); META[tid]=int(m.group(1))
for k in EP: EP[k]=META.get(EP[k],EP[k])
for tid,(s,x) in LT.items():
    if s in EP: conv.SELF[tid]='tw://[self]?tid=%d'%EP[s]
STOP=set('a an the of to in on for with by from and or as at be is are was were it its that this which who not no any one into upon also used etc esp sts c gen dat acc pl sg i ii iii'.split())
def words(t): return set(w for w in re.findall(r'[a-z]{3,}',t.lower()) if w not in STOP)
def glosses(x):
    out=[]
    for li,runs in parse(x):
        for t,g,it,b,lk in runs:
            if it and not g: out.append(t)
    return ' '.join(out)
def plain(x): return rtf_text('\n'.join(emit(parse(x))).encode('latin1'))
SEC=['Thayer Definition','Definition','BDB Definition']
def choose(r):
    tids=[t for c in r['cands'] for t in LS.get(c,[])]
    tids=list(dict.fromkeys(tids))
    if len(tids)==1: return tids[0],[],''
    S=sections(E[r['g']][1]); mine=words(' '.join(S.get(k,'') for k in SEC))
    sc=[]
    for t in tids:
        x=LT[t][1]; gl=words(glosses(x)); al=words(plain(x)[:4000])
        sc.append((len(mine&gl)*3+len(mine&al)*0.2, -abs(len(plain(x))-0), t))
    sc.sort(reverse=True)
    note='several LSJ homographs: chose by meaning match (%s); others: %s'%(LT[sc[0][2]][0],', '.join(LT[t][0] for _,_,t in sc[1:]))
    if sc[0][0]==sc[1][0]: note='several LSJ homographs, no clear meaning match – PLEASE CHECK; chose '+LT[sc[0][2]][0]+'; others: '+', '.join(LT[t][0] for _,_,t in sc[1:])
    return sc[0][2],[t for _,_,t in sc[1:]],note
def follow(t):
    x=LT[t][1]
    if len(plain(x))<300:
        m=re.search(r'HYPERLINK "tw://\[self\]\?tid=(\d+)"',x)
        if m and int(m.group(1)) in LT and int(m.group(1))!=t: return int(m.group(1))
    return None
HEAD='\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b LSJ Definition:}\\par'
STOPSEC=re.compile(r'^\\pard\\sb0\\sa120\\li0\\fi0 \{\\plain\\f0\\fs20\\b (Related Word|TDNT|NT Occurrences|OT \(LXX\) Occurrences|Hebrew|English Name|Pronunciation):')
def insert(g,lines):
    tid=E[g][0]
    d=e.execute("select data from content where topic_id=?",(tid,)).fetchone()[0].decode('latin1')
    L=d.split('\n'); k=next((j for j,x in enumerate(L) if STOPSEC.match(x)),None)
    if k is None: k=len(L)-1 if L[-1].strip()=='}' else len(L)
    L[k:k]=[HEAD]+lines
    nd='\n'.join(L)
    e.execute("update content set data=? where topic_id=?",(nd.encode('latin1'),tid))
    row=e.execute("select data from content_search where topic_id=?",(tid,)).fetchone()
    add=['LSJ Definition:']+[rtf_text(x.encode('latin1')) for x in lines]
    if row:
        S_=row[0].decode('utf-16-le').split('\r\n')
        j=next((i for i,x in enumerate(S_) if re.match(r'(Related Word|TDNT|NT Occurrences|OT \(LXX\) Occurrences|Hebrew|English Name|Pronunciation):',x)),len(S_))
        S_[j:j]=add
        e.execute("update content_search set data=? where topic_id=?",('\r\n'.join(S_).encode('utf-16-le'),tid))
    else: MISS.append(tid)
    return tid
# lemma -> G for form-of links
def h2(g):
    ls=E[g][1].split('\n')
    h=ls[1] if ls[0].startswith('Form of') and len(ls)>1 else ls[0]
    return re.split(r' \(',h)[0].split(' / ')[0].strip()
LEM={}
for r in R:
    if r['form_of'] and k2(h2(r['g']))==k2(r['lemma']): LEM.setdefault(k1(r['lemma']),r['g'])
for r in R: LEM.setdefault(k1(h2(r['g'])),r['g'])
LEM2={}
for k_,g_ in LEM.items(): LEM2.setdefault(k2(k_),g_)
def grp(r):
    v=r['how'].split(':',1)[-1] if r['how'].startswith('variant') else ''
    a=k2(r['lemma'])
    if r['form_of']: return '6 Form of'
    if 'γιγν' in v: return '4 γιν→γιγν'
    if a.endswith('ομαι') and v.endswith('ω'): return '1 middle→active'
    if a.endswith('ω') and v.endswith('ομαι'): return '2 active→middle'
    if v.endswith('μι'): return '5 -ω→-μι'
    if a.endswith('ον'): return '3 neuter→adjective'
    return '7 other variant'
