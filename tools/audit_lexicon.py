#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Edmund Paulino Valdez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Audit a compiled GBL-EPV_*.dct.twm SQLite module and README.md."""

from __future__ import annotations

import argparse
import glob
import re
import sqlite3
import sys
from pathlib import Path

ALLOWED_PLAIN_DEFINITION_STRONGS = {
    "G5627",
    "G5649",
    "G5763",
    "G5777",
    "G5794",
    "G6102",
    "G6104",
    "G6122",
}

RAW_GILL_MARKERS = (r"\{k\}", r"\{y\}", r"\k\\", r"\y\\")

REQUIRED_SOURCES: list[tuple[str, tuple[str, ...]]] = [
    ("Thayer", ("thayer",)),
    ("Online Bible / Larry Pierce", ("online bible", "larry pierce")),
    ("Perseus Digital Library / LSJ (CC BY-SA 3.0 US)", ("perseus", "cc by-sa 3.0")),
    ("BDB / uBDB", ("bdb", "brown-driver-briggs")),
    ("ISBE (1915)", ("isbe",)),
    ("McClintock & Strong", ("mcclintock",)),
    ("John Gill", ("john gill", "gill")),
    ("Textus Receptus (TRa)", ("textus receptus", "tra")),
    ("Robinson-Pierpont 2018", ("robinson-pierpont",)),
    ("SBLGNT (CC BY 4.0)", ("sblgnt",)),
    ("MorphGNT (CC BY-SA 3.0)", ("morphgnt",)),
    ("lxxmorph-rc", ("lxxmorph-rc", "catss")),
    ("eliranwong/LXX-Rahlfs-1935", ("lxx-rahlfs-1935", "rahlfs")),
    ("eliranwong/LXX-Swete-1930", ("lxx-swete-1930",)),
    ("sleeptillseven/LXX-Swete", ("lxx-swete", "swete")),
    ("LXX Brenton+", ("brenton",)),
    ("aruljohn/Bible-kjv", ("bible-kjv",)),
]


def _decode_blob(val: object) -> str:
    if val is None:
        return ""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return str(val)


def check_integrity(conn: sqlite3.Connection) -> tuple[bool, str]:
    rows = conn.execute("PRAGMA integrity_check;").fetchall()
    result = ", ".join(str(r[0]) for r in rows)
    return (len(rows) == 1 and str(rows[0][0]).lower() == "ok"), result


def check_twot(conn: sqlite3.Connection) -> list[str]:
    hits: list[str] = []
    for name, value in conn.execute("SELECT name, value FROM config;"):
        text = _decode_blob(value)
        if "(TWOT)" in text:
            hits.append(f"config.{name}")
    for tid, data in conn.execute("SELECT topic_id, data FROM content;"):
        text = _decode_blob(data)
        if "(TWOT)" in text:
            hits.append(f"content.topic_id={tid}")
    return hits


def check_gill_markers(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for tid, data in conn.execute("SELECT topic_id, data FROM content;"):
        text = _decode_blob(data)
        found = [m for m in RAW_GILL_MARKERS if m in text]
        if found:
            hits.append((tid, ", ".join(found)))
    return hits


def check_plain_definition(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    plain_re = re.compile(r"\{\\plain\\f0\\fs20\\b Definition:\}")
    strong_re = re.compile(r"^G(\d+)$", re.IGNORECASE)
    rows = conn.execute(
        "SELECT t.id, t.subject, c.data "
        "FROM topics t JOIN content c ON c.topic_id = t.id;"
    )
    for tid, subject, data in rows:
        subj = (subject or "").strip()
        m = strong_re.match(subj)
        if not m:
            continue
        num = int(m.group(1))
        if not (1 <= num <= 6134):
            continue
        if subj.upper() in ALLOWED_PLAIN_DEFINITION_STRONGS:
            continue
        text = _decode_blob(data)
        if plain_re.search(text):
            hits.append((tid, subj))
    return hits


def check_source_parity(
    conn: sqlite3.Connection, readme_path: Path
) -> dict[str, list[str]]:
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace").lower()
    about_row = conn.execute(
        "SELECT value FROM config WHERE name = 'about';"
    ).fetchone()
    about_text = _decode_blob(about_row[0]).lower() if about_row else ""
    app_row = conn.execute(
        "SELECT data FROM content WHERE topic_id = 24331;"
    ).fetchone()
    appendix_text = _decode_blob(app_row[0]).lower() if app_row else ""

    missing: dict[str, list[str]] = {
        "README.md": [],
        "config.about": [],
        "Appendix(tid=24331)": [],
    }
    for label, needles in REQUIRED_SOURCES:
        if not any(n in readme_text for n in needles):
            missing["README.md"].append(label)
        if not any(n in about_text for n in needles):
            missing["config.about"].append(label)
        if not any(n in appendix_text for n in needles):
            missing["Appendix(tid=24331)"].append(label)
    return missing


def resolve_db_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = sorted(glob.glob("GBL-EPV_*.dct.twm"))
    if not candidates:
        raise FileNotFoundError("No GBL-EPV_*.dct.twm file found in current directory.")
    return Path(candidates[-1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a GBL-EPV_*.dct.twm SQLite module and README.md."
    )
    parser.add_argument(
        "db",
        nargs="?",
        help="Path to GBL-EPV_*.dct.twm (defaults to latest GBL-EPV_*.dct.twm).",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="Path to README.md (default: README.md).",
    )
    args = parser.parse_args(argv)

    db_path = resolve_db_path(args.db)
    readme_path = Path(args.readme)
    if not db_path.is_file():
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        return 1
    if not readme_path.is_file():
        print(f"ERROR: README not found: {readme_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    failures = 0

    try:
        ok, integrity_msg = check_integrity(conn)
        print(f"[a] PRAGMA integrity_check: {'PASS' if ok else 'FAIL'} ({integrity_msg})")
        if not ok:
            failures += 1

        twot_hits = check_twot(conn)
        print(f"[b] (TWOT) occurrences: {'PASS' if not twot_hits else 'FAIL'} ({len(twot_hits)})")
        if twot_hits:
            failures += 1
            for h in twot_hits[:20]:
                print(f"    - {h}")

        gill_hits = check_gill_markers(conn)
        print(f"[c] Raw Gill markers: {'PASS' if not gill_hits else 'FAIL'} ({len(gill_hits)})")
        if gill_hits:
            failures += 1
            for tid, markers in gill_hits[:20]:
                print(f"    - topic_id={tid}: {markers}")

        def_hits = check_plain_definition(conn)
        print(
            f"[d] Plain 'Definition:' in G1-G6134 (excl. 8 GBL-EPV): "
            f"{'PASS' if not def_hits else 'FAIL'} ({len(def_hits)})"
        )
        if def_hits:
            failures += 1
            for tid, subj in def_hits[:20]:
                print(f"    - {subj} (topic_id={tid})")

        parity = check_source_parity(conn, readme_path)
        parity_ok = all(not v for v in parity.values())
        print(f"[e] Source parity (README / config.about / Appendix): {'PASS' if parity_ok else 'FAIL'}")
        if not parity_ok:
            failures += 1
            for target, missing_list in parity.items():
                if missing_list:
                    print(f"    - Missing in {target}: {', '.join(missing_list)}")
    finally:
        conn.close()

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
