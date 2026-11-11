# mzLib 1.0.595 -> 1.0.597: what moves (1.5.0 build list item 1), 2026-11-11

**Method.** master's code at `b97d1bc`, built twice: as is (mzLib 1.0.595) and with only the `mzLib` package version changed to
1.0.597 (a throwaway worktree). Each build ingested PXD011740 (label-free, modification-heavy) and PXD034564 (TMT10) from aging's live
batch manifest into its own scratch store, `F:/datarepo_scratch_150/store595` and `store597` (PXD017944 was refused: excluded since
2026-11-09). `compare_stores.py` compares every table row for row in both directions (`compare_stores.out`); `pair_moved.py` pairs each moved
row with its counterpart (`pair_moved.out`).

**Result: peptidoform keys move, nothing else does, and the bundle id does not.**

| table | PXD011740 rows moved | PXD034564 rows moved | what moved |
|---|---:|---:|---|
| `peptidoforms` | 69 of 64,731 | 967 of 360,551 | `peptidoform` (the key): a mass tag becomes a Unimod accession; every other column equal, rows pair one to one by `engine_full_sequences` |
| `psms` | 120 of 176,667 | 1,276 of 495,857 | `peptidoform` and `usi` only; every row keeps its `psm_id` |
| `ptm_sites` | 4 of 6,207 | 123 of 78,418 | `modification`: NULL becomes `UNIMOD:64`; ids unchanged |
| `quant_values` | 0 | 1,395 of 901,996 | `feature_id` (peptidoform rows); every (assay, definition, value) equal |
| every other table | equal | equal | |

- **Why:** mzLib #1416 and #1524 link 106 UniProt modifications to the Unimod records UniProt does not cite. N6-succinyllysine
  (`[+100.016044]` -> `[UNIMOD:64]`), N6-crotonyllysine (`UNIMOD:1363`), N6-benzoyllysine (`UNIMOD:136`) and, in PXD034564, four more
  masses (+15.994915, +114.031694, +44.985078, +86.000394). Four PXD034564 peptidoforms keep a `[+` because a second modification on
  them is still unlinked.
- **The bundle id does not move** (`b7dbca088aa5c165`, `ff841cc55ccccb31` from both builds): it hashes inputs, never code. So 1.0.597
  must not ship without an ingest-path bump; 1.5.0's `cs-1.3.0` carries it.
- **Not moved by #1415** (PSI-MOD charges from a table, a charged mass from its formula): no row changed. The unit test that failed
  used a made-up ptmlist entry whose mass disagreed with its own formula; fixed in the test.
- **#1513 (eight more lysine acyl amides block cleavage):** no ingest row. In ptmQtl's S2c (a runner, not ingest) all five of ptmQtl's
  own acyl amides are now on mzLib's list, so their reason reads "mzLib's list", and decanoyl, lactoyl and stearoyl lysine now block too.
- **Tell at the announcement:** ptmQtl and QuantProject (peptidoform keys move, as at 1.4.0's G26), ptmQtl (S2c reasons; three more
  blocking modifications), aging.

The full test suite on 1.0.597 failed 15 of 848; 10 fail on master's 1.0.595 too (real-data fixtures re-searched or re-downloaded since
their Python reference was captured, and aging's study delivery), and the 5 bump failures are fixed in the tests.
