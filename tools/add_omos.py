import sys,sqlite3,zlib,re
sys.path.insert(0,'py'); import conv; from conv import parse,emit,esc
from rtf import rtf_text
F=sys.argv[1]
e=sqlite3.connect(F); e.text_factory=bytes
l=sqlite3.connect('file:in/Liddell.dct.twm?mode=ro',uri=True); l.text_factory=bytes
EP={}
for tid,sb in e.execute("select id,subject from topics"): EP.setdefault(sb.decode(),tid)
for tid,s in l.execute("select id,subject from topics"):
    if s.decode() in EP: conv.SELF[tid]='tw://[self]?tid=%d'%EP[s.decode()]
src=zlib.decompress(l.execute("select data from content where topic_id=116219").fetchone()[0]).decode('latin1')
HDR=e.execute("select data from content where topic_id=1").fetchone()[0].decode('latin1').split('\n')[0]
G='G13149'; W='ὠμός'; TR='ōmos'
def H(lbl,val=None):
    return '\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b %s:%s}%s\\par'%(lbl,' ' if val else '','{\\plain\\f0\\fs20 %s}'%esc(val) if val else '')
body=[HDR,
 '\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f1\\fs24\\b\\cf1 %s}{\\plain\\f0\\fs20  }{\\plain\\f0\\fs20\\cf2\\i (%s)}\\par'%(esc(W),esc(TR)),
 H('Part of Speech','adjective'),
 H('Definition')]
for d in ['1) raw, uncooked (of meat)','2) unripe','3) metaphorically, savage, cruel']:
    body.append('\\pard\\sb0\\sa120\\li360\\fi-360 {\\plain\\f0\\fs20 %s}\\par'%esc(d))
body.append(H('LSJ Definition')); body+=emit(parse(src))
body.append(H('OT (LXX) Occurrences','Rahlfs: 1 · Swete: 1 · Brenton: 1'))
body.append('\\pard\\sb0\\sa120\\li0\\fi0 {\\field{\\*\\fldinst HYPERLINK "tw://bible.*?id=2.12.9"}{\\fldrslt {\\plain\\f0\\fs18\\cf3 Exod 12:9}}}\\par')
body.append('}')
gdata='\n'.join(body)
lem='\n'.join([HDR,
 '\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f1\\fs28\\b\\cf1 %s}{\\plain\\f0\\fs20  }{\\plain\\f0\\fs20\\cf2\\i (%s)}{\\plain\\f0\\fs20  %s}\\par'%(esc(W),esc(TR),esc('— raw, uncooked')),
 '\\pard\\sb0\\sa60\\li360\\fi-360 {\\field{\\*\\fldinst HYPERLINK "tw://[self]?%s"}{\\fldrslt {\\plain\\f0\\fs20\\cf3 %s}}}{\\plain\\f0\\fs20  }{\\plain\\f1\\fs24\\cf1 %s}{\\plain\\f0\\fs20  }{\\plain\\f0\\fs20\\cf2\\i (%s)}{\\plain\\f0\\fs20  %s}\\par'%(G,G,esc(W),esc(TR),esc('— adjective')),'}'])
assert not e.execute("select 1 from topics where subject in (?,?)",(G,W)).fetchone()
ro=e.execute("select rel_order from topics where id=25691").fetchone()[0]
e.execute("update topics set rel_order=rel_order+1 where pid=0 and rel_order>?",(ro,))
mx=e.execute("select max(id) from topics").fetchone()[0]
lid,gid=mx+1,mx+2
e.execute("insert into topics(id,pid,subject,rel_order,content_type) values(?,?,?,?,?)",(lid,0,W,ro+1,'rtf'))
e.execute("insert into topics(id,pid,subject,rel_order,content_type) values(?,?,?,?,?)",(gid,lid,G,0,'rtf'))
for tid,d in ((lid,lem),(gid,gdata)):
    e.execute("insert into content(topic_id,data,data2) values(?,?,NULL)",(tid,d.encode('latin1')))
    e.execute("insert into content_search(topic_id,data) values(?,?)",(tid,rtf_text(d.encode('latin1')).replace('\n','\r\n').encode('utf-16-le')))
e.execute("insert into topics_wordindex values(?,?,1)",(lid,W)); e.execute("insert into topics_wordindex values(?,?,1)",(gid,G.lower()))
e.execute("insert into bible_link_search values(?,?)",(gid,',2.12.9,1\r\nTotal_LINK_Count:1\r\n'))
d=e.execute("select value from config where name='description'").fetchone()[0].decode()
e.execute("update config set value=? where name='description'",(re.sub(r'G1-G\d+','G1-G13149',d).encode(),))
ec=e.execute("select value from config where name='editorial.comments'").fetchone()[0].decode()
ec+='\r\n-added G13149 ὠμός "raw, uncooked" (Exod 12:9); the LXX modules tag this word as G5606 ὦμος "shoulder"'
e.execute("update config set value=? where name='editorial.comments'",(ec.encode(),))
e.commit(); print(lid,gid); print(rtf_text(gdata.encode('latin1'))[:900]); print(rtf_text(lem.encode('latin1')))
