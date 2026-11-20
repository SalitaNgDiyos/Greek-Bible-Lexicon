GBL-EPV update (`2026-11-20_1823`):

- **Link & XML cleanup across 342 topics (`0` broken links remaining):**
  - Removed all **205** raw XML markers (`<checkingNeeded/>`, `<wrongReferenceRemoved/>`) leaked from source BDB text.
  - Fixed **33** mis-assigned Bible links (e.g. `2Sam 72/89/122/132` → `Psalms`, Hebrew `Joel 4` → KJV `Joel 3`, `Ezra 12:33` → `Neh 12:33`, `1Chr 34:12` → `2Chr 34:12`, `Jude 9` → `Jude 1:9`) and unlinked **76** unresolvable/false-autodetect Bible references (plus 5 removed with `G8335`).
  - Rewrote **30** legacy module links (`tw://bdb-thayer.dct?H...` → `tw://[strong]?t=H...`, `G5646`, `G5823`) and stripped **4** garbled/dead legacy links (`tw://AMBD?`, `tw://jb121?`).
  - Stripped **7,374** external `perseus.tufts.edu` web hyperlink wrappers while preserving the Greek and citation text cleanly offline.
- **Entry fixes:** Replaced mismatched BDB text in **`G8335` (`Αβι`)** (and its parent lemma gloss) and **`G9423` (`Ορη`)** with accurate contextual definitions.
- **Includes all `2026-11-20_1410` updates:** `G13150–G15737` Deuterocanon expansion, `729` noun genders, `1,964` proper-name sub-tags, and `1,008` self-contained internal LSJ links.

Unzip `GBL-EPV_2026-11-20_1823.dct.zip` and place `GBL-EPV_2026-11-20_1823.dct.twm` in your theWord `Modules` folder.
