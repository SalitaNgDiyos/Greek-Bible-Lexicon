import sqlite3, re, os, csv, shutil, zipfile, collections
from datetime import datetime

OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
SRC_DB = f"{OUT_BASE}/GBL-EPV_2026-11-20_1317.dct.twm"
CSV_IN = f"{OUT_BASE}/GBL-EPV_nouns_without_gender_2026-11-20_1321.csv"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
NEW_DB = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"
LOG_CSV = f"{OUT_BASE}/GBL-EPV_noun_genders_updated_{STAMP}.csv"

shutil.copy2(SRC_DB, NEW_DB)
con = sqlite3.connect(NEW_DB)
cur = con.cursor()

def rtf_to_plain(rtf_text):
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

def get_rtf(tid):
    d = cur.execute("SELECT data FROM content WHERE topic_id=?", (tid,)).fetchone()[0]
    return d.decode("latin1") if isinstance(d, bytes) else d

def set_rtf(tid, rtf_str):
    cur.execute("UPDATE content SET data=? WHERE topic_id=?", (rtf_str.encode("latin1"), tid))
    cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain(rtf_str).encode("utf-16-le"), tid))

# Scholarly overrides for non-LSJ / conflicting / non-noun items
OVERRIDES = {
    "G2035":  ("adjective", "numeral adjective (seven thousand)"),
    "G15160": ("adjective", "2-ending adjective (-ος, -ον) used substantivally"),
    "G11171": ("verb", "verb (LSJ: διαλαμβάνω, fut. -λήψομαι)"),
    "G5598":  ("noun neuter", "Greek letter Omega (τὸ Ὦ)"),
    "G8641":  ("noun neuter", "2nd-declension neuter (τὸ σίελον)"),
    "G9363":  ("noun masculine", "2nd/3rd-declension masculine (ὁ λυτρών)"),
    "G14068": ("noun feminine", "1st-declension feminine (ἡ ἐπιμιξία)"),
    "G14653": ("noun masculine", "2nd-declension masculine (LSJ: μόλυβδος, ὁ)"),
    "G14793": ("noun feminine", "1st-declension feminine (ἡ παθοκρατορία)"),
    "G14819": ("noun feminine", "1st-declension feminine (ἡ παντοδυναμία)"),
    "G15227": ("noun feminine", "3rd-declension feminine (ἡ συμπερίληψις)"),
}

rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8-sig")))
stats = collections.Counter()
log_rows = []

for r in rows:
    g = r["Number"]
    hw = r["Headword"]
    tid = cur.execute("SELECT id FROM topics WHERE subject=?", (g,)).fetchone()[0]
    txt = cur.execute("SELECT data FROM content_search WHERE topic_id=?", (tid,)).fetchone()[0].decode("utf-16-le")
    lsj_m = re.search(r"LSJ Definition:\s*[\r\n]+([^\r\n]+)", txt)
    lsj_line = lsj_m.group(1).strip() if lsj_m else ""

    new_pos = None
    source = ""

    if g in OVERRIDES:
        new_pos, source = OVERRIDES[g]
    else:
        # Check LSJ article first line for grammatical gender
        lsj_g = set()
        if lsj_line:
            if re.search(r"(?:^|[,;\s])ὁ(?:\s*,|\s*$|\s*\()", lsj_line):
                lsj_g.add("masculine")
            if re.search(r"(?:^|[,;\s])ἡ(?:\s*,|\s*$|\s*\()", lsj_line):
                lsj_g.add("feminine")
            if re.search(r"(?:^|[,;\s])τό(?:\s*,|\s*$|\s*\()", lsj_line):
                lsj_g.add("neuter")
            if ", ὁ, ἡ" in lsj_line or ", ὁ and ἡ" in lsj_line:
                lsj_g.update(["masculine", "feminine"])

        if lsj_g == {"masculine"}:
            new_pos, source = "noun masculine", "LSJ (ὁ)"
        elif lsj_g == {"feminine"}:
            new_pos, source = "noun feminine", "LSJ (ἡ)"
        elif lsj_g == {"neuter"}:
            new_pos, source = "noun neuter", "LSJ (τό)"
        elif lsj_g == {"masculine", "feminine"}:
            new_pos, source = "noun masculine or feminine", "LSJ (ὁ, ἡ)"
        elif lsj_g == {"masculine", "neuter"}:
            new_pos, source = "noun masculine or neuter", "LSJ (ὁ, τό)"
        elif lsj_g == {"masculine", "feminine", "neuter"}:
            new_pos, source = "noun masculine or feminine or neuter", "LSJ (ὁ, ἡ, τό)"
        elif r["Suggested_POS"].startswith("noun "):
            new_pos = r["Suggested_POS"]
            source = "Rahlfs/Swete morph"
        else:
            new_pos = "noun indeclinable"
            source = "indeclinable Hebrew/Aramaic transliteration"

    # Replace Part of Speech in child RTF
    rtf = get_rtf(tid)
    # Match both 'Part of Speech: ... noun' and older 'Part of speech: ... noun' patterns
    rtf_new, n_sub = re.subn(
        r'(Part of [Ss]peech:\s*(?:\\b0\s*)?\{\\(?:plain\\f0\\fs20|cf9)\s*)noun(\})',
        rf'\g<1>{new_pos}\2',
        rtf,
        count=1
    )
    if n_sub == 0:
        # Fallback: match {\plain\f0\fs20\b Part of Speech: }{\plain\f0\fs20 noun}\par
        rtf_new, n_sub = re.subn(
            r'(Part of [Ss]peech:[^}]*\}\{[^}]*?\s*)noun(\})',
            rf'\g<1>{new_pos}\2',
            rtf,
            count=1
        )
    assert n_sub == 1, f"Could not update POS in RTF for {g} ({hw}): {rtf[:400]}"
    set_rtf(tid, rtf_new)

    stats[new_pos] += 1
    log_rows.append([g, hw, "noun", new_pos, source])

# Update Appendix Section 7 (Known issues) & Section 9 (Revision history)
ap_rtf = get_rtf(24331)
m_pos = re.search(r'Part of speech: \}\{\\plain\\f0\\fs20 .*?\\par', ap_rtf)
assert m_pos, "Part of speech bullet not found in Appendix!"
new_pos_bullet = (
    "Part of speech: }{\\plain\\f0\\fs20 all 729 nouns that previously lacked a gender "
    "were updated (20 November 2026) using LSJ articles, morphological agreement, and "
    "noun indeclinable classification; 1,194 proper names are still not sub-tagged as person vs place.}\\par"
)
ap_rtf = ap_rtf.replace(m_pos.group(0), new_pos_bullet, 1)
ap_rtf = ap_rtf.replace(
    "appendix and number ranges updated.}",
    "appendix and number ranges updated; all 729 nouns without gender updated from LSJ and morphological scholarship.}"
)
set_rtf(24331, ap_rtf)

con.commit()

# Verify 0 remaining 'Part of Speech: noun' without gender
rem = []
for g, raw in cur.execute("SELECT t.subject, cs.data FROM topics t JOIN content_search cs ON cs.topic_id=t.id WHERE t.subject LIKE 'G%'"):
    if not re.fullmatch(r"G\d+", g):
        continue
    m = re.search(r"Part of Speech:\s*([^\r\n]+)", raw.decode("utf-16-le"))
    if m and m.group(1).strip() == "noun":
        rem.append(g)

ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
assert ic == "ok", f"integrity_check failed: {ic}"
assert not rem, f"Remaining genderless nouns: {rem}"
con.close()

with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=os.path.basename(NEW_DB))

with open(LOG_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Number", "Headword", "Old_POS", "New_POS", "Source"])
    w.writerows(log_rows)

print(f"DONE! Updated {len(log_rows)} entries. Remaining genderless nouns: {len(rem)}")
print("Breakdown of new Part of Speech labels:")
for k, v in stats.most_common():
    print(f"  {k:36s} : {v}")
print(f"PRAGMA integrity_check: {ic}")
print(f"DB:  {NEW_DB} ({os.path.getsize(NEW_DB):,} bytes)")
print(f"ZIP: {NEW_ZIP} ({os.path.getsize(NEW_ZIP):,} bytes)")
print(f"LOG: {LOG_CSV}")
