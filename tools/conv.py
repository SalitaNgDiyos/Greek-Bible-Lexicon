import re
SYM={'ldblquote':'\u201c','rdblquote':'\u201d','lquote':'\u2018','rquote':'\u2019','emdash':'\u2014','endash':'\u2013','tab':'\t','bullet':'\u2022'}
def parse(src):
    """LSJ RTF -> list of paragraphs (li, [(text, greek, ital, bold, link)])"""
    s=src; i=0; n=len(s)
    st=dict(g=False,i=False,link=None,skip=False,fld=False,inst=False)
    stack=[]; bold=False; li=0
    paras=[]; runs=[]
    def add(t):
        if st['skip']: return
        if st['inst']: st['_buf'].append(t); return
        runs.append([t,st['g'],st['i'],bold,st['link']])
    while i<n:
        ch=s[i]
        if ch=='{':
            stack.append(dict(st)); i+=1
            if s.startswith('\\*',i):
                if st['inst']: st['skip']=True
                else: st['inst']=True; st['_buf']=[]; st['_d']=len(stack)
                i+=2
            continue
        if ch=='}':
            if st['inst'] and st.get('_d')==len(stack):
                m=re.search(r'HYPERLINK\s+"([^"]*)"',''.join(st['_buf']))
                tgt=m.group(1) if m else None
                st=stack.pop(); st['_pend']=tgt
            else:
                pend=st.get('_pend'); 
                st=stack.pop()
                if pend is not None and '_pend' not in st: pass
            i+=1; continue
        if ch=='\\':
            m=re.match(r'\\u(-?\d+)\??',s[i:])
            if m:
                v=int(m.group(1)); v+=65536 if v<0 else 0; add(chr(v)); i+=m.end(); continue
            m=re.match(r"(?:\\'[0-9a-fA-F]{2})+",s[i:])
            if m:
                bb=bytes(int(h,16) for h in re.findall(r"'([0-9a-fA-F]{2})",m.group(0)))
                try: add(bb.decode('utf-8'))
                except UnicodeDecodeError: add(bb.decode('cp1252','replace'))
                i+=m.end(); continue
            m=re.match(r'\\([{}\\])',s[i:])
            if m: add(m.group(1)); i+=2; continue
            m=re.match(r'\\([a-zA-Z]+)(-?\d+)? ?',s[i:])
            if not m: i+=1; continue
            w,a=m.group(1),m.group(2); i+=m.end()
            if w=='f': st['g']=(a=='1')
            elif w=='i': st['i']=(a!='0')
            elif w=='b': bold=(a!='0')
            elif w=='par':
                paras.append((li,runs)); runs=[]
            elif w=='pard': li=0
            elif w=='li': li=int(a)
            elif w=='field': st['fld']=True
            elif w=='fldrslt':
                if not st['inst']: st['link']=stack[-1].get('_pend') if stack else None
            elif w in SYM: add(SYM[w])
            continue
        if ch in '\r\n': i+=1; continue
        add(ch); i+=1
    if runs: paras.append((li,runs))
    return paras
def _fix(m):
    try: return m.group(0).encode('latin1').decode('utf-8')
    except UnicodeError: return m.group(0)
def esc(t):
    t=re.sub(r'[\x80-\xff]{2,}',_fix,t)
    o=[]
    for c in t:
        if c in '\\{}': o.append('\\'+c)
        elif ord(c)>126: v=ord(c); o.append('\\u%d '%(v-65536 if v>32767 else v))
        else: o.append(c)
    return ''.join(o)
LI={0:360,250:720,500:1080}
SELF={}
def emit(paras):
    out=[]
    lv=sorted(set(li for li,_ in paras)); LI={v:360+360*k for k,v in enumerate(lv)}
    for li,runs in paras:
        # merge
        m=[]
        for r in runs:
            if m and m[-1][1:]==r[1:]: m[-1][0]+=r[0]
            else: m.append(list(r))
        # strip trailing whitespace of paragraph
        while m and not m[-1][0].strip(): m.pop()
        if m: m[-1][0]=m[-1][0].rstrip()
        while m and not m[0][0].strip(): m.pop(0)
        m2=[]
        for r in m:
            if m2 and not r[0].strip() and m2[-1][0].endswith(' '): continue
            m2.append(r)
        m=m2
        if not m: continue
        parts=[]
        for t,g,it,b,lk in m:
            if not t: continue
            fmt='\\plain\\f1\\fs24\\cf1' if g else '\\plain\\f0\\fs20'
            if lk is not None and lk.startswith('tw://[self]?tid='):
                n_=int(lk.split('=')[1]); lk=SELF.get(n_,'tw://dct.Liddell.dct?tid=%d'%n_)
            if lk is not None:
                fmt=('\\plain\\f1\\fs24\\cf3' if g else '\\plain\\f0\\fs20\\cf3')+('\\b' if b else '')+('\\i' if it else '')
                parts.append('{\\field{\\*\\fldinst HYPERLINK "%s"}{\\fldrslt {%s %s}}}'%(esc(lk),fmt,esc(t)))
                continue
            if b: fmt+='\\b'
            if it: fmt+='\\i'
            parts.append('{%s %s}'%(fmt,esc(t)))
        out.append('\\pard\\sb0\\sa120\\li%d\\fi-360 %s\\par'%(LI.get(li,li),''.join(parts)))
    return out
