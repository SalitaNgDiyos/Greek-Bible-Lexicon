import sys
sys.argv=['x',sys.argv[1],'/dev/null']
exec(open('py/lib.py').read())
R2={r['g']:r for r in R}
REPL=['G145','G179','G2036','G5548','G5628','G5665','G5666','G5673','G5844','G5893','G5921','G5991','G5999','G6012','G6112','G6175','G8622','G13107','G13148']
REMOVE=['G2136','G9475']
LBL=re.compile(r'^(Related Word|TDNT|NT Occurrences|OT \(LXX\) Occurrences|Hebrew|English Name|Pronunciation|BDB Definition|Definition|Thayer Definition):')
out=[]
def replace(g,lines):
    tid=E[g][0]
    d=e.execute("select data from content where topic_id=?",(tid,)).fetchone()[0].decode('latin1').split('\n')
    a=next(j for j,x in enumerate(d) if x==HEAD)
    b=next((j for j in range(a+1,len(d)) if re.match(r'^\\pard\\sb0\\sa120\\li0\\fi0 \{\\plain\\f0\\fs20\\b [^}]*:',d[j])),len(d)-1)
    old=d[a:b]
    d[a:b]=([HEAD]+lines) if lines is not None else []
    nd='\n'.join(d).encode('latin1')
    e.execute("update content set data=? where topic_id=?",(nd,tid))
    S_=e.execute("select data from content_search where topic_id=?",(tid,)).fetchone()[0].decode('utf-16-le').split('\r\n')
    a2=next(j for j,x in enumerate(S_) if x.endswith('LSJ Definition:'))
    b2=next((j for j in range(a2+1,len(S_)) if LBL.match(S_[j])),len(S_))
    S_[a2:b2]=(['LSJ Definition:']+[rtf_text(x.encode('latin1')) for x in lines]) if lines is not None else []
    e.execute("update content_search set data=? where topic_id=?",('\r\n'.join(S_).encode('utf-16-le'),tid))
    return rtf_text('\n'.join(old[1:]).encode('latin1'))
for g in REPL:
    r=R2[g]; t,others,note=choose(r)
    lines=emit(parse(LT[t][1])); used=[LT[t][0]]
    old=replace(g,lines)
    out.append([g,r['lemma'],'replaced',old[:150].replace('\n',' | '),'+'.join(used),note])
for g in REMOVE:
    old=replace(g,None); out.append([g,R2[g]['lemma'],'removed (proper name; text was for a different common word, and LSJ has no entry for this name)',old[:150].replace('\n',' | '),'',''])
ec=e.execute("select value from config where name='editorial.comments'").fetchone()[0].decode()
ec+='\r\n-replaced %d LSJ sections that held the wrong or a partial entry with the full LSJ entry; removed the wrong LSJ text from G2136 and G9475 (proper names)'%len(REPL)
e.execute("update config set value=? where name='editorial.comments'",(ec.encode(),))
e.commit()
import csv
csv.writer(open('fix22.csv','w',newline='',encoding='utf-8-sig')).writerows([['Strong’s','Headword','Change','Old LSJ text (start)','LSJ entry now','Note']]+out)
for x in out: print(x[0],x[1],x[2][:8],'|',x[3][:70],'->',x[4],x[5][:60])
