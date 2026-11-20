import sqlite3, re, os, shutil, zipfile
from datetime import datetime

OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
SRC_DB = f"{OUT_BASE}/GBL-EPV_2026-11-20_1234.dct.twm"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
NEW_DB = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"

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
    plain = rtf_to_plain(rtf_str)
    cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (plain.encode("utf-16-le"), tid))

# 1. Fix parent short meanings for G9423 (Ορη, pid=14613) and G10991 (Ηρων, pid=17981)
for g, short_gloss in [
    ("G9423", "Habor / mountains of the Medes (2 Kgs 17:6; 18:11)"),
    ("G10991", "Addon, a place in Babylonia from which exiles returned (Neh 7:61)"),
]:
    pid = cur.execute("SELECT pid FROM topics WHERE subject=?", (g,)).fetchone()[0]
    prtf = get_rtf(pid)
    first_par, rest = prtf.split("\\par", 1)
    if "\\u8212" not in first_par and "\\endash" not in first_par:
        prtf_new = first_par + f"{{\\plain\\f0\\fs20   \\u8212  {short_gloss}}}\\par" + rest
        set_rtf(pid, prtf_new)
        print(f"Updated parent short meaning for {g} (pid={pid})")

# 2. Update Start here (tid=24351)
sh_rtf = get_rtf(24351)
sh_rtf_new = sh_rtf.replace("G15518", "G15737")
assert sh_rtf_new != sh_rtf, "Start here G15518 not found!"
set_rtf(24351, sh_rtf_new)
print("Updated Start here (tid=24351): G5625-G15737")

# 3. Update Appendix – Notes on this edition (tid=24331)
ap_rtf = get_rtf(24331)
ap_rtf_new = ap_rtf.replace("revised 22 October 2026", "revised 20 November 2026")
ap_rtf_new = ap_rtf_new.replace("G13150 to G15518", "G13150 to G15737")
m_sm = re.search(r'Short meanings: \}\{\\plain\\f0\\fs20 .*?\\par', ap_rtf_new)
assert m_sm, "Short meanings RTF run not found!"
new_sm = (
    "Short meanings: }{\\plain\\f0\\fs20 the two lemma pages that previously lacked a short meaning "
    "(G9423, G10991) have been updated (20 November 2026); all lemma pages now display a short gloss.}\\par"
)
ap_rtf_new = ap_rtf_new.replace(m_sm.group(0), new_sm, 1)

# Append 20 November revision history entry before closing '}'
rev_20 = (
    "\n\\pard\\sb0\\sa120\\li0\\fi0 {\\plain\\f0\\fs20\\b 20 November: }{\\plain\\f0\\fs20 "
    "219 new entries, G15519 to G15737, completing vocabulary and proper names across both the Rahlfs and Swete "
    "deuterocanonical texts (with contextual proper-name definitions, LSJ entries, and Rahlfs/Swete occurrence counts); "
    "parent short meanings added for G9423 and G10991; appendix and number ranges updated.}\\par\n"
)
idx_close = ap_rtf_new.rfind("}")
ap_rtf_new = ap_rtf_new[:idx_close] + rev_20 + ap_rtf_new[idx_close:]
set_rtf(24331, ap_rtf_new)
print("Updated Appendix (tid=24331)")

con.commit()
ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
assert ic == "ok", f"integrity_check failed: {ic}"

# Verify brace balance on all modified topics
for tid in (24331, 24351, 14613, 17981):
    r = get_rtf(tid)
    op = r.count("{") - r.count("\\{")
    cl = r.count("}") - r.count("\\}")
    assert op == cl, f"Unbalanced braces in tid={tid}: {op} vs {cl}"
print("Brace balance check: PASS (all 4 modified topics balanced)")
con.close()

with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=os.path.basename(NEW_DB))

print(f"DONE! integrity_check={ic}")
print(f"  DB:  {NEW_DB} ({os.path.getsize(NEW_DB):,} bytes)")
print(f"  ZIP: {NEW_ZIP} ({os.path.getsize(NEW_ZIP):,} bytes)")
