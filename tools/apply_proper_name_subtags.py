import sqlite3, re, os, csv, shutil, zipfile, collections
from datetime import datetime

OUT_BASE = "/home/eddie/.gemini/antigravity/scratch/SalitaNgDiyos/deuterocanon"
SRC_DB = f"{OUT_BASE}/GBL-EPV_2026-11-20_1326.dct.twm"
CSV_IN = f"{OUT_BASE}/GBL-EPV_proper_names_unclassified_2026-11-20_1347.csv"
STAMP = datetime.now().strftime("%Y-%m-%d_%H%M")
NEW_DB = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.twm"
NEW_ZIP = f"{OUT_BASE}/GBL-EPV_{STAMP}.dct.zip"
LOG_CSV = f"{OUT_BASE}/GBL-EPV_proper_names_subtagged_{STAMP}.csv"

shutil.copy2(SRC_DB, NEW_DB)

def collect_deut_genders():
    genders = collections.defaultdict(collections.Counter)
    for folder, prefix in [(f"{OUT_BASE}/rahlfs", "Packard:"), (f"{OUT_BASE}/swete", "Robinson:")]:
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith(".usfm"): continue
            txt = open(f"{folder}/{fn}", encoding="utf-8").read()
            for w, a in re.findall(r'\\w\s+([^|]+)\|([^\\]+)\\w\*', txt):
                ms = re.search(r'strong="([^"]+)"', a)
                mm = re.search(r'x-morph="([^"]+)"', a)
                if not (ms and mm): continue
                code = mm.group(1).replace(prefix, "")
                mg = re.search(r'^[NA][A-Z0-9]*-[NGDAV][SPD]([MFN])', code)
                if mg:
                    for g in ms.group(1).split(","):
                        genders[g][mg.group(1)] += 1
    return genders

deut_g = collect_deut_genders()

# Hand-verified verse-context overrides for the 180 items that lacked automatic keyword triggers
MANUAL_180 = {
    "G5723": ("proper name location", "Gen 10:13 Naphtuhim (Lower Egypt)"),
    "G5764": ("proper name masculine", "Gen 11:26 Abram (Abraham)"),
    "G5885": ("noun indeclinable", "Gen 22:13 transliterated Hebrew sebakh (thicket)"),
    "G7317": ("proper name masculine", "Num 26:24 Jashub, son of Issachar"),
    "G7318": ("proper name masculine", "Num 26:24 Jashubite clan"),
    "G7383": ("proper name masculine", "Num 31:2 Midianites"),
    "G7428": ("proper name location", "Num 33:19; Judg 20:45 Rimmon-perez / rock of Rimmon"),
    "G7469": ("proper name masculine", "Num 34:23 Hanniel son of Ephod"),
    "G7512": ("proper name masculine", "Deut 2:20 Ammonites"),
    "G7515": ("proper name masculine", "Deut 2:23 Cappadocians"),
    "G7561": ("proper name location", "Deut 10:6 Moserah (camp where Aaron died)"),
    "G7625": ("proper name feminine", "Deut 22:19 Israelite woman (Ἰσραηλῖτις)"),
    "G7976": ("proper name location", "Josh 15:59 Peor (town in Judah)"),
    "G8022": ("proper name location", "Josh 17:11 Dor (coastal city)"),
    "G8071": ("proper name location", "Josh 19:7 En-rimmon (town in Simeon)"),
    "G8084": ("proper name location", "Josh 19:13 Rimmon-methoar (Zebulun boundary town)"),
    "G8202": ("proper name location", "Judg 1:10 Kiriath-arba (Hebron)"),
    "G8272": ("proper name masculine", "Judg 5:5 Eloi (Hebrew divine title)"),
    "G8318": ("proper name location", "Judg 7:24 Beth-barah (Jordan crossing)"),
    "G8350": ("proper name location", "Judg 9:37 Meonenim (soothsayers' oak near Shechem)"),
    "G8368": ("proper name location", "Judg 11:33 Abel-cheramim (place in Ammon)"),
    "G8374": ("proper name masculine", "Judg 12:11 Elon the Zebulonite"),
    "G8383": ("proper name masculine", "Judg 13:5 Nazirite (Samson)"),
    "G8479": ("proper name masculine", "1 Sam 1:11 Adonai (Lord)"),
    "G8498": ("proper name location", "1 Sam 4:1 Ebenezer (encampment)"),
    "G8501": ("proper name masculine", "1 Sam 4:21 Ichabod, son of Phinehas"),
    "G8546": ("proper name location", "1 Sam 13:17 Ophrah (town in Benjamin)"),
    "G8577": ("noun indeclinable", "1 Sam 15:3 transliterated Hebrew cherem"),
    "G8592": ("proper name masculine", "1 Sam 16:18 Jesse the Bethlehemite"),
    "G8593": ("proper name location", "1 Sam 17:1 Ephes-dammim (encampment)"),
    "G8618": ("proper name masculine", "1 Sam 17:58 Jesse the Bethlehemite"),
    "G8620": ("proper name masculine", "1 Sam 18:19 Adriel the Meholathite"),
    "G8656": ("proper name location", "1 Sam 23:19 strongholds near Ziph"),
    "G8662": ("proper name location", "1 Sam 24:2 rocks of the wild goats in En-gedi"),
    "G8688": ("proper name feminine", "1 Sam 27:3 Ahinoam the Jezreelitess"),
    "G8690": ("proper name masculine", "1 Sam 27:8 Geshurites/Girzites"),
    "G8790": ("proper name masculine", "2 Sam 6:2 Cherubim"),
    "G8856": ("proper name location", "2 Sam 13:37 land in Geshur"),
    "G8864": ("proper name masculine", "2 Sam 15:12 Ahithophel the Gilonite"),
    "G8865": ("proper name masculine", "2 Sam 15:18 Pelethites (David's bodyguard)"),
    "G8872": ("proper name masculine", "2 Sam 15:22 Ittai the Gittite"),
    "G8896": ("noun indeclinable", "2 Sam 17:29 transliterated Hebrew shephoth (cheese)"),
    "G8897": ("proper name masculine", "2 Sam 18:2 Ittai the Gittite"),
    "G8910": ("proper name masculine", "2 Sam 20:7 Cherethites (David's bodyguard)"),
    "G8916": ("proper name location", "2 Sam 20:15 Abel of Beth-maacah"),
    "G8938": ("proper name masculine", "2 Sam 21:18 Sibbecai the Hushathite"),
    "G9013": ("proper name location", "2 Sam 24:6 Tahtim-hodshi (land visited in census)"),
    "G9014": ("proper name location", "2 Sam 24:6 Tahtim-hodshi (land visited in census)"),
    "G9021": ("proper name feminine", "1 Kgs 1:3 Abishag the Shunammite"),
    "G9022": ("proper name masculine", "1 Kgs 1:5 Adonijah, son of David"),
    "G9024": ("proper name location", "1 Kgs 1:9 stone of Zoheleth near En-rogel"),
    "G9042": ("proper name location", "1 Kgs 2:46 Raphia (border town toward Gaza)"),
    "G9058": ("proper name masculine", "1 Kgs 4:6 Eliak, steward of Solomon"),
    "G9081": ("proper name location", "1 Kgs 4:13 Ramoth-gilead"),
    "G9094": ("proper name masculine", "1 Kgs 4:31 Ethan the Ezrahite"),
    "G9099": ("proper name location", "1 Kgs 4:34 Mergab/Gezer"),
    "G9172": ("proper name masculine", "1 Kgs 10:29 Hittites"),
    "G9242": ("proper name masculine", "1 Kgs 16:34 Hiel the Bethelite"),
    "G9278": ("proper name masculine", "1 Kgs 21:7 Naboth the Jezreelite"),
    "G9280": ("proper name masculine", "1 Kgs 22:8 Imlah, father of Micaiah"),
    "G9322": ("proper name masculine", "2 Kgs 5:18 Rimmon (Syrian deity)"),
    "G9349": ("proper name masculine", "2 Kgs 9:16 Arameans/Syrians"),
    "G9354": ("proper name location", "2 Kgs 9:27 Beth-gan (garden house)"),
    "G9357": ("proper name location", "2 Kgs 10:12 Beth-eked of the shepherds"),
    "G9412": ("proper name location", "2 Kgs 15:29 Abel-beth-maacah"),
    "G9433": ("proper name feminine", "2 Kgs 17:30 Ashima (deity of Hamath)"),
    "G9435": ("proper name masculine", "2 Kgs 17:31 Tartak (deity of the Avvites)"),
    "G9437": ("proper name masculine", "2 Kgs 17:31 Anammelech (deity of Sepharvaim)"),
    "G9636": ("proper name masculine", "1 Chr 2:44 Jorkoam, Calebite descendant"),
    "G9643": ("proper name masculine", "1 Chr 2:48 Tirhanah, son of Caleb"),
    "G9650": ("proper name masculine", "1 Chr 2:51 Hareph, Calebite father of Beth-gader"),
    "G9664": ("proper name masculine", "1 Chr 2:54 Manahethites (clan of Judah)"),
    "G9673": ("proper name masculine", "1 Chr 3:2 Adonijah, son of David"),
    "G9728": ("proper name masculine", "1 Chr 4:4 Shuhah, descendant of Judah"),
    "G9802": ("proper name location", "1 Chr 4:32 Rimmon (town of Simeon)"),
    "G9827": ("proper name masculine", "1 Chr 5:6 Tiglath-pileser, king of Assyria"),
    "G9831": ("proper name masculine", "1 Chr 5:12 Jaanai, Gadite chief"),
    "G9852": ("proper name masculine", "1 Chr 5:26 Pul, king of Assyria"),
    "G10059": ("proper name masculine", "1 Chr 8:37 Azel, descendant of Jonathan"),
    "G10089": ("proper name location", "Amos 6:2 Hamath-rabbah (city)"),
    "G10107": ("proper name masculine", "Amos 5:26 Raiphan/Rephan (star-god)"),
    "G10119": ("proper name masculine", "1 Chr 11:27 Helez the Pelonite"),
    "G10133": ("proper name location", "1 Chr 11:32 brooks/wadis of Gaash"),
    "G10135": ("proper name masculine", "1 Chr 11:33 Azmaveth the Baharumite"),
    "G10143": ("proper name masculine", "1 Chr 11:36 Hepher the Mecherathite"),
    "G10144": ("proper name masculine", "1 Chr 11:36 Ahijah the Pelonite"),
    "G10167": ("proper name masculine", "1 Chr 11:46 Eliel the Mahavite"),
    "G10186": ("proper name masculine", "1 Chr 12:5 Shephatiah the Haruphite"),
    "G10187": ("proper name masculine", "1 Chr 12:6 Isshiah the Korahite"),
    "G10260": ("proper name masculine", "1 Chr 20:4 Sibbecai the Hushathite"),
    "G10382": ("proper name masculine", "1 Chr 27:30 Jehdeiah the Meronothite"),
    "G10427": ("proper name location", "2 Chr 8:3 Hamath-zobah (city)"),
    "G10465": ("proper name masculine", "2 Chr 18:7 Imla, father of Micaiah"),
    "G10685": ("proper name masculine", "Ezra 4:7 Artaxerxes, king of Persia"),
    "G10842": ("proper name masculine", "Neh 2:10 Sanballat the Horonite"),
    "G11100": ("proper name masculine", "Neh 13:28 Sanballat the Horonite"),
    "G11183": ("proper name masculine", "Esth 4:5 Hatach (Achrathaeus), eunuch"),
    "G11209": ("proper name masculine", "Esth 7:9 Harbona (Bugathan), eunuch"),
    "G11285": ("proper name masculine", "Job 4:1 Eliphaz the Temanite"),
    "G11329": ("proper name masculine", "Job 8:1 Bildad the Shuhite"),
    "G11340": ("proper name feminine", "Job 9:9 Pleiades (ἡ Πλειάς)"),
    "G11658": ("proper name masculine", "Ps 54:1 Ziphites"),
    "G12278": ("proper name masculine", "Isa 37:38 Nisroch (Assyrian god)"),
    "G12280": ("proper name location", "Isa 37:38 Armenia (country)"),
    "G12468": ("proper name location", "Jer 31:40 fields outside Jerusalem toward Kidron"),
    "G12508": ("proper name masculine", "Jer 40:8 Jezaniah the Maacathite"),
    "G12524": ("noun indeclinable", "Jer 46:17 transliterated Hebrew shaon"),
    "G12715": ("proper name masculine", "Ezek 27:4 builders/rulers of Tyre"),
    "G12724": ("proper name masculine", "Ezek 27:12 Carthaginians"),
    "G12792": ("proper name location", "Ezek 47:16 Sibraim (border city)"),
    "G12811": ("proper name masculine", "Dan 1:11 Melzar (Amelsad), steward"),
    "G12882": ("proper name masculine", "Hos 2:13 Baalim"),
    "G12889": ("proper name masculine", "Hos 5:13 King Jareb of Assyria"),
    "G12915": ("proper name masculine", "Amos 1:1 herdsmen (Nakadim) of Tekoa"),
    "G12921": ("proper name masculine", "1 Sam 14:48 Swete proper name"),
    "G12924": ("proper name masculine", "1 Chr 4:19 genealogy of Judah"),
    "G12925": ("proper name masculine", "1 Chr 4:19 genealogy of Judah"),
    "G12926": ("proper name masculine", "1 Chr 4:19 genealogy of Judah"),
    "G12927": ("proper name masculine", "1 Chr 4:19 genealogy of Judah"),
    "G12946": ("proper name masculine", "Gen 46:21 Huppim, son of Benjamin"),
    "G12962": ("proper name location", "Josh 13:27 Beth-haram (city in Gad)"),
    "G12964": ("proper name location", "Josh 15:11 Shikkeron (border town of Judah)"),
    "G12966": ("proper name location", "Josh 21:22 Kibzaim (Levitical city in Ephraim)"),
    "G12967": ("proper name location", "Josh 21:35 Dimnah (Levitical city in Zebulun)"),
    "G12986": ("proper name location", "Judg 7:22 Beth-shittah (town)"),
    "G12993": ("proper name location", "Judg 11:33 Minnith (Ammonite town)"),
    "G12995": ("proper name location", "Judg 12:1 Zaphon (town East of Jordan)"),
    "G13011": ("proper name masculine", "2 Sam 15:32 Hushai the Archite"),
    "G13012": ("proper name masculine", "2 Sam 23:9 David's mighty man"),
    "G13013": ("proper name masculine", "2 Sam 23:9 David's mighty man"),
    "G13014": ("proper name masculine", "2 Sam 23:25 Elika the Harodite"),
    "G13015": ("proper name masculine", "2 Sam 23:29 Heled son of Baanah"),
    "G13016": ("proper name masculine", "2 Sam 23:32 sons of Jashen"),
    "G13017": ("proper name masculine", "2 Sam 23:33 Ahiam son of Sharar"),
    "G13018": ("proper name masculine", "2 Sam 23:35 Paarai the Arbite"),
    "G13019": ("proper name masculine", "2 Sam 23:35 Paarai the Arbite"),
    "G13021": ("proper name location", "1 Kgs 4:9 Solomon's 2nd administrative district"),
    "G13022": ("proper name location", "1 Kgs 4:10 Solomon's 3rd administrative district"),
    "G13023": ("proper name location", "1 Kgs 4:10 Solomon's 3rd administrative district"),
    "G13024": ("proper name location", "1 Kgs 4:10 Solomon's 3rd administrative district"),
    "G13025": ("proper name location", "1 Kgs 4:12 Solomon's 5th administrative district"),
    "G13026": ("proper name location", "1 Kgs 4:12 Solomon's 5th administrative district"),
    "G13029": ("proper name location", "1 Kgs 7:33 Rahlfs place/technical term"),
    "G13035": ("proper name masculine", "1 Chr 2:31; 11:41 Ahlai"),
    "G13036": ("proper name masculine", "1 Chr 2:55 Shimeathites (scribal family)"),
    "G13037": ("proper name masculine", "1 Chr 4:12 men of Recah"),
    "G13038": ("proper name masculine", "1 Chr 4:16 sons of Jehallelel"),
    "G13040": ("proper name masculine", "1 Chr 4:19 genealogy of Judah"),
    "G13041": ("proper name masculine", "1 Chr 6:34 Elidad/Eldad in Levitical genealogy"),
    "G13042": ("proper name location", "1 Chr 6:59 Ashan (priestly city in Judah/Simeon)"),
    "G13044": ("proper name masculine", "1 Chr 7:13 Jezer, son of Naphtali"),
    "G13045": ("proper name masculine", "1 Chr 7:20 Tahath, descendant of Ephraim"),
    "G13047": ("proper name feminine", "1 Chr 8:8, 11 Hushim, wife of Shaharaim"),
    "G13048": ("proper name masculine", "1 Chr 9:4 Uthai son of Ammihud"),
    "G13050": ("proper name masculine", "1 Chr 11:36 Hepher the Mecherathite"),
    "G13052": ("proper name masculine", "1 Chr 24:26 Beno, son of Merari"),
    "G13053": ("proper name masculine", "1 Chr 27:30 Obil the Ishmaelite"),
    "G13056": ("proper name location", "2 Chr 28:18 Gederoth (town in Judah)"),
    "G13059": ("proper name masculine", "Ezra 4:9 Elamites"),
    "G13061": ("proper name masculine", "Ezra 10:43 Jaddu, son of Nebo"),
    "G13063": ("proper name masculine", "Neh 11:5 Col-hozeh, ancestor of Maaseiah"),
    "G13064": ("proper name masculine", "Neh 12:12 Meraiah, head of priestly house"),
    "G13065": ("proper name masculine", "Neh 12:42 Jezrahiah, leader of singers"),
    "G13087": ("proper name location", "Isa 16:7 Kir-hareseth (Moabite city)"),
    "G13088": ("proper name location", "Jer 26:2 (MT 46:2) Carchemish on the Euphrates"),
    "G13089": ("noun indeclinable", "Jer 26:17 (MT 46:17) transliterated Hebrew phrase"),
    "G13091": ("proper name location", "Jer 31:5 (MT 48:5) ascent of Luhith in Moab"),
    "G13093": ("proper name location", "Jer 31:34 (MT 48:34) Eglath-shelishiyah in Moab"),
    "G13095": ("proper name masculine", "Jer 46:3 (MT 39:3) Nergal-sharezer, Babylonian prince"),
    "G13096": ("proper name masculine", "Jer 46:3 (MT 39:3) Rab-mag, Babylonian official title"),
    "G13104": ("proper name masculine", "Ezek 27:9 elders/wise men of Byblos"),
    "G13115": ("adverb", "Dan 2:26 in the Chaldean/Aramaic language (-ιστί)"),
    "G13128": ("proper name masculine", "Dan 9:1 Xerxes (Ahasuerus), father of Darius"),
    "G13129": ("adjective", "Dan 9:1 Median (τῆς Μηδικῆς)"),
    "G13142": ("proper name masculine", "1 Chr 8:39 son of Ulam in Benjamin"),
    "G13143": ("proper name masculine", "Ezra 2:49 Uzza, ancestor of temple servants"),
    "G13513": ("proper name masculine", "Tob 3:8, 17 Asmodeus, the evil demon"),
    "G13792": ("proper name location", "2 Macc 6:7 festival of the Dionysia"),
    "G14227": ("noun masculine", "4 Macc 17:12 contest/arbiter (not a proper name)"),
    "G14344": ("proper name masculine", "1 Macc 2:2 Gaddis, surname of John son of Mattathias"),
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

con = sqlite3.connect(NEW_DB)
cur = con.cursor()

def get_rtf(tid):
    d = cur.execute("SELECT data FROM content WHERE topic_id=?", (tid,)).fetchone()[0]
    if isinstance(d, bytes):
        return d.decode("latin1"), True
    return d, False

def set_rtf(tid, rtf_str, is_bytes=True):
    val = rtf_str.encode("latin1") if is_bytes else rtf_str
    cur.execute("UPDATE content SET data=? WHERE topic_id=?", (val, tid))
    cur.execute("UPDATE content_search SET data=? WHERE topic_id=?", (rtf_to_plain_clean(rtf_str).encode("utf-16-le"), tid))

rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8-sig")))
stats = collections.Counter()
log_rows = []

for r in rows:
    g = r["Number"]
    hw = r["Headword"]
    tid = cur.execute("SELECT id FROM topics WHERE subject=?", (g,)).fetchone()[0]
    txt = cur.execute("SELECT data FROM content_search WHERE topic_id=?", (tid,)).fetchone()[0].decode("utf-16-le")
    occ_idx = txt.find("OT (LXX) Occurrences:")
    body = txt[:occ_idx] if occ_idx > 0 else txt
    bl = body.lower()

    new_pos = None
    src = ""

    if g in MANUAL_180:
        new_pos, src = MANUAL_180[g]
    else:
        if re.search(r'\bn\.pr\.f\.|\bproper name,\s*feminine\b|\bproper name feminine\b', bl):
            new_pos, src = "proper name feminine", "BDB (n.pr.f.)"
        elif re.search(r'\bn\.pr\.loc\.|\bn\.pr\.terr\.|\bn\.pr\.fl\.|\bn\.pr\.mont\.|\bproper name,\s*of a place\b|\bproper name of a location\b|\bproper name,\s*location\b', bl):
            new_pos, src = "proper name location", "BDB (n.pr.loc.)"
        elif re.search(r'\bn\.pr\.m\.|\bproper name,\s*masculine\b|\bproper name masculine\b', bl):
            new_pos, src = "proper name masculine", "BDB (n.pr.m.)"
        elif re.search(r'\b(woman|wife of|daughter of|mother of|sister of|queen of|queen|goddess|concubine|widow|handmaid|female|heroine)\b', bl) and not re.search(r'\b(son of|father of|king of|priest|city|town|place|village)\b', bl):
            new_pos, src = "proper name feminine", "Definition (female person)"
        elif re.search(r'\b(town|city|cities|village|villages|district|region|province|country|land of|mountain|mount |mountains|river|wadi|torrent|valley|plain|brook|spring|fountain|well|fortress|stronghold|sanctuary|temple|island|gate of|hill|hills|coast|port|harbor|harbour|territory|kingdom|place|border|boundary|wilderness|desert|station|encampment|altar|rock|cliff|cave|forest|wood|pool|sea|lake|quarter of jerusalem|capital of)\b', bl):
            new_pos, src = "proper name location", "Definition (location)"
        elif re.search(r'\b(son of|sons of|sixth son|firstborn|father of|grandfather of|brother of|brothers of|king of|kings of|high priest|priest|priests|levite|levites|governor|commander|captain|general|officer|official|scribe|recorder|prophet|ambassador|envoy|ruler|elder|leader|ancestor|descendant|descendants|man |men of|family|clan|house of|soldier|warrior|martyr|prince|chief|duke|head of|servant|servants|gatekeeper|porter|singer|musician|patriot|patriarch|apostle|disciple|husband|nephew|uncle|cousin|friend of|enemy of|ally of|architect|craftsman)\b', bl):
            new_pos, src = "proper name masculine", "Definition (male person/clan)"
        elif re.search(r'\b(person listed|person named|man named|one of those|one of the|name in a list|in a list of|returned from|came up from|put away)\b', bl):
            if "daughter" in bl or "wife" in bl or "woman" in bl:
                new_pos, src = "proper name feminine", "Definition (female in list)"
            else:
                new_pos, src = "proper name masculine", "Definition (male in genealogical/census list)"
        elif re.search(r'\b(tribe|people|peoples|nation|nations|inhabitants|gentilic|canaanite|egyptian|arabian|edomite|moabite|ammonite|philistine|syrian|persian|greek|roman|cretans)\b', bl):
            new_pos, src = "proper name masculine", "Definition (gentilic/people/tribe)"
        elif g in deut_g:
            top_g = deut_g[g].most_common(1)[0][0]
            new_pos = "proper name feminine" if top_g == "F" else "proper name masculine"
            src = f"Deuterocanon morph ({top_g})"

    assert new_pos, f"Unresolved proper name: {g} ({hw})"

    rtf, is_b = get_rtf(tid)
    rtf_new, n_sub = re.subn(
        r'(Part of [Ss]peech:[^}]*\}\{[^}]*?\s*)proper name(\})',
        rf'\g<1>{new_pos}\2',
        rtf,
        count=1
    )
    assert n_sub == 1, f"Could not replace POS in {g} ({hw})"
    set_rtf(tid, rtf_new, is_b)

    stats[new_pos] += 1
    log_rows.append([g, hw, "proper name", new_pos, src])

# Update Appendix (tid=24331):
# 1) Update subtitle (epv-thayer-kjv) -> (GBL-EPV)
# 2) Remove '; 2026 revision prepared with Claude' per standing rule
# 3) Update Section 7 Part of speech bullet & Section 9 20 November line
ap_rtf, ap_is_b = get_rtf(24331)
ap_rtf = ap_rtf.replace("(epv-thayer-kjv)", "(GBL-EPV)")
ap_rtf = ap_rtf.replace("; 2026 revision prepared with Claude.", ".")
m_pos = re.search(r'Part of speech: \}\{\\plain\\f0\\fs20 .*?\\par', ap_rtf)
assert m_pos, "Part of speech bullet not found in Appendix!"
new_pos_bullet = (
    "Part of speech: }{\\plain\\f0\\fs20 all 729 nouns that previously lacked a gender "
    "and all 1,964 generic proper names have been sub-tagged (20 November 2026) using LSJ articles, "
    "BDB/ISBE classifications, morphological agreement, and verse context.}\\par"
)
ap_rtf = ap_rtf.replace(m_pos.group(0), new_pos_bullet, 1)
ap_rtf = ap_rtf.replace(
    "all 729 nouns without gender updated from LSJ and morphological scholarship.}",
    "all 729 nouns without gender and all 1,964 generic proper names sub-tagged from LSJ, BDB, ISBE, and verse context.}"
)
set_rtf(24331, ap_rtf, ap_is_b)

con.commit()

# Verify 0 remaining generic 'Part of Speech: proper name'
rem = []
for g, raw in cur.execute("SELECT t.subject, cs.data FROM topics t JOIN content_search cs ON cs.topic_id=t.id WHERE t.subject LIKE 'G%'"):
    if not re.fullmatch(r"G\d+", g):
        continue
    m = re.search(r"Part of Speech:\s*([^\r\n]+)", raw.decode("utf-16-le"))
    if m and m.group(1).strip() == "proper name":
        rem.append(g)

ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
assert ic == "ok", f"integrity_check failed: {ic}"
assert not rem, f"Remaining generic proper names: {rem}"
con.close()

with zipfile.ZipFile(NEW_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NEW_DB, arcname=os.path.basename(NEW_DB))

with open(LOG_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Number", "Headword", "Old_POS", "New_POS", "Source"])
    w.writerows(log_rows)

print(f"DONE! Updated {len(log_rows)} entries. Remaining generic proper names: {len(rem)}")
for k, v in stats.most_common():
    print(f"  {k:32s} : {v}")
print(f"PRAGMA integrity_check: {ic}")
print(f"DB:  {NEW_DB} ({os.path.getsize(NEW_DB):,} bytes)")
print(f"ZIP: {NEW_ZIP} ({os.path.getsize(NEW_ZIP):,} bytes)")
print(f"LOG: {LOG_CSV}")
