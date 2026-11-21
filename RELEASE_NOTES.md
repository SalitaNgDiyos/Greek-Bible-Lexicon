GBL-EPV update (`2026-11-21_1850`):

- **TWOT removal in `G5687`:** removed leftover `(TWOT)` reference in `G5687`.
- **Gill footnote marker cleanup:** cleaned raw Gill footnote markers (`\{k\}`, `\{y\}`, `\k\`, `\y\`) across entries.
- **`G25` LSJ gloss separation:** separated the `G25` LSJ gloss from the main definition body.
- **Relabeled 327 entries:** relabeled **327** misattributed `Definition:` entries with their proper source labels.
- **Attribution, documentation & licensing updates:** updated `config.about`, `Appendix` §1 & §8 (`tid=24331`), `README.md`, and added root `LICENSE` (crediting Online Bible / Larry Pierce, Perseus Digital Library CC BY-SA 3.0 US for 10,135+ LSJ articles, and `AGPL-3.0-or-later` for `tools/`).
- **Automated audit script:** added `tools/audit_lexicon.py` (under `AGPL-3.0-or-later`) to verify `PRAGMA integrity_check`, `(TWOT)` absence, raw Gill marker absence, `G1–G6134` `Definition:` attribution, and source parity across `README.md`, `config.about`, and `Appendix`.
- **`content_search` rebuild:** rebuilt `content_search` index for `GBL-EPV_2026-11-21_1850.dct.zip` (`PRAGMA integrity_check = ok`).
- **Includes all `2026-11-20_2123`, `2026-11-20_1845`, and `2026-11-20_1823` updates:** 4 converted RVF binary LSJ blocks, word-index fixes, link & XML cleanup across `342` topics, `G13150-G15737` Deuterocanon expansion, `729` noun genders, `1,964` proper-name sub-tags, and `1,008` internal LSJ links.

Unzip `GBL-EPV_2026-11-21_1850.dct.zip` and place `GBL-EPV_2026-11-21_1850.dct.twm` in your theWord `Modules` folder.
