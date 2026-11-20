GBL-EPV update (`2026-11-20_2123`):

- **Converted 4 raw RVF binary LSJ blocks (`-8 1 3 ... 1rvsDyna...`) to clean RTF:**
  - **`G2443` (`ἵνα`)**: converted `29,658` bytes of raw TRichView binary (`645` styled UTF-16 items and `213` hyperlinks) into formatted RTF (`10 pt Segoe UI`, `12 pt maroon Gentium`, bold sense headings, italic glosses, and blue `HYPERLINK` fields, plus remapping the internal `ἐάν` link to `tw://[self]?tid=24952`).
  - **`G1654` (`ἐλεημοσύνη`)**: converted `1,798` bytes of raw RVF binary (`17` items) into formatted RTF.
  - **`G3889` (`παραμυθία`)**: converted `3,898` bytes of raw RVF binary (`68` items) into formatted RTF.
  - **`G5614` (`ὡσαννά`)**: converted `1,753` bytes of raw RVF binary (`15` items) into formatted RTF.
  - Verified `0` binary control bytes and `0` RVF blocks remaining across all `44,507` topics (`PRAGMA integrity_check = ok`).
- **Includes all `2026-11-20_1845` and `2026-11-20_1823` updates:** word-index fixes (`'david'` on `G1138 Δαβίδ`, `'abi'` on `G8335 Αβι`), link & XML cleanup across `342` topics (`0` broken links), `G8335`/`G9423` entry fixes, `G13150–G15737` Deuterocanon expansion, `729` noun genders, `1,964` proper-name sub-tags, and `1,008` internal LSJ links.

Unzip `GBL-EPV_2026-11-20_2123.dct.zip` and place `GBL-EPV_2026-11-20_2123.dct.twm` in your theWord `Modules` folder.
