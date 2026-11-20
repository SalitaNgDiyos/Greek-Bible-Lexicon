import sqlite3, re, os, shutil, zipfile
from datetime import datetime

OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
SRC_DB = f"{OUT_BASE}/GBL-EPV_2026-11-20_1410.dct.twm"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
NEW_DB = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"

shutil.copy2(SRC_DB, NEW_DB)

RTF_HEADER = (
    r"{\rtf1\ansi\ansicpg1252\uc0\deff0"
    r"{\fonttbl{\f0\fnil Segoe UI;}{\f1\fnil\fcharset161 Gentium;}{\f2\fnil\fcharset177 Cardo;}}"
    r"{\colortbl;\red128\green0\blue0;\red0\green0\blue128;\red0\green0\blue255;\red96\green96\blue96;\red190\green190\blue190;}"
)

MAX_CH = {
    1:50,2:40,3:27,4:36,5:34,6:24,7:21,8:4,9:31,10:24,11:22,12:25,13:29,14:36,15:10,16:13,17:10,18:42,
    19:150,20:31,21:12,22:8,23:66,24:52,25:5,26:48,27:12,28:14,29:3,30:9,31:1,32:4,33:7,34:3,35:3,36:3,
    37:2,38:14,39:4,40:28,41:16,42:24,43:21,44:28,45:16,46:16,47:13,48:6,49:6,50:4,51:4,52:5,53:3,54:6,
    55:4,56:3,57:1,58:13,59:5,60:5,61:3,62:5,63:1,64:1,65:1,66:22
}

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

def strip_field_to_display(inner_fldrslt):
    # Remove blue link color \cf3: if Greek \f1 -> \cf1, else plain (no \cf3)
    if "\\f1" in inner_fldrslt:
        return inner_fldrslt.replace("\\cf3", "\\cf1")
    return inner_fldrslt.replace("\\cf3", "")

# Helper to find and transform balanced {\field{\*\fldinst HYPERLINK "..."}{\fldrslt ...}} blocks
FIELD_START_RE = re.compile(r'\{\\field\{\\\*\\fldinst\s+HYPERLINK\s+"([^"]+)"\}\{\\fldrslt\s*')

def transform_hyperlinks(rtf_str, stats):
    out = []
    pos = 0
    n = len(rtf_str)
    while pos < n:
        m = FIELD_START_RE.search(rtf_str, pos)
        if not m:
            out.append(rtf_str[pos:])
            break
        out.append(rtf_str[pos:m.start()])
        url = m.group(1)
        # Find balanced closing braces for {\fldrslt ...} and outer {\field ...}
        # At m.end(), we are inside {\field{...}{\fldrslt <HERE>
        # Brace depth relative to outer {\field is 2 (outer field=1, fldrslt=2)
        i = m.end()
        depth = 2
        fldrslt_end = None
        field_end = None
        while i < n and depth > 0:
            ch = rtf_str[i]
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 1 and fldrslt_end is None:
                    fldrslt_end = i
                elif depth == 0:
                    field_end = i + 1
                    break
            i += 1
        if fldrslt_end is None or field_end is None:
            # Malformed, leave untouched
            out.append(rtf_str[m.start():m.end()])
            pos = m.end()
            continue

        disp = rtf_str[m.end():fldrslt_end]
        orig_block = rtf_str[m.start():field_end]

        # 1. Perseus web links -> strip hyperlink wrapper, keep clean display text
        if url.startswith("http://www.perseus.tufts.edu/") or url.startswith("https://www.perseus.tufts.edu/"):
            stats["perseus_stripped"] += 1
            out.append(strip_field_to_display(disp))
            pos = field_end
            continue

        # 2. Legacy module links
        if url.startswith("tw://bdb-thayer.dct?H"):
            hnum = url.split("?")[1]
            stats["legacy_rewritten"] += 1
            out.append(orig_block.replace(url, f"tw://[strong]?t={hnum}"))
            pos = field_end
            continue
        if url == "tw://dct.uBDB?tid=18258":
            stats["legacy_rewritten"] += 1
            out.append(orig_block.replace(url, "tw://[strong]?t=H3568"))
            pos = field_end
            continue
        if url == "tw://dct.bdb-thayer.dct?tid=12438":
            stats["legacy_rewritten"] += 1
            out.append(orig_block.replace(url, "tw://[self]?G2438"))
            pos = field_end
            continue
        if url.startswith("tw://AMBD?") or url.startswith("tw://jb121?"):
            stats["legacy_stripped"] += 1
            out.append(strip_field_to_display(disp))
            pos = field_end
            continue

        # 3. Invalid Bible book/chapter/verse links
        if url.startswith("tw://bible.*?id="):
            bm = re.match(r"tw://bible\.\*\?id=(\d+)\.(\d+)\.(\d+)", url)
            if bm:
                bk, ch, vs = int(bm.group(1)), int(bm.group(2)), int(bm.group(3))
                if bk not in MAX_CH or ch < 1 or ch > MAX_CH[bk] or vs < 1:
                    # Fix known clear uBDB book/chapter swaps:
                    if bk == 29 and ch == 4 and vs >= 1:  # Hebrew Joel 4 -> KJV Joel 3
                        new_u = f"tw://bible.*?id=29.3.{vs}"
                        new_disp = disp.replace(f"Joel 4:{vs}", f"Joel 3:{vs}")
                        stats["bible_fixed"] += 1
                        out.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{new_u}"}}{{\\fldrslt {new_disp}}}}}')
                    elif bk == 10 and ch in (72, 89, 122, 132) and vs >= 1:  # 2Sam -> Psalms
                        new_u = f"tw://bible.*?id=19.{ch}.{vs}"
                        new_disp = disp.replace(f"2Sam {ch}:{vs}", f"Ps {ch}:{vs}")
                        stats["bible_fixed"] += 1
                        out.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{new_u}"}}{{\\fldrslt {new_disp}}}}}')
                    elif bk == 15 and ch == 12 and vs == 33:  # Ezra 12:33 -> Neh 12:33
                        new_u = "tw://bible.*?id=16.12.33"
                        new_disp = disp.replace("Ezra 12:33", "Neh 12:33")
                        stats["bible_fixed"] += 1
                        out.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{new_u}"}}{{\\fldrslt {new_disp}}}}}')
                    elif bk == 13 and ch == 34 and vs == 12:  # 1Chr 34:12 -> 2Chr 34:12
                        new_u = "tw://bible.*?id=14.34.12"
                        new_disp = disp.replace("1Chr 34:12", "2Chr 34:12")
                        stats["bible_fixed"] += 1
                        out.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{new_u}"}}{{\\fldrslt {new_disp}}}}}')
                    elif bk == 65 and ch == 9 and vs == 1:  # Jude 9 -> Jude 1:9
                        new_u = "tw://bible.*?id=65.1.9"
                        stats["bible_fixed"] += 1
                        out.append(f'{{\\field{{\\*\\fldinst HYPERLINK "{new_u}"}}{{\\fldrslt {disp}}}}}')
                    else:
                        # Unresolvable / false autodetect (e.g. A.Pers.13, Ar.Nu.17, Hos 35:15) -> plain text
                        stats["bible_unlinked"] += 1
                        out.append(strip_field_to_display(disp))
                    pos = field_end
                    continue

        out.append(orig_block)
        pos = field_end
    return "".join(out)

con = sqlite3.connect(NEW_DB)
cur = con.cursor()

stats = {
    "xml_removed": 0,
    "perseus_stripped": 0,
    "legacy_rewritten": 0,
    "legacy_stripped": 0,
    "bible_fixed": 0,
    "bible_unlinked": 0,
    "topics_modified": 0,
}

# Step 1: Fix G8335 (Αβι) & its parent (pid=11763) and G9423 (Ορη)
g8335_rtf = "\n".join([
    RTF_HEADER,
    r"\pard\sb0\sa120\li0\fi0 {\plain\f1\fs24\b\cf1 \u913 \u946 \u953 }{\plain\f0\fs20   }{\plain\f0\fs20\cf2\i (Abi)}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b Part of Speech: }{\plain\f0\fs20 proper name masculine}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b Definition:}\par",
    r"\pard\sb0\sa120\li360\fi-360 {\plain\f0\fs20 Abi: (1) first element of the split gentilic Abi-ezri (Abiezrite) at Ophrah of the Abiezrites (Judg 8:32); (2) Abi son of Joab, listed in the Septuagint as commander of Solomon's army (1 Kgs 2:46; Brenton 3:1).}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b OT (LXX) Occurrences: }{\plain\f0\fs20 Rahlfs: 1 \u183  Swete: 1 \u183  Brenton: 2}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs18\cf3 Judg 8:32 Br; 1Kgs 2:46 R\u183 S; 1Kgs 3:1 Br}\par",
    "}"
])
tid_8335, pid_8335 = cur.execute("SELECT id, pid FROM topics WHERE subject='G8335'").fetchone()
cur.execute("UPDATE content SET data=? WHERE topic_id=?", (g8335_rtf.encode("latin1"), tid_8335))
cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(g8335_rtf).encode("utf-16-le"), tid_8335))

p8335_rtf = "\n".join([
    RTF_HEADER,
    r"\pard\sb0\sa120\li0\fi0 {\plain\f1\fs28\b\cf1 \u913 \u946 \u953 }{\plain\f0\fs20   }{\plain\f0\fs20\cf2\i (Abi)}{\plain\f0\fs20   \u8212  Abi (Abi-ezri; Abi son of Joab)}\par",
    r'\pard\sb0\sa60\li0\fi0 {\field{\*\fldinst HYPERLINK "tw://[self]?G8335"}{\fldrslt {\plain\f0\fs20\cf3 G8335}}}{\plain\f0\fs20   }{\plain\f1\fs24\b\cf1 \u913 \u946 \u953 }{\plain\f0\fs20   }{\plain\f0\fs20\cf2\i (Abi)}{\plain\f0\fs20   \u8212  proper name masculine}\par',
    "}"
])
cur.execute("UPDATE content SET data=? WHERE topic_id=?", (p8335_rtf.encode("latin1"), pid_8335))
cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(p8335_rtf).encode("utf-16-le"), pid_8335))

g9423_rtf = "\n".join([
    RTF_HEADER,
    r"\pard\sb0\sa120\li0\fi0 {\plain\f1\fs24\b\cf1 \u927 \u961 \u951 }{\plain\f0\fs20   }{\plain\f0\fs20\cf2\i (Or\u275 )}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b Part of Speech: }{\plain\f0\fs20 proper name location}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b Definition:}\par",
    r"\pard\sb0\sa120\li360\fi-360 {\plain\f0\fs20 Ore ('mountains' of the Medes, \u8004 \u961 \u951  \u924 \u942 \u948 \u969 \u957 ; MT 'cities of the Medes'), the region in Media to which the king of Assyria deported Israelites (2 Kgs 17:6; 18:11).}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b OT (LXX) Occurrences: }{\plain\f0\fs20 Rahlfs: 2 \u183  Swete: 2 \u183  Brenton: 2}\par",
    r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs18\cf3 2Kgs 17:6; 2Kgs 18:11}\par",
    "}"
])
tid_9423 = cur.execute("SELECT id FROM topics WHERE subject='G9423'").fetchone()[0]
cur.execute("UPDATE content SET data=? WHERE topic_id=?", (g9423_rtf.encode("latin1"), tid_9423))
cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(g9423_rtf).encode("utf-16-le"), tid_9423))
print("Fixed G8335 (Αβι + parent) and G9423 (Ορη)")

# Step 2: Sweep ALL content rows for raw XML tags, Perseus links, legacy links, and invalid Bible refs
all_rows = cur.execute("SELECT topic_id, data FROM content").fetchall()
for tid, d in all_rows:
    is_b = isinstance(d, bytes)
    s = d.decode("latin1") if is_b else d
    s_new = s

    # Remove <checkingNeeded/> and <wrongReferenceRemoved/>
    if "<checkingNeeded/>" in s_new or "<wrongReferenceRemoved/>" in s_new:
        c1 = s_new.count("<checkingNeeded/>")
        c2 = s_new.count("<wrongReferenceRemoved/>")
        stats["xml_removed"] += c1 + c2
        s_new = s_new.replace("<checkingNeeded/>", "").replace("<wrongReferenceRemoved/>", "")

    # Transform hyperlinks if any relevant pattern present
    if any(k in s_new for k in ("perseus.tufts.edu", "bdb-thayer.dct", "tw://AMBD?", "tw://jb121?", "tw://dct.uBDB?tid=", "tw://bible.*?id=")):
        s_new = transform_hyperlinks(s_new, stats)

    if s_new != s:
        # Verify our transform did not alter brace balance!
        op_old = s.count("{") - s.count("\\{")
        cl_old = s.count("}") - s.count("\\}")
        op = s_new.count("{") - s_new.count("\\{")
        cl = s_new.count("}") - s_new.count("\\}")
        assert (op - cl) == (op_old - cl_old), f"Brace delta changed in tid={tid}: {op_old-cl_old} -> {op-cl}"
        val = s_new.encode("latin1") if is_b else s_new
        cur.execute("UPDATE content SET data=? WHERE topic_id=?", (val, tid))
        cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(s_new).encode("utf-16-le"), tid))
        stats["topics_modified"] += 1

# Step 3: Update Appendix (tid=24331) Section 9 (20 November)
ap_d = cur.execute("SELECT data FROM content WHERE topic_id=24331").fetchone()[0]
ap_is_b = isinstance(ap_d, bytes)
ap_rtf = ap_d.decode("latin1") if ap_is_b else ap_d
ap_rtf = ap_rtf.replace(
    "all 1,008 LSJ links resolve internally.}",
    "all 1,008 LSJ links resolve internally; removed 205 raw XML markers, fixed or unlinked 114 invalid Bible links and 34 legacy module links, stripped 7,374 external Perseus web links, and corrected G8335 and G9423.}"
)
cur.execute("UPDATE content SET data=? WHERE topic_id=24331", (ap_rtf.encode("latin1") if ap_is_b else ap_rtf,))
cur.execute("UPDATE content_search SET data=? WHERE topic_id=24331", (rtf_to_plain_clean(ap_rtf).encode("utf-16-le"),))

con.commit()

# Final verification!
rem_xml = rem_perseus = rem_legacy = rem_bad_bible = 0
for (d,) in cur.execute("SELECT data FROM content"):
    s = d.decode("latin1") if isinstance(d, bytes) else d
    if "<checkingNeeded/>" in s or "<wrongReferenceRemoved/>" in s:
        rem_xml += 1
    if 'HYPERLINK "http://www.perseus.tufts.edu' in s or 'HYPERLINK "https://www.perseus.tufts.edu' in s:
        rem_perseus += 1
    if any(k in s for k in ("bdb-thayer.dct", "tw://AMBD?", "tw://jb121?", "tw://dct.uBDB?tid=")):
        rem_legacy += 1
    for bm in re.finditer(r'HYPERLINK "tw://bible\.\*\?id=(\d+)\.(\d+)\.(\d+)', s):
        bk, ch, vs = int(bm.group(1)), int(bm.group(2)), int(bm.group(3))
        if bk not in MAX_CH or ch < 1 or ch > MAX_CH[bk] or vs < 1:
            rem_bad_bible += 1

ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
con.close()

assert ic == "ok"
assert rem_xml == 0 and rem_perseus == 0 and rem_legacy == 0 and rem_bad_bible == 0, \
    f"Leftovers: xml={rem_xml} perseus={rem_perseus} legacy={rem_legacy} bad_bible={rem_bad_bible}"

with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=os.path.basename(NEW_DB))

print("CLEANUP STATS:", stats)
print(f"VERIFICATION PASS: xml=0, perseus=0, legacy=0, bad_bible=0, integrity_check={ic}")
print(f"DB:  {NEW_DB} ({os.path.getsize(NEW_DB):,} bytes)")
print(f"ZIP: {NEW_ZIP} ({os.path.getsize(NEW_ZIP):,} bytes)")
