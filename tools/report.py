import sys,pickle,re,csv,collections,unicodedata
sys.path.insert(0,'.'); W=sys.argv[1]
exec(open('analyze2.py').read().split("rows=[]")[0])
R=pickle.load(open(W+'/rows.pkl','rb'))
def hebrewish(r):
    t=E[r['g']][1]
    return ('Hebrew' in sections(t)) or not any(unicodedata.combining(ch) for ch in unicodedata.normalize('NFD',r['lemma']))
cat=collections.Counter(); out=[]
for r in R:
    proper=r['proper']; best=r['best'] or ''
    capmatch=bool(best[:1]) and best[:1].isupper()
    if r['has']:
        if r['cov'] is None: c='3 Has LSJ section, but no LSJ headword found to compare'
        elif r['cov']>=0.8: c='1 OK: has full LSJ entry'
        else: c='2 Has LSJ section, but it does not match the LSJ entry for this word (wrong or partial text)'
    else:
        if r['cands'] and proper and not capmatch: c='6 Proper name: LSJ has only a common word with this spelling (not added)'
        elif r['cands'] and r['how']=='exact': c='4 Missing: LSJ has this exact headword (add full entry)'
        elif r['cands']: c='5 Missing: LSJ has it under a related headword (add after your review)'
        elif proper: c='7 Not in LSJ: proper name'
        elif hebrewish(r): c='8 Not in LSJ: Hebrew/Aramaic transliteration'
        else: c='9 Not in LSJ: Greek word (needs another source or a manual LSJ search)'
    cat[c]+=1
    out.append([c,r['g'],r['lemma'],r['pos'].replace('\n',' '),best,r['how'],'' if r['cov'] is None else '%.0f%%'%(100*r['cov']),
                'Thayer' if r['thayer'] else ('Other definition' if r['other'] else '')])
out.sort(key=lambda x:(x[0],int(x[1][1:])))
fn=W+'/LSJ_coverage_report_%s.csv'%sys.argv[2]
with open(fn,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['Category','Strong’s','Headword','Part of speech','LSJ headword matched','How matched','LSJ text present','Other definition in entry']); w.writerows(out)
for k in sorted(cat): print(cat[k],k)
print(sum(cat.values()),fn)
