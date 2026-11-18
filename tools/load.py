import sys,sqlite3,zlib,re,pickle,unicodedata
sys.path.insert(0,'.')
from rtf import rtf_text
W=sys.argv[1]
c=sqlite3.connect('file:'+W+'/in/Liddell.dct.twm?mode=ro',uri=True); c.text_factory=bytes
L={}
for tid,s,d in c.execute("select t.id,t.subject,c.data from topics t join content c on c.topic_id=t.id"):
    try: d=zlib.decompress(d)
    except Exception:
        try: d=zlib.decompress(d,-15)
        except Exception: pass
    L[tid]=(s.decode('utf-8','replace'),rtf_text(d),len(d))
pickle.dump(L,open(W+'/lsj.pkl','wb'))
e=sqlite3.connect('file:'+W+'/epv/epv-thayer-kjv_2026-10-30_v3.dct.twm?mode=ro',uri=True); e.text_factory=bytes
E={}
for tid,s,d in e.execute("select t.id,t.subject,c.data from topics t join content c on c.topic_id=t.id"):
    s=s.decode('utf-8','replace')
    if re.fullmatch(r'G\d+',s): E[s]=(tid,rtf_text(d))
pickle.dump(E,open(W+'/epv.pkl','wb'))
print(len(L),len(E))
