# Greek Bible Lexicon - Various Authors (`GBL-EPV`)

A Greek dictionary module for [theWord](https://www.theword.net/), keyed to Strong's numbers.

- **Module id:** jb51 · **Title:** Greek Bible Lexicon - Various Authors · **Abbreviation:** GBL-EPV
- **Numbers:** G1-G15737 (G1-G5624 standard Strong's; G5625-G13149 canonical Septuagint words and names; G13150-G15737 deuterocanonical words and names across Apostoliki Diakonia/Orthodox, Brenton, Rahlfs, and Swete)
- **Content:** Thayer definitions, Liddell-Scott-Jones (LSJ) definitions, Brown-Driver-Briggs and contextual entries for proper names, NT counts (Textus Receptus, Byzantine, SBLGNT), and LXX verse lists (Rahlfs, Swete, Brenton, plus Deuterocanon)
- **Companion modules:** LXX Brenton+, SweteLXX+, LXX Rahlfs+ (see the LXX-Strong-and-RMA-Codes repository)

## Download

`GBL-EPV_<date>.dct.zip` contains the `.dct.twm` file. Unzip it and put it in your theWord `Modules` folder. The newest dated file is the current one.

## Latest update (2026-11-21)

- Removed leftover `(TWOT)` reference in `G5687`
- Cleaned raw Gill footnote markers (`\{k\}`, `\{y\}`, `\k\`, `\y\`) across entries
- Separated `G25` LSJ gloss from the main definition body
- Relabeled **327** misattributed `Definition:` entries with their proper source labels
- Credited **Online Bible / Larry Pierce** in `config.about` for Strong's/Thayer introductory note & abridged Thayer/BDB outlines
- Credited **Perseus Digital Library** (**CC BY-SA 3.0 US**) for 10,135+ `LSJ Definition:` articles
- Synchronized `Appendix` §1 & §8 (`tid=24331`) with `config.about` and `README.md`
- Added root `LICENSE` and `tools/audit_lexicon.py` (`AGPL-3.0-or-later`)

## Previous update (2026-11-20)

- Renamed module file from `epv-thayer-kjv` to `GBL-EPV`
- Added **2,588** deuterocanonical entries (**G13150-G15737**) covering all vocabulary and proper names in the Greek Deuterocanon (Apostoliki Diakonia/Orthodox, Brenton, Rahlfs, and Swete), with full LSJ entries, contextual proper-name definitions, and occurrence counts
- Updated all **729** nouns that previously lacked a grammatical gender (`noun feminine`, `noun masculine`, `noun neuter`, `noun indeclinable`, `noun masculine or feminine`) from LSJ articles and morphological scholarship
- Sub-tagged all **1,964** generic proper names into `proper name masculine` (1,099), `proper name location` (794), and `proper name feminine` (63) from BDB, ISBE, morphological agreement, and verse context
- Copied all **850** external `Liddell.dct` cross-reference targets into `GBL-EPV` and rewrote all **1,008** LSJ cross-reference links to resolve internally (`0` external `Liddell.dct` links remaining)
- Added parent short meanings for `G9423` (`Όρη`) and `G10991` (`Ηρων`) and updated the Appendix

Every change is listed in `change-logs/`.

## Sources and credits

- **Thayer's Greek-English Lexicon** (1889, public domain)
- **Online Bible / Larry Pierce** — Strong's/Thayer introductory note & abridged Thayer/BDB outlines
- **Perseus Digital Library — Liddell-Scott-Jones (`LSJ`, 1940)** — Perseus Digital Library TEI XML via `Liddell.dct` (10,135+ `LSJ Definition:` articles, **CC BY-SA 3.0 US**)
- **Brown-Driver-Briggs (`uBDB`)** — Hebrew and English Lexicon (public domain)
- **International Standard Bible Encyclopedia (`ISBE`, 1915)** (public domain)
- **McClintock & Strong** — Cyclopedia of Biblical, Theological, and Ecclesiastical Literature (public domain)
- **John Gill** — Exposition of the Entire Bible (public domain)
- **Textus Receptus (`TRa`)** — Stephanus 1550 / Scrivener 1894 (public domain)
- **Robinson-Pierpont 2018** — Byzantine Majority Text (public domain)
- **SBLGNT** — Society of Biblical Literature & Logos Bible Software (2010), edited by Michael W. Holmes (`LogosBible/SBLGNT`, **CC BY 4.0**)
- **MorphGNT** — `morphgnt/sblgnt` (**CC BY-SA 3.0**) and `biblicalhumanities.org` Nestle 1904 lemma list (**CC0 1.0**)
- **`lxxmorph-rc`** — CATSS LXX Morphology (University of Pennsylvania), compiled by Rúbio Terra (**CC BY-NC-SA 4.0** / CCAT non-commercial)
- **`eliranwong/LXX-Rahlfs-1935`** — 249 verses (**CC BY-NC-SA 4.0** / CCAT non-commercial)
- **`eliranwong/LXX-Swete-1930`** — Swete's Septuagint (**GPL-3.0**)
- **`sleeptillseven/LXX-Swete`** — Swete's Septuagint (**CC BY-NC-SA 4.0**, non-commercial use only)
- **`LXX Brenton+`** — Brenton's Septuagint (public domain)
- **`aruljohn/Bible-kjv`** — King James Version (public domain)
- **Build & audit scripts (`tools/`)** — Copyright © 2026 Edmund Paulino Valdez, licensed under **AGPL-3.0-or-later** (see `LICENSE`)
