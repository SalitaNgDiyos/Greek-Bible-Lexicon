#!/usr/bin/env python3
# Copyright (C) 2026 Edmund Paulino Valdez
# License: AGPL-3.0-or-later
import os, re, sqlite3, sys, zipfile

SRC_ZIP = "GBL-EPV_2026-11-20_2123.dct.zip"
STAMP = "2026-11-21_1850"
NEW_DB = f"GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"GBL-EPV_{STAMP}.dct.zip"
GILL = {"G5721","G5724","G5726","G5733","G5735","G5736","G5737","G5741"}
MC = {"G5656","G5660","G5661","G5662","G5664","G5922","G6040"}
LSJ23 = {"G5674","G5681","G5762","G5781","G5809","G5823","G5827","G5847","G5855","G5857","G5872","G5879","G5911","G5917","G5959","G5972","G5973","G6001","G6004","G6006","G6007","G6018","G6128"}
ALLOW = {"G5627","G5649","G5763","G5777","G5794","G6102","G6104","G6122"}

def as_str(d): return d.decode("latin1") if isinstance(d, bytes) else (d or "")
def rtf_to_plain(s):
    t = re.sub(r'\\u(-?\d+)\s?', lambda m: chr(int(m.group(1)) & 0xFFFF), s)
    t = re.sub(r'\{\\\*\\fldinst[^}]*\}', '', t)
    t = re.sub(r'\{\\fonttbl.*?\{\\colortbl[^}]*\}\}', '', t, flags=re.S)
    t = t.replace(r'\par', '\r\n')
    t = re.sub(r'\\[a-zA-Z]+-?\d*\s?', '', t).replace('{', '').replace('}', '')
    return re.sub(r'[ \t]+', ' ', t).strip()

with zipfile.ZipFile(SRC_ZIP) as zf:
    src = [n for n in zf.namelist() if n.endswith(".dct.twm")][0]
    open(NEW_DB, "wb").write(zf.read(src))

con = sqlite3.connect(NEW_DB)
cur = con.cursor()
mod = set()
def set_rtf(tid, r):
    cur.execute("UPDATE content SET data=? WHERE topic_id=?", (r, tid))
    cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain(r).encode("utf-16-le"), tid))
    mod.add(tid)

s5687 = as_str(cur.execute("SELECT data FROM content WHERE topic_id=5713").fetchone()[0])
set_rtf(5713, "".join(l for l in s5687.splitlines(True) if "(TWOT)" not in l).replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b Online Bible Abridged BDB:}"))

for g in sorted(GILL):
    tid, d = cur.execute("SELECT t.id, c.data FROM topics t JOIN content c ON t.id=c.topic_id WHERE t.subject=?", (g,)).fetchone()
    set_rtf(tid, re.sub(r'\s*\\\{[a-z]+\\\}', '', as_str(d)).replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b John Gill:}"))

for g in sorted(MC):
    tid, d = cur.execute("SELECT t.id, c.data FROM topics t JOIN content c ON t.id=c.topic_id WHERE t.subject=?", (g,)).fetchone()
    set_rtf(tid, as_str(d).replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b McClintock & Strong:}"))

s25 = as_str(cur.execute("SELECT data FROM content WHERE topic_id=25").fetchone()[0]).replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b Thayer Definition:}", 1)
t25 = r"\pard\sb0\sa120\li720\fi-360 {\plain\f0\fs20 2. show affection for}\par"
set_rtf(25, s25.replace(t25, r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b LSJ Glosses:}\par" + "\n" + t25, 1))

for tid, subj, d in cur.execute("SELECT t.id, t.subject, c.data FROM topics t JOIN content c ON t.id=c.topic_id WHERE t.subject GLOB 'G[0-9]*'").fetchall():
    if tid in mod: continue
    m = re.match(r'^G(\d+)$', subj)
    if not m or int(m.group(1)) > 6134: continue
    s = as_str(d)
    if r"{\plain\f0\fs20\b Definition:}" not in s or subj in ALLOW: continue
    if int(m.group(1)) <= 5624:
        s = s.replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b Thayer Definition:}", 1)
    elif subj in LSJ23:
        s = s.replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b LSJ Definition:}", 1)
    else:
        dup = r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b Definition:}\par"
        s = s.replace(dup + "\n" + dup, dup).replace(r"{\plain\f0\fs20\b Definition:}", r"{\plain\f0\fs20\b Online Bible Abridged BDB:}")
    set_rtf(tid, s)

about = as_str(cur.execute("SELECT value FROM config WHERE name='about'").fetchone()[0])
about = about.replace(r"Thayer\rquote s Greek Definitions\b0\par", r"Thayer\rquote s Greek Definitions (Online Bible / Larry Pierce Introductory Note)\b0\par", 1)
about = about.replace(r"G5625\u8211 G13143 were added for Septuagint words.", r"G5625\u8211 G15737 were added for Septuagint and Deuterocanonical words.")
about = about.replace(r"Strong\rquote s Greek lookup (G1\endash G15518)", r"Strong\rquote s Greek lookup (G1\endash G15737)")
credit = (r"\par" + "\n" + r"\pard\nowidctlpar\sb80\sa120\b Sources & Licenses: \b0 "
    "Online Bible / Larry Pierce (Strong's/Thayer introductory note & abridged Thayer/BDB outlines); "
    "Thayer's Greek-English Lexicon (1889, public domain); Liddell-Scott-Jones (LSJ, 1940) via Perseus Digital Library TEI XML (CC BY-SA 3.0 US) and Liddell.dct; "
    "Brown-Driver-Briggs (uBDB, public domain); ISBE (1915, public domain); McClintock & Strong Cyclopedia & John Gill's Exposition (public domain); "
    "Textus Receptus (Stephanus 1550 / TRa) & Robinson-Pierpont Byzantine Textform (2018, public domain); SBLGNT (CC BY 4.0) & MorphGNT (CC BY-SA 3.0); "
    "CATSS / lxxmorph-rc (Rubio Terra), eliranwong/LXX-Rahlfs-1935 (CC BY-NC-SA 4.0 / CCAT non-commercial), eliranwong/LXX-Swete-1930 (GPL-3.0), "
    "sleeptillseven/LXX-Swete (CC BY-NC-SA 4.0), LXX Brenton+, and aruljohn/Bible-kjv. Original build/audit scripts by Edmund Valdez are licensed under AGPL-3.0-or-later." + r"\par" + "\n")
i = about.rfind("}")
cur.execute("UPDATE config SET value=? WHERE name='about'", (about[:i] + credit + about[i:],))
cur.execute("UPDATE config SET value=? WHERE name='version.date'", ("2026-11-21",))

ap = as_str(cur.execute("SELECT data FROM content WHERE topic_id=24331").fetchone()[0]).replace("revised 20 November 2026", "revised 21 November 2026")
ap = ap.replace(
    r"{\plain\f0\fs20 Definition labels keep their source: }{\plain\f0\fs20\b Thayer Definition}{\plain\f0\fs20 , }{\plain\f0\fs20\b LSJ Definition}{\plain\f0\fs20  (Liddell-Scott-Jones), }{\plain\f0\fs20\b BDB Definition}{\plain\f0\fs20  (Brown-Driver-Briggs), or plain }{\plain\f0\fs20\b Definition}{\plain\f0\fs20  for definitions written for this module.",
    r"{\plain\f0\fs20 Definition labels keep their source: }{\plain\f0\fs20\b Thayer Definition}{\plain\f0\fs20  (1889 unabridged and Online Bible abridged outlines), }{\plain\f0\fs20\b LSJ Definition}{\plain\f0\fs20  (Liddell-Scott-Jones), }{\plain\f0\fs20\b BDB Definition}{\plain\f0\fs20  (unabridged Brown-Driver-Briggs), }{\plain\f0\fs20\b Online Bible Abridged BDB}{\plain\f0\fs20 , }{\plain\f0\fs20\b McClintock & Strong}{\plain\f0\fs20 , }{\plain\f0\fs20\b John Gill}{\plain\f0\fs20 , or plain }{\plain\f0\fs20\b Definition}{\plain\f0\fs20  strictly for definitions written for this module.", 1)
ap = ap.replace("the Liddell-Scott-Jones text at perseus.tufts.edu (CC BY-SA) was used to compare hand-written definitions.",
    "the Perseus Digital Library TEI XML of Liddell-Scott-Jones (1940, CC BY-SA 3.0 US) underlies the 10,135+ LSJ Definition articles (via Liddell.dct) and was also used to verify hand-written definitions.", 1)
ap = ap.replace(r"{\plain\f0\fs20\b LSJ: }{\plain\f0\fs20 Liddell, Scott and Jones, }{\plain\f0\fs20\i A Greek-English Lexicon}{\plain\f0\fs20 .}\par",
    r"{\plain\f0\fs20\b LSJ: }{\plain\f0\fs20 Liddell, Scott and Jones, }{\plain\f0\fs20\i A Greek-English Lexicon}{\plain\f0\fs20  (1940), via the Perseus Digital Library TEI XML (CC BY-SA 3.0 US) and Liddell.dct (10,135+ articles).}\par" + "\n" + r"\pard\sb0\sa120\li360\fi-240 {\plain\f0\fs20 \u8226 \tab }{\plain\f0\fs20\b Online Bible: }{\plain\f0\fs20 Larry Pierce / Online Bible (Strong\u8217 s/Thayer introductory note and abridged Thayer and BDB outlines).}\par", 1)
ap = ap.replace(r"{\plain\f0\fs20\b BDB: }{\plain\f0\fs20 Brown, Driver and Briggs, }{\plain\f0\fs20\i A Hebrew and English Lexicon of the Old Testament}{\plain\f0\fs20 .}\par",
    r"{\plain\f0\fs20\b BDB: }{\plain\f0\fs20 Brown, Driver and Briggs, }{\plain\f0\fs20\i A Hebrew and English Lexicon of the Old Testament}{\plain\f0\fs20  (uBDB, public domain).}\par" + "\n" +
    r"\pard\sb0\sa120\li360\fi-240 {\plain\f0\fs20 \u8226 \tab }{\plain\f0\fs20\b ISBE (1915): }{\plain\f0\fs20 International Standard Bible Encyclopedia (public domain).}\par" + "\n" +
    r"\pard\sb0\sa120\li360\fi-240 {\plain\f0\fs20 \u8226 \tab }{\plain\f0\fs20\b McClintock & Strong: }{\plain\f0\fs20 Cyclopedia of Biblical, Theological, and Ecclesiastical Literature (public domain).}\par" + "\n" +
    r"\pard\sb0\sa120\li360\fi-240 {\plain\f0\fs20 \u8226 \tab }{\plain\f0\fs20\b John Gill: }{\plain\f0\fs20 Exposition of the Entire Bible (public domain).}\par", 1)
rev21 = "\n" + r"\pard\sb0\sa120\li0\fi0 {\plain\f0\fs20\b 21 November: }{\plain\f0\fs20 Attribution, cleanup, and open-license compliance update: removed stray TWOT-tagged line from G5687; stripped raw footnote markers from John Gill entries; separated blended LSJ glosses from Thayer in G25; relabeled misattributed plain Definition: entries; credited Online Bible / Larry Pierce in config.about and Perseus Digital Library (CC BY-SA 3.0 US) plus all upstream sources across Appendix \u167 8, README.md, and LICENSE.}\par" + "\n"
j = ap.rfind("}")
set_rtf(24331, ap[:j] + rev21 + ap[j:])
con.commit()
assert cur.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
con.close()
with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=NEW_DB)
os.remove(NEW_DB)
print("Built", NEW_ZIP)
