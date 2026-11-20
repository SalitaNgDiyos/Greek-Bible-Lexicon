import sqlite3, csv, json, os, re, shutil, zipfile, unicodedata, glob
from datetime import datetime
import sys

SCRATCH = "/home/eddie/.gemini/antigravity/brain/b16b06c4-30b5-46db-a486-605c7ab29bf0/scratch"
sys.path.insert(0, SCRATCH)
from proper_name_and_new_defs import PROPER_NAME_DEFS, NEW_G15724_PLUS

CSV3 = "/home/eddie/.gemini/antigravity/brain/b16b06c4-30b5-46db-a486-605c7ab29bf0/.user_uploaded/media_1795135836817_15e21e87.csv"
OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
TODAY_ISO = datetime.now().strftime("%Y-%m-%d")

BOOK_ABBREV = {
    "TOB": "Tob", "JDT": "Jdt", "WIS": "Wis", "SIR": "Sir",
    "BAR": "Bar", "LJE": "Ep Jer", "S3Y": "Pr Azar",
    "SUS": "Sus", "BEL": "Bel", "1MA": "1 Macc",
    "2MA": "2 Macc", "1ES": "1 Esd", "MAN": "Pr Man",
    "3MA": "3 Macc", "4MA": "4 Macc",
}
BOOK_FULL = {
    "TOB": "Tobit", "JDT": "Judith", "WIS": "Wisdom of Solomon", "SIR": "Sirach",
    "BAR": "Baruch", "LJE": "Letter of Jeremiah", "S3Y": "Prayer of Azariah",
    "SUS": "Susanna", "BEL": "Bel and the Dragon", "1MA": "1 Maccabees",
    "2MA": "2 Maccabees", "1ES": "1 Esdras", "MAN": "Prayer of Manasseh",
    "3MA": "3 Maccabees", "4MA": "4 Maccabees",
}

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
            # RTF signed 16-bit \uN (with \uc0 -> trailing space delimiter)
            u = o if o < 32768 else o - 65536
            out.append(f"\\u{u} ")
    return "".join(out)

def strip_accents(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().replace("ς", "σ")

# Clean SBL-style Greek transliteration
GREEK_MAP = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē", "θ": "th",
    "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p",
    "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "ō",
}
def transliterate_sbl(word):
    out = []
    # Check rough breathing per character via NFD
    chars = list(word)
    for i, ch in enumerate(chars):
        nfd = unicodedata.normalize("NFD", ch)
        base = nfd[0]
        marks = nfd[1:]
        rough = "\u0314" in marks
        is_upper = base.isupper()
        low = base.lower()
        tr = GREEK_MAP.get(low, base)
        # upsilon in diphthongs au, eu, ou, ēu -> u
        if low == "υ" and i > 0:
            prev_base = unicodedata.normalize("NFD", chars[i-1])[0].lower()
            if prev_base in ("α", "ε", "η", "ο"):
                tr = "u"
        # gamma nasal before γ, κ, ξ, χ -> n
        if low == "γ" and i + 1 < len(chars):
            next_base = unicodedata.normalize("NFD", chars[i+1])[0].lower()
            if next_base in ("γ", "κ", "ξ", "χ"):
                tr = "n"
        if rough:
            if low == "ρ":
                tr = "rh"
            else:
                tr = "h" + tr
        if is_upper and tr:
            tr = tr[0].upper() + tr[1:]
        out.append(tr)
    return "".join(out)

def normalize_lsj_rtf(raw_rtf):
    # Remove trailing \pard or whitespace
    s = raw_rtf.strip()
    # Convert \uN? (uc1) to \uN  (uc0)
    s = re.sub(r'\\u(-?\d+)\?', r'\\u\1 ', s)
    # Strip dead internal tid links (tw://[self]?tid=...) to plain styled display text
    s = re.sub(
        r'\{\\field\{\\\*\\fldinst\s+HYPERLINK\s+"tw://\[self\]\?tid=\d+"\}\{\\fldrslt\s+(.*?)\}\}',
        r'\1',
        s
    )
    # Style external tooltip hyperlinks nicely
    s = re.sub(
        r'\{\\field\{\\\*\\fldinst\s+(HYPERLINK\s+"tw://\*\.\*\?txt=[^"]+")\}\{\\fldrslt\s+([^{}]+)\}\}',
        r'{\\field{\\*\\fldinst \1}{\\fldrslt {\\plain\\f0\\fs20\\cf3 \2}}}',
        s
    )
    # Style {\f1 ...} Greek runs to {\plain\f1\fs24\cf1 ...}
    s = re.sub(r'\{\\f1\s+', r'{\\plain\\f1\\fs24\\cf1 ', s)
    # Split on \par and wrap paragraphs cleanly
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

def rtf_to_plain_for_search(rtf_text):
    # Decode \uN  escapes back to unicode and strip RTF control words/braces
    def dec_u(m):
        n = int(m.group(1))
        if n < 0:
            n += 65536
        return chr(n)
    t = re.sub(r'\\u(-?\d+)\s?', dec_u, rtf_text)
    t = re.sub(r'\{\\\*\\fldinst[^}]*\}', '', t)
    t = re.sub(r'\{\\fonttbl.*?\{\\colortbl[^}]*\}\}', '', t, flags=re.S)
    t = t.replace(r'\par', '\r\n')
    t = re.sub(r'\\[a-zA-Z]+-?\d*\s?', '', t)
    t = t.replace('{', '').replace('}', '')
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

# Load occurrence index & LSJ bodies
occ_data = json.load(open(f"{SCRATCH}/deut_occurrences.json", encoding="utf-8"))
ra_occ = occ_data["rahlfs"]
sw_occ = occ_data["swete"]
lsj_bodies = json.load(open(f"{SCRATCH}/lsj_bodies.json", encoding="utf-8"))

# Build complete list of 219 new entries (G15519..G15737)
entries = []
with open(CSV3, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        g = r["Number"].strip()
        if not re.fullmatch(r"G15(5[1-9]\d|6\d\d|7[0-2]\d)", g):
            continue
        hw = r["Headword"].strip()
        pos = r["Part of speech"].strip()
        defn = r["Definition"].strip()
        how = r["How defined"].strip()
        lsj = r["LSJ"].strip()
        if g in PROPER_NAME_DEFS:
            defn = PROPER_NAME_DEFS[g]
            how = "name+context"
        assert defn, f"Missing definition for {g} ({hw})"
        entries.append((g, hw, pos, defn, how, lsj))

for row in NEW_G15724_PLUS:
    entries.append(row)

# Verify contiguous G15519..G15737 (219 entries)
nums = [int(e[0][1:]) for e in entries]
assert nums == list(range(15519, 15738)), f"Non-contiguous range! len={len(nums)}, min={min(nums)}, max={max(nums)}"
print(f"Verified contiguous new entries: G15519..G15737 ({len(entries)} entries)")

# Copy base GBL-EPV db to output path
base_db = glob.glob(f"{SCRATCH}/GBL-EPV*.dct.twm")[0]
out_twm = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
shutil.copy2(base_db, out_twm)

con = sqlite3.connect(out_twm)
cur = con.cursor()

# Existing max topic id & existing pid=0 subjects
max_id = cur.execute("SELECT MAX(id) FROM topics").fetchone()[0]
existing_parents = {}
for tid, subj in cur.execute("SELECT id, subject FROM topics WHERE pid=0"):
    existing_parents[subj] = tid

existing_g = set(r[0] for r in cur.execute("SELECT subject FROM topics WHERE subject LIKE 'G%'") if re.fullmatch(r"G\d+", r[0]))

log_rows = []
inserted_count = 0

for g, hw, pos, defn, how, lsj in entries:
    assert g not in existing_g, f"{g} already exists in base GBL-EPV!"
    translit = transliterate_sbl(hw)
    ro = ra_occ.get(g, [])
    so = sw_occ.get(g, [])

    # Build concise verse reference list (grouped by book)
    book_refs = {}
    books_used = []
    for bk, ch, v, _ in ro + so:
        if bk not in book_refs:
            book_refs[bk] = []
            books_used.append(bk)
        ref = f"{ch}:{v}"
        if ref not in book_refs[bk]:
            book_refs[bk].append(ref)
    ref_parts = []
    for bk in books_used:
        ab = BOOK_ABBREV.get(bk, bk)
        ref_parts.append(f"{ab} " + ", ".join(book_refs[bk]))
    ref_line = "; ".join(ref_parts)
    books_csv = "; ".join(BOOK_FULL.get(bk, bk) for bk in books_used)

    # Build child (G####) RTF
    rtf_lines = [
        RTF_HEADER,
        f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f1\\fs24\\b\\cf1 {rtf_escape(hw)}}}{{\\plain\\f0\\fs20   }}{{\\plain\\f0\\fs20\\cf2\\i ({rtf_escape(translit)})}}\\par",
        f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f0\\fs20\\b Part of Speech: }}{{\\plain\\f0\\fs20 {rtf_escape(pos)}}}\\par",
        "\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b Definition:}\\par",
    ]
    for sense in defn.split("|"):
        sense = sense.strip()
        if sense:
            rtf_lines.append(f"\\pard\\sb0\\sa120\\li360\\fi-360 {{\\plain\\f0\\fs20 {rtf_escape(sense)}}}\\par")

    if g in lsj_bodies:
        rtf_lines.append("\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b LSJ Definition:}\\par")
        rtf_lines.append(normalize_lsj_rtf(lsj_bodies[g]["rtf"]))

    if ro or so:
        rtf_lines.append(
            f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f0\\fs20\\b OT (LXX) Occurrences: }}"
            f"{{\\plain\\f0\\fs20 Deuterocanon: Rahlfs {len(ro)} \\u183  Swete {len(so)}}}\\par"
        )
        rtf_lines.append(f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f0\\fs18\\cf3 {rtf_escape(ref_line)}}}\\par")

    rtf_lines.append("}")
    child_rtf = "\n".join(rtf_lines)
    child_bytes = child_rtf.encode("latin1")
    child_search = rtf_to_plain_for_search(child_rtf).encode("utf-16-le")

    # Short gloss for parent card
    short_gloss = defn.split("|")[0].strip()
    short_gloss = re.sub(r"^1\)\s*", "", short_gloss)
    if len(short_gloss) > 100:
        short_gloss = short_gloss[:97].rstrip(" ,;.") + "..."

    link_line = (
        f"\\pard\\sb0\\sa60\\li0\\fi0 "
        f"{{\\field{{\\*\\fldinst HYPERLINK \"tw://[self]?{g}\"}}{{\\fldrslt {{\\plain\\f0\\fs20\\cf3 {g}}}}}}}"
        f"{{\\plain\\f0\\fs20   }}{{\\plain\\f1\\fs24\\b\\cf1 {rtf_escape(hw)}}}"
        f"{{\\plain\\f0\\fs20   }}{{\\plain\\f0\\fs20\\cf2\\i ({rtf_escape(translit)})}}"
        f"{{\\plain\\f0\\fs20   \\u8212  {rtf_escape(pos)}}}\\par"
    )

    if hw in existing_parents:
        pid = existing_parents[hw]
        # Append link to existing parent RTF
        old_p = cur.execute("SELECT data FROM content WHERE topic_id=?", (pid,)).fetchone()
        if old_p and old_p[0]:
            old_str = (old_p[0].decode("latin1") if isinstance(old_p[0], bytes) else old_p[0]).rstrip()
            if old_str.endswith("}"):
                new_p = old_str[:-1] + "\n" + link_line + "\n}"
                cur.execute("UPDATE content SET data=? WHERE topic_id=?", (new_p.encode("latin1"), pid))
                cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_for_search(new_p).encode("utf-16-le"), pid))
        next_rel = (cur.execute("SELECT MAX(rel_order) FROM topics WHERE pid=?", (pid,)).fetchone()[0] or -1) + 1
    else:
        max_id += 1
        pid = max_id
        existing_parents[hw] = pid
        cur.execute("INSERT INTO topics (id, pid, subject, rel_order, content_type) VALUES (?, 0, ?, 0, 'rtf')", (pid, hw))
        parent_rtf = "\n".join([
            RTF_HEADER,
            f"\\pard\\sb0\\sa120\\li0\\fi0 {{\\plain\\f1\\fs28\\b\\cf1 {rtf_escape(hw)}}}{{\\plain\\f0\\fs20   }}{{\\plain\\f0\\fs20\\cf2\\i ({rtf_escape(translit)})}}{{\\plain\\f0\\fs20   \\u8212  {rtf_escape(short_gloss)}}}\\par",
            link_line,
            "}"
        ])
        cur.execute("INSERT INTO content (topic_id, data) VALUES (?, ?)", (pid, parent_rtf.encode("latin1")))
        cur.execute("INSERT INTO content_search (topic_id, data) VALUES (?, ?)", (pid, rtf_to_plain_for_search(parent_rtf).encode("utf-16-le")))
        # topics_wordindex for parent
        wi_entries = [
            (hw.lower(), 1),
            (strip_accents(hw), 500),
            (translit.lower(), 600),
        ]
        seen_w = set()
        for w, prio in wi_entries:
            if w and w not in seen_w:
                seen_w.add(w)
                cur.execute("INSERT INTO topics_wordindex (id, word, priority) VALUES (?, ?, ?)", (pid, w, prio))
        next_rel = 0

    max_id += 1
    cid = max_id
    cur.execute("INSERT INTO topics (id, pid, subject, rel_order, content_type) VALUES (?, ?, ?, ?, 'rtf')", (cid, pid, g, next_rel))
    cur.execute("INSERT INTO content (topic_id, data) VALUES (?, ?)", (cid, child_bytes))
    cur.execute("INSERT INTO content_search (topic_id, data) VALUES (?, ?)", (cid, child_search))
    cur.execute("INSERT INTO topics_wordindex (id, word, priority) VALUES (?, ?, 1)", (cid, g.lower()))
    inserted_count += 1

    log_rows.append([g, hw, translit, pos, defn, how, lsj, len(ro), len(so), len(ro)+len(so), books_csv])

# Re-sort pid=0 topics alphabetically by accentless key (keeping non-Greek front matter at top if any)
top_rows = cur.execute("SELECT id, subject, rel_order FROM topics WHERE pid=0").fetchall()
def sort_key(row):
    tid, subj, old_ro = row
    # Keep non-Greek subjects (like abbreviations/preface) at their original front order
    if not re.search(r'[\u0370-\u03FF\u1F00-\u1FFF]', subj):
        return (0, old_ro, subj.lower())
    return (1, 0, strip_accents(subj), subj)

top_rows.sort(key=sort_key)
for idx, (tid, _, _) in enumerate(top_rows):
    cur.execute("UPDATE topics SET rel_order=? WHERE id=?", (idx, tid))

# Update config metadata
cur.execute("UPDATE config SET value=? WHERE name='version.date'", (TODAY_ISO.encode("utf-8"),))
desc_raw = cur.execute("SELECT value FROM config WHERE name='description'").fetchone()[0]
desc_str = desc_raw.decode("utf-8") if isinstance(desc_raw, bytes) else str(desc_raw)
desc_str = desc_str.replace("G1-G15518", "G1-G15737")
cur.execute("UPDATE config SET value=? WHERE name='description'", (desc_str.encode("utf-8"),))

ec_raw = cur.execute("SELECT value FROM config WHERE name='editorial.comments'").fetchone()[0]
ec_str = ec_raw.decode("utf-8") if isinstance(ec_raw, bytes) else str(ec_raw)
ec_add = (
    f"\r\n11/20/2026\r\n"
    f"-added G15519 to G15737 (219 entries): Deuterocanon Rahlfs and Swete vocabulary "
    f"and proper names with contextual definitions, LSJ entries, and occurrence counts"
)
cur.execute("UPDATE config SET value=? WHERE name='editorial.comments'", ((ec_str + ec_add).encode("utf-8"),))

con.commit()

# --- FULL VERIFICATION ---
ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
assert ic == "ok", f"SQLite integrity_check failed: {ic}"

# Verify 0 copyrighted lexicon author names in ALL newly inserted entries + config
BANNED = ["Lust", "Eynikel", "Hauspie", "Muraoka"]
new_tids = [r[0] for r in cur.execute("SELECT id FROM topics WHERE subject GLOB 'G15519' OR (subject LIKE 'G15%' AND CAST(SUBSTR(subject,2) AS INT) >= 15519)")]
assert len(new_tids) == 219, f"Expected 219 new G-topics, found {len(new_tids)}"
for tid in new_tids:
    txt = cur.execute("SELECT data FROM content_search WHERE topic_id=?", (tid,)).fetchone()[0].decode("utf-16-le")
    for b in BANNED:
        assert b.lower() not in txt.lower(), f"BANNED word {b} found in topic {tid}!"
for name, val in cur.execute("SELECT name, value FROM config"):
    vstr = val.decode("utf-8", errors="ignore") if isinstance(val, bytes) else str(val)
    for b in BANNED:
        assert b.lower() not in vstr.lower(), f"BANNED word {b} found in config.{name}!"

# Verify 100% of Strong's numbers across all 30 USFM files exist in GBL-EPV!
all_g_in_db = set(r[0] for r in cur.execute("SELECT subject FROM topics WHERE subject LIKE 'G%'") if re.fullmatch(r"G\d+", r[0]))
missing_from_db = set()
for ed in ("rahlfs", "swete"):
    for fn in sorted(os.listdir(f"{OUT_BASE}/{ed}")):
        if not fn.endswith(".usfm"):
            continue
        txt = open(f"{OUT_BASE}/{ed}/{fn}", encoding="utf-8").read()
        for m in re.finditer(r'strong="([^"]+)"', txt):
            for g in m.group(1).split(","):
                if g not in all_g_in_db:
                    missing_from_db.add(g)
assert not missing_from_db, f"USFM references missing from GBL-EPV: {missing_from_db}"
con.close()

# --- PACKAGE ALL 5 DELIVERABLES ---
# 1. GBL-EPV_STAMP.dct.zip
gbl_zip_path = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"
with zipfile.ZipFile(gbl_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(out_twm, arcname=os.path.basename(out_twm))

# 2 & 3. USFM_Rahlfs_Deuterocanon_STAMP.zip & USFM_Swete_Deuterocanon_STAMP.zip
ra_zip_path = f"{OUT_BASE}/USFM_Rahlfs_Deuterocanon_{STAMP}.zip"
with zipfile.ZipFile(ra_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for fn in sorted(os.listdir(f"{OUT_BASE}/rahlfs")):
        if fn.endswith(".usfm"):
            new_fn = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{4}\.usfm$', f'_{STAMP}.usfm', fn)
            zf.write(f"{OUT_BASE}/rahlfs/{fn}", arcname=new_fn)

sw_zip_path = f"{OUT_BASE}/USFM_Swete_Deuterocanon_{STAMP}.zip"
with zipfile.ZipFile(sw_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for fn in sorted(os.listdir(f"{OUT_BASE}/swete")):
        if fn.endswith(".usfm"):
            new_fn = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{4}\.usfm$', f'_{STAMP}.usfm', fn)
            zf.write(f"{OUT_BASE}/swete/{fn}", arcname=new_fn)

# 4. deuterocanon_needs_review_resolved_STAMP.csv
audit_rows = json.load(open(f"{SCRATCH}/stage1_audit_rows.json", encoding="utf-8"))
audit_csv_path = f"{OUT_BASE}/deuterocanon_needs_review_resolved_{STAMP}.csv"
with open(audit_csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Edition", "Book", "Ref", "Category", "Surface", "Strong", "Morph", "Lemma", "Note"])
    w.writerows(audit_rows)

# 5. GBL-EPV_new_entries_log_STAMP.csv
log_csv_path = f"{OUT_BASE}/GBL-EPV_new_entries_log_{STAMP}.csv"
with open(log_csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Number", "Headword", "Transliteration", "Part of Speech", "Definition", "How Defined", "LSJ", "Rahlfs", "Swete", "Total Occurrences", "Books"])
    w.writerows(log_rows)

print("\n=== ALL 5 DELIVERABLES BUILT & VERIFIED ===")
print(f"  PRAGMA integrity_check:      {ic}")
print(f"  New entries inserted:        {inserted_count} (G15519-G15737)")
print(f"  Total G-numbers in GBL-EPV:  {len(all_g_in_db)}")
print(f"  USFM Strong's coverage:      100% (0 missing)")
print(f"  Copyright hygiene check:     PASS (0 banned author names)")
for p in [ra_zip_path, sw_zip_path, gbl_zip_path, out_twm, audit_csv_path, log_csv_path]:
    sz = os.path.getsize(p)
    print(f"  {p} ({sz:,} bytes)")
