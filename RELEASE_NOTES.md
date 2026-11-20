GBL-EPV update (`2026-11-20_1845`):

- **Word-index fix (`topics_wordindex`):**
  - Removed stale `'david'` index rows from **`G8335` (`Αβι`)** and its parent lemma **`Αβι`**, which previously caused English word lookups for *"David"* to return `G8335` (`Αβι`).
  - Indexed **`'abi'`** on `G8335` and `Αβι`.
  - Indexed **`'david'`** on **`G1138` (`Δαβίδ`)** and its parent lemma **`Δαβίδ`** so looking up *"David"* resolves directly to the main David entry (`G1138`).
- **Includes all `2026-11-20_1823` updates:** link & XML cleanup across 342 topics (`0` broken links), `G8335`/`G9423` entry fixes, `G13150–G15737` Deuterocanon expansion, `729` noun genders, `1,964` proper-name sub-tags, and `1,008` internal LSJ links.

Unzip `GBL-EPV_2026-11-20_1845.dct.zip` and place `GBL-EPV_2026-11-20_1845.dct.twm` in your theWord `Modules` folder.
