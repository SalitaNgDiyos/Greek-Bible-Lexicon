# The Greek Bible English Lexicons (TGBEL-EPV)

A Greek dictionary module for [theWord](https://www.theword.net/), keyed to Strong's numbers.

- **Module id:** jb51 · **Title:** Greek Bible Lexicon - Various Authors · **Abbreviation:** GBL-EPV
- **Numbers:** G1–G15737 (G1–G5624 standard Strong's; G5625–G13149 canonical Septuagint words and names; G13150–G15737 deuterocanonical words and names across Apostoliki Diakonia/Orthodox, Brenton, Rahlfs, and Swete)
- **Content:** Thayer definitions, Liddell-Scott-Jones (LSJ) definitions, Brown-Driver-Briggs and contextual entries for proper names, NT counts (Textus Receptus, Byzantine, SBLGNT), and LXX verse lists (Rahlfs, Swete, Brenton, plus Deuterocanon)
- **Companion modules:** LXX Brenton+, SweteLXX+, LXX Rahlfs+ (see the LXX-Strongs-and-RMA-Codes repository)

## Download

`GBL-EPV_<date>.dct.zip` contains the `.dct.twm` file. Unzip it and put it in your theWord `Modules` folder. The newest dated file is the current one.

## Latest update (2026-11-20)

- Renamed module file from `epv-thayer-kjv` to `GBL-EPV`
- Added **2,588** deuterocanonical entries (**G13150–G15737**) covering all vocabulary and proper names in the Greek Deuterocanon (Apostoliki Diakonia/Orthodox, Brenton, Rahlfs, and Swete), with full LSJ entries, contextual proper-name definitions, and occurrence counts
- Updated all **729** nouns that previously lacked a grammatical gender (`noun feminine`, `noun masculine`, `noun neuter`, `noun indeclinable`, `noun masculine or feminine`) from LSJ articles and morphological scholarship
- Sub-tagged all **1,964** generic proper names into `proper name masculine` (1,099), `proper name location` (794), and `proper name feminine` (63) from BDB, ISBE, morphological agreement, and verse context
- Copied all **850** external `Liddell.dct` cross-reference targets into `GBL-EPV` and rewrote all **1,008** LSJ cross-reference links to resolve internally (`0` external `Liddell.dct` links remaining)
- Added parent short meanings for `G9423` (`Ορη`) and `G10991` (`Ηρων`) and updated the Appendix

Every change is listed in `change-logs/`.

## Sources

Thayer's Greek-English Lexicon; Liddell-Scott-Jones, *A Greek-English Lexicon*; Brown-Driver-Briggs (uBDB); International Standard Bible Encyclopedia (ISBE); CATSS LXX morphology (Rahlfs); Swete's Septuagint; Brenton's Septuagint. Each source keeps its own licence terms.
