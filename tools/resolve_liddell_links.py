import sqlite3, re, os, json, shutil, zipfile, unicodedata
from datetime import datetime

SCRATCH = "/home/eddie/.gemini/antigravity/brain/b16b06c4-30b5-46db-a486-605c7ab29bf0/scratch"
OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
SRC_DB = f"{OUT_BASE}/GBL-EPV_2026-11-20_1359.dct.twm"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
NEW_DB = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"

shutil.copy2(SRC_DB, NEW_DB)

RTF_HEADER = (
    r"{\rtf1\ansi\ansicpg1252\uc0\deff0"
    r"{\fonttbl{\f0\fnil Segoe UI;}{\f1\fnil\fcharset161 Gentium;}{\f2\fnil\fcharset177 Cardo;}}"
    r"{\colortbl;\red128\green0\blue0;\red0\green0\blue128;\red0\green0\blue255;\red96\green96\blue96;\red190\green190\blue190;}"
)

def rtf_escape(s):
    out = []
    for ch in s:
        o = ord(ch)
        if ch in ("\\", "{", "}"):
            out.append("\\" + ch)
        elif o < 128:
            out.append(ch)
        else:
            u = o if o < 32768 else o - 65536
            out.append(f"\\u{u} ")
    return "".join(out)

def strip_accents(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().replace("ς", "σ")

GREEK_MAP = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē", "θ": "th",
    "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p",
    "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "ō",
}
def transliterate_sbl(word):
    out = []
    chars = list(word)
    for i, ch in enumerate(chars):
        nfd = unicodedata.normalize("NFD", ch)
        base = nfd[0]
        marks = nfd[1:]
        rough = "\u0314" in marks
        is_upper = base.isupper()
        low = base.lower()
        tr = GREEK_MAP.get(low, base)
        if low == "υ" and i > 0:
            prev_base = unicodedata.normalize("NFD", chars[i-1])[0].lower()
            if prev_base in ("α", "ε", "η", "ο"):
                tr = "u"
        if low == "γ" and i + 1 < len(chars):
            next_base = unicodedata.normalize("NFD", chars[i+1])[0].lower()
            if next_base in ("γ", "κ", "ξ", "χ"):
                tr = "n"
        if rough:
            tr = "rh" if low == "ρ" else "h" + tr
        if is_upper and tr:
            tr = tr[0].upper() + tr[1:]
        out.append(tr)
    return "".join(out)

def normalize_lsj_rtf(raw_rtf, ltid_to_gbl):
    s = raw_rtf.strip()
    s = re.sub(r'\\u(-?\d+)\?', r'\\u\1 ', s)
    # Remap internal Liddell tid links to GBL tid if available, else plain styled Greek
    def repl_tid(m):
        ltid = int(m.group(1))
        inner = m.group(2)
        if ltid in ltid_to_gbl:
            gtid = ltid_to_gbl[ltid]
            return f'{{\\field{{\\*\\fldinst HYPERLINK "tw://[self]?tid={gtid}"}}{{\\fldrslt {inner}}}}}'
        return inner
    s = re.sub(
        r'\{\\field\{\\\*\\fldinst\s+HYPERLINK\s+"tw://\[self\]\?tid=(\d+)"\}\{\\fldrslt\s+(.*?)\}\}',
        repl_tid,
        s
    )
    s = re.sub(
        r'\{\\field\{\\\*\\fldinst\s+(HYPERLINK\s+"tw://\*\.\*\?txt=[^"]+")\}\{\\fldrslt\s+([^{}]+)\}\}',
        r'{\\field{\\*\\fldinst \1}{\\fldrslt {\\plain\\f0\\fs20\\cf3 \2}}}',
        s
    )
    s = re.sub(r'\{\\f1\s+', r'{\\plain\\f1\\fs24\\cf1 ', s)
    paras = [p.strip() for p in re.split(r'\\par\b', s) if p.strip() and p.strip() != r'\pard']
    out = []
    for idx, p in enumerate(paras):
        p = re.sub(r'^\\pard\s*', '', p)
        if p.startswith(r'\li250'):
            p = re.sub(r'^\\li250\s*', '', p)
            li = r'\pard\sb0\sa120\li720\fi-360 '
        elif idx == 0:
            li = r'\pard\sb0\sa120\li360\fi-360 '
        else:
            li = r'\pard\sb0\sa120\li720\fi-360 '
        out.append(f"{li}{{\\plain\\f0\\fs20 {p}}}\\par")
    return "\n".join(out)

def rtf_to_plain_clean(rtf_text):
    def dec_u(m):
        n = int(m.group(1))
        if n < 0: n += 65536
        return chr(n)
    t = re.sub(r"\\u(-?\d+)\s?", dec_u, rtf_text)
    t = re.sub(r"\{\\\*\\fldinst[^}]*\}", "", t)
    t = re.sub(r"\{\\fonttbl.*?\{\\colortbl[^}]*\}\}", "", t, flags=re.S)
    t = re.sub(r"\\par\b", "\r\n", t)
    t = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", t)
    t = t.replace("{", "").replace("}", "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"(\r\n){2,}", "\r\n", t)
    return t.strip()

liddell_850 = json.load(open(f"{SCRATCH}/liddell_850.json", encoding="utf-8"))

con = sqlite3.connect(NEW_DB)
cur = con.cursor()

gbl_lemmas = {r[1]: r[0] for r in cur.execute("SELECT id, subject FROM topics WHERE pid=0")}
max_id = cur.execute("SELECT MAX(id) FROM topics").fetchone()[0]
max_ro = cur.execute("SELECT MAX(rel_order) FROM topics WHERE pid=0").fetchone()[0] or 0

# Step 1: Assign GBL tid for all 850 Liddell tids (reuse existing pid=0 lemma or allocate new hidden topic id)
ltid_to_gbl = {}
new_lsj_topics = []
reused_count = 0

for ltid_str, info in sorted(liddell_850.items(), key=lambda x: int(x[0])):
    ltid = int(ltid_str)
    subj = info["subject"]
    clean_hw = subj.rstrip("0123456789 ")
    if clean_hw in gbl_lemmas:
        ltid_to_gbl[ltid] = gbl_lemmas[clean_hw]
        reused_count += 1
    elif subj in gbl_lemmas:
        ltid_to_gbl[ltid] = gbl_lemmas[subj]
        reused_count += 1
    else:
        max_id += 1
        ltid_to_gbl[ltid] = max_id
        new_lsj_topics.append((max_id, ltid, subj, clean_hw, info["rtf"]))

# Step 2: Insert the 767 new hidden LSJ reference topics into GBL-EPV
for gtid, ltid, subj, clean_hw, raw_rtf in new_lsj_topics:
    max_ro += 1
    translit = transliterate_sbl(clean_hw)
    norm_body = normalize_lsj_rtf(raw_rtf, ltid_to_gbl)
    full_rtf = "\n".join([
        RTF_HEADER,
        f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f1\\fs24\\b\\cf1 {rtf_escape(subj)}}}{{\\plain\\f0\\fs20   }}{{\\plain\\f0\\fs20\\cf2\\i ({rtf_escape(translit)})}}\\par",
        "\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b LSJ Definition:}\\par",
        norm_body,
        "}"
    ])
    cur.execute("INSERT INTO topics (id, pid, subject, rel_order, content_type) VALUES (?, 0, ?, ?, 'rtf')", (gtid, subj, max_ro))
    cur.execute("INSERT INTO topics_flags (id, hidden) VALUES (?, 1)", (gtid,))
    cur.execute("INSERT INTO content (topic_id, data) VALUES (?, ?)", (gtid, full_rtf.encode("latin1")))
    cur.execute("INSERT INTO content_search (topic_id, data) VALUES (?, ?)", (gtid, rtf_to_plain_clean(full_rtf).encode("utf-16-le")))
    for w, prio in [(clean_hw.lower(), 1), (strip_accents(clean_hw), 500), (translit.lower(), 600)]:
        cur.execute("INSERT INTO topics_wordindex (id, word, priority) VALUES (?, ?, ?)", (gtid, w, prio))

print(f"Mapped 850 Liddell tids: {reused_count} reused existing GBL lemmas, {len(new_lsj_topics)} inserted as hidden LSJ topics")

# Step 3: Rewrite all 1,008 tw://dct.Liddell.dct?tid=N links across all 905 topics in GBL-EPV,
# AND inline the referenced LSJ body into the 12 short cross-reference entries!
SHORT_12 = {9822, 33108, 34736, 34784, 35558, 35694, 35748, 36016, 36248, 37038, 37230, 37258}
rewritten_topics = 0
rewritten_links = 0
inlined_short = 0

rows_to_fix = cur.execute("SELECT topic_id, data FROM content").fetchall()
for tid, d in rows_to_fix:
    is_b = isinstance(d, bytes)
    s = d.decode("latin1") if is_b else d
    if "tw://dct.Liddell.dct?tid=" not in s:
        continue

    # If one of the 12 short cross-ref entries, inline the referenced LSJ paragraphs before OT (LXX) Occurrences
    if tid in SHORT_12:
        m_first = re.search(r"tw://dct\.Liddell\.dct\?tid=(\d+)", s)
        if m_first:
            ref_ltid = m_first.group(1)
            ref_norm = normalize_lsj_rtf(liddell_850[ref_ltid]["rtf"], ltid_to_gbl)
            occ_pos = s.find(r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b OT (LXX) Occurrences:")
            if occ_pos > 0:
                s = s[:occ_pos] + ref_norm + "\n" + s[occ_pos:]
            else:
                rbrace = s.rfind("}")
                s = s[:rbrace] + ref_norm + "\n" + s[rbrace:]
            inlined_short += 1

    def repl_liddell(m):
        global rewritten_links
        ltid = int(m.group(1))
        gtid = ltid_to_gbl[ltid]
        rewritten_links += 1
        return f"tw://[self]?tid={gtid}"

    s_new = re.sub(r"tw://dct\.Liddell\.dct\?tid=(\d+)", repl_liddell, s)
    val = s_new.encode("latin1") if is_b else s_new
    cur.execute("UPDATE content SET data=? WHERE topic_id=?", (val, tid))
    cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(s_new).encode("utf-16-le"), tid))
    rewritten_topics += 1

# Step 4: Update Appendix (tid=24331) Section 7 (Liddell links) and Section 9 (20 November)
ap_d = cur.execute("SELECT data FROM content WHERE topic_id=24331").fetchone()[0]
ap_is_b = isinstance(ap_d, bytes)
ap_rtf = ap_d.decode("latin1") if ap_is_b else ap_d
m_lid = re.search(r'Liddell links: \}\{\\plain\\f0\\fs20 .*?\\par', ap_rtf)
assert m_lid, "Liddell links bullet not found in Appendix!"
new_lid_bullet = (
    "Liddell links: }{\\plain\\f0\\fs20 all 1,008 cross-references inside LSJ definitions that formerly pointed "
    "to the external Liddell.dct module have now been copied into this dictionary and linked internally (20 November 2026), "
    "so every LSJ link works standalone without Liddell.dct installed.}\\par"
)
ap_rtf = ap_rtf.replace(m_lid.group(0), new_lid_bullet, 1)
ap_rtf = ap_rtf.replace(
    "sub-tagged from LSJ, BDB, ISBE, and verse context.}",
    "sub-tagged from LSJ, BDB, ISBE, and verse context; all 850 external Liddell.dct cross-reference targets copied into GBL-EPV so all 1,008 LSJ links resolve internally.}"
)
cur.execute("UPDATE content SET data=? WHERE topic_id=24331", (ap_rtf.encode("latin1") if ap_is_b else ap_rtf,))
cur.execute("UPDATE content_search SET data=? WHERE topic_id=24331", (rtf_to_plain_clean(ap_rtf).encode("utf-16-le"),))

con.commit()

# Verify 0 remaining tw://dct.Liddell.dct links anywhere in the database!
rem_liddell = 0
for (d,) in cur.execute("SELECT data FROM content"):
    s = d.decode("latin1") if isinstance(d, bytes) else d
    if "Liddell.dct?tid=" in s:
        rem_liddell += 1
assert rem_liddell == 0, f"Remaining Liddell.dct links: {rem_liddell}"

ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
assert ic == "ok", f"integrity_check failed: {ic}"
con.close()

with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=os.path.basename(NEW_DB))

print(f"DONE! Rewrote {rewritten_links} links across {rewritten_topics} topics; inlined {inlined_short} short cross-ref entries.")
print(f"Remaining external Liddell.dct links: {rem_liddell}")
print(f"PRAGMA integrity_check: {ic}")
print(f"DB:  {NEW_DB} ({os.path.getsize(NEW_DB):,} bytes)")
print(f"ZIP: {NEW_ZIP} ({os.path.getsize(NEW_ZIP):,} bytes)")
