# Which database did each served search read, and is it recorded? (2026-11-09)

**Why:** the user, 2026-11-09: "somehow somewhere we need to store a pointer to the database ... without it there is no hope of
reproducing a result." A search is calibration, then GPTMD, then the search. GPTMD writes new databases, and the search reads
those, not the files it started from.

**How:** read only. Sources: aging's serving catalog `3ab0a6770154cf5a` (208 bundles, built by 1.4.3), each bundle's `bundle.json`,
its verbatim copy of the search provenance (`sources/provenance_04_search.json`) and of `results.txt` (`sources/results.txt`;
"Databases loaded"), and the files' sizes on disk. Scripts: `searched_db.py` (writes `searched_db.tsv`), `categories.py`,
`inputs.py`, `compress.py`.

## Results

| what the search loaded | bundles | where the pointer is |
|---|---:|---|
| GPTMD's databases | 150 | path, size and sha256 in the provenance copy (`outputs[]`); **in no table**. Files on disk at the recorded size |
| the input databases (no GPTMD step) | 48 | `bundle.json` `sources` (`protein_database:*`, with sha256) and `dataset_databases` |
| a GPTMD proteome database **with no recorded sha256** | 10 | none: MetaMorpheus 1.1.11 searches whose provenance lists only the contaminant GPTMD file (PXD036557 has no provenance copy at all) |

- **The 10:** PXD007999, PXD018969, PXD027318, PXD032040, PXD032202, PXD036557, PXD042301, PXD044773, PXD052189,
  PXD058775 (bundle ids in `ten.py`).
- **Their files are still on disk** (`ten.py`, `ten.txt`). Each search folder the served bundle names holds both GPTMD files,
  exactly the two its `results.txt` loaded, each last written before the search's provenance. Seven of those folders are
  `.superseded-*` now, so a path recorded before the move no longer resolves; the sha256 still identifies the file.
  - **Nine recorded contaminant files still match their recorded sha256.**
  - **The ten proteome files were hashed on 2026-11-09:** a pointer from today, not proof of what the search read.
- **A first pass said these files were gone.** Its listing never looked inside the task folder. Corrected before anything was sent.
- **What a reader is told today:** `dataset_databases`, `datasets.search_database` and `bundle.json`'s `protein_databases` all name
  the databases GPTMD STARTED from, for the 150 as well. Nothing says the search read another file.
- **One checksum verified:** PXD017944's `…v088GPTMD.xml` hashes to `76b99fb1…7ce4`, the provenance's value.

## Keeping the databases themselves

- **GPTMD's databases:** 159 searches, 51.7 GB as written. One (292.4 MB) compresses to 29.3 MB with zstd -3 (10.0x, 2 s), 19.8 MB at
  -19, and 35.5 MB with gzip -6. All 159 would be about 5 GB at zstd -3.
- **The originals:** 46 distinct by sha256, 11.6 GB, all still on disk at a recorded path. They are shared: one proteome serves many
  searches.
- **For scale:** the 208 served bundles take 29.4 GiB.
