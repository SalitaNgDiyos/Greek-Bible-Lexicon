# Build scripts (Python 3)

The scripts that produced the 2026-11-18 update. They read the original dictionary and the LSJ module (`Liddell.dct.twm`) and write a new copy; they never change the original.

1. `load.py`, `analyze2.py`, `report.py`: read both modules, match each Strong's entry to an LSJ headword, and write the coverage report.
2. `build.py`: add LSJ sections to entries that lack one (uses `lib.py`, `conv.py`, `rtf.py`).
3. `fix22.py`: replace the wrong or partial LSJ sections.
4. `add_omos.py`: add G13149 ὠμός.

`conv.py` converts LSJ's RTF into this dictionary's layout. Run on entries that already had LSJ text, it reproduced the existing sections exactly or with identical text in 4,604 of 4,604 comparable entries. The file paths at the top of each script are those of the working folder used then, so adjust them to your own.
