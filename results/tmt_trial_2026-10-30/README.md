# The isobaric ingest on PXReprise's TMT trial (2026-10-30)

**Input:** `F:\pxreprise_trial_tmt\runs\PXD034564\e2e-default\04_search` (PXReprise's, kept for us; profile `tmt-dda@2`,
MetaMorpheus 1.1.13, TMT10 SPS-MS3, 32 files, PXReprise's default design, flagged `no_channel_design`). Ingested from a
scratch run dir of junctions, with the entry PXReprise 074 says their stage 7 will write (`quant_method: TMT`,
`labelling: TMT`, `labelling_plex: 10`) and `--mm-settings F:/aging_data/mm_settings/1.1.13`. Nothing written outside
the session scratchpad.

| | 1.4.0 (bundle `2048e6a8ed5de2ba`) | feat/tmt (bundle `6953203f8f2e506a`) | the search's files |
|---|---:|---:|---:|
| assays | 32 `label_free` | 320 (file, channel) | 320 design rows |
| samples | 32 synthetic | 320 (the design's `Sample Name`s) | 320 |
| protein groups | 0 | 7,327 | 7,327 in `AllProteinGroups.tsv` |
| protein groups at 1% | 0 (`count_mismatch`) | 6,466 | `results.txt` 6,466 |
| `DEF-TMT-PEP` values | none | 528,137 on 44,834 peptidoforms | 528,137 non-zero cells, 44,834 rows with one |
| `DEF-TMT-PROT` values | none | 374,320 on 7,059 groups | 374,320 non-zero cells, 7,059 rows with one |
| PSMs at 1% | 59,028 | 59,028 | `results.txt` 59,028 |
| peptidoforms at 1% | 44,037 | 44,037 | `results.txt` 43,114 |

- **Placement:** 8,000 random cells of `ProteinGroupQuantification.tsv` (400 rows x 20 columns) checked against the
  stored row of their (group, assay): none differs, every 0 is absent.
- **Left out:** nothing. No `|` key, no repeated key (mzLib #1463 is in 1.1.13), every protein row names a written group,
  every peptide row keys a peptidoform, no design channel lacks its column.
- **Findings added:** `isobaric_unlabelled_peptides` (180 rows, 1,313 values: QuantProject 066's 180), and
  `isobaric_files_uncalibrated` (16 of 32, PXReprise's `calibration_failed`), `occupancy_not_ingested`.
- **Catalog:** a scratch folder build of the bundle passes all 23 checks; `dataset_overview` reads `isobaric`, 32 runs,
  320 samples; `catalog_reconciliation` agrees on PSMs and groups.

## The peptidoform gap (DATAREPO-D10), still open

`AllPeptides.psmtsv`, counted directly: targets with `QValue` <= 0.01 are 44,146; with `QValue Notch` <= 0.01 as well,
44,037, which is MetaMorpheus's own peptide filter (`FilteredPsms.cs:192` at MetaMorpheus `6e152da70`, `QValue` and
`QValueNotch` both at the threshold, the summary line labelled "q-value"). `results.txt` says 43,114. The same rule
agrees exactly on the label-free 1.1.13 deposit PXD045861 (10,572 and 10,572), so the gap belongs to this TMT search.
One lead, unverified: targets with `QValue` <= 0.01 **and** `PEP_QValue` <= 0.01 are 43,117, three from `results.txt`.
The 1.4.1 build leaves the check `unexplained`, as it should.

**Explained (QuantProject 071, 2026-11-01):** a multiplex search's `AllPeptides.psmtsv` carries each peptide's best
PSM's PSM-level q-values (MetaMorpheus #2941, open), while `results.txt` counts at peptide level. Our 44,037 is the
right rule on PSM-level values; the `PEP_QValue` lead was a coincidence.

## 1.4.2 on the same trial (2026-11-01)

Bundle `55d39d1895e98784` (was `6953203f8f2e506a`; isobaric reader 2). Against 1.4.1's bundle every table is equal but
`definitions` (`DEF-TMT-PEP`/`PROT` at v3.19) and `findings` (one new: `isobaric_peptide_q_psm_level`). The scratch
catalog's `catalog_reconciliation` reads `peptidoforms_target_1pct` 44,037 / 43,114 `explained`, basis #2941, no bound;
`reconciliation_failed` is empty. Label-free ids unchanged: tutorial `004f8de1881cec43`, PXD017944 `3cd52dd1b39472d8`.

## 1.4.2 as released: DEF-TMT-* at v3.22, isobaric reader 3 (2026-11-03)

QuantProject 073 retracted v3.14's per-file claim (v3.22: only the combined `AllPeptides.psmtsv` is PSM-level), so the
texts and the finding were corrected and the reader went to 3 (2 was pushed, never released). The trial folder
`F:\pxreprise_trial_tmt` is gone, so this was measured on the three isobaric deposits aging serves since PXReprise 080,
re-ingested by a 1.4.2-stamped build into a scratch store from aging's own search folders (read only), and compared
table by table with PXReprise's 1.4.1 bundles (bundle_id ignored):

| deposit | 1.4.1 (served) | 1.4.2 | differs |
|---|---|---|---|
| PXD034564 | `b0cab7e13c179b64` | `ff841cc55ccccb31` | `definitions` 2 rows (DEF-TMT-PEP/PROT), `findings` +1 |
| PXD043296 | `85d48996d238fe25` | `eb5e98c7e6ccd75c` | the same |
| PXD051031 | `8804bb3780600f01` | `fccf50e5513f38f7` | the same |

Every other table is equal in rows and content, and the only differing source is the `isobaric_reader` declaration.
The new finding is `isobaric_peptide_q_psm_level` in each. The ingest's `peptidoforms_target_1pct` gaps (44,059 vs
43,102; 60,606 vs 59,884; 5,812 vs 4,900) are the PSM-level file against `results.txt`'s peptide-level count (#2941).
Label-free ids unchanged: the tutorial's `004f8de1881cec43` (catalog `17a70f4c8baf3c04` on 1.4.2).
