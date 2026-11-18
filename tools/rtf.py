import re
def rtf_text(b):
    s=b.decode('latin1') if isinstance(b,bytes) else b
    # drop fldinst
    s=re.sub(r'\{\\\*\\fldinst[^{}]*\}','',s)
    s=re.sub(r'\{\\fonttbl.*?\}\}','',s,flags=re.S)
    s=re.sub(r'\{\\colortbl[^}]*\}','',s)
    out=[];i=0;n=len(s)
    while i<n:
        ch=s[i]
        if ch=='\\':
            m=re.match(r"\\u(-?\d+) ?\??",s[i:])
            if m:
                v=int(m.group(1)); v+=65536 if v<0 else 0
                out.append(chr(v)); i+=m.end(); continue
            m=re.match(r"\\'([0-9a-fA-F]{2})",s[i:])
            if m: out.append(bytes([int(m.group(1),16)]).decode('cp1252','replace')); i+=m.end(); continue
            m=re.match(r"\\(par|line)\b ?",s[i:])
            if m: out.append('\n'); i+=m.end(); continue
            m=re.match(r"\\(ldblquote|rdblquote|lquote|rquote|emdash|endash|tab)\b ?",s[i:])
            if m: out.append({'ldblquote':'\u201c','rdblquote':'\u201d','lquote':'\u2018','rquote':'\u2019','emdash':'\u2014','endash':'\u2013','tab':'\t'}[m.group(1)]); i+=m.end(); continue
            m=re.match(r"\\([{}\\])",s[i:])
            if m: out.append(m.group(1)); i+=2; continue
            m=re.match(r"\\[a-zA-Z]+-?\d* ?",s[i:])
            if m: i+=m.end(); continue
            i+=2; continue
        if ch in '{}': i+=1; continue
        if ch in '\r\n': i+=1; continue
        out.append(ch); i+=1
    t=''.join(out)
    t=re.sub(r'[ \t]+',' ',t); t=re.sub(r' *\n *','\n',t); t=re.sub(r'\n{2,}','\n',t)
    return t.strip()
