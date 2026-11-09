# 1.4.5 split trial, 2026-11-09 (G126, D58; PXReprise 105 PXR-R57, our 106)

**Question:** does the 1.4.5 branch (`feat/1.4.5` at `f33cacf`) serve a split deposit as one deposit, refuse it served whole beside
its parts, and leave every value of an unsplit store as it was?

**How:** the branch's CLI, published to the session's scratchpad (`0.0.0-dev`), a scratch store under the same scratchpad, and
aging's search folders and served bundles read in place. The served whole deposit (`PXD027754/2799534125b81db3`) and the control
(`PXD017944/3cd52dd1b39472d8`) were junctioned into the scratch store. Nothing was written under `F:`. The scratch catalogs and
bundles are not kept; these are the scripts run and their output.

## PXD027754 under split keys (`trial.ps1`, `trial_log.txt`, `compare_trial.txt`)

| key | bundle | meaning |
|---|---|---|
| `PXD027754-rat` | `6f88a1ee622775bf` | as on 1.4.3 (our 093), now with `split_reason: species`: the field moves no id |
| `PXD027754-mouse` | `5a6fd7af5b7544f5` | **stand-in:** the same folder again, as in 093 |

- **Parts + control:** catalog `0641521e9e09c00e`, format 16, 59 checks pass. `dataset_overview` names `accession PXD027754`,
  groups `mouse`/`rat`, reason `species`; `deposits` has PXD027754 with 2 datasets and 40 runs.
- **Indexes:** `protein_index` (53,445 rows) and `peptide_index` (10,732) equal the catalog of the whole deposit in every count.
  Under a count by key, 42,777 protein rows and 4,105 peptide rows would read the deposit twice.
- **Whole beside parts:** refused before staging: `PXD027754 beside PXD027754-mouse, PXD027754-rat`.
- **One part alone:** builds; its page says "No other part of it is in this repository", and the deposit gets its page.
- **Sites:** `datasets/PXD027754.html` lists both parts; each part links PRIDE `projects/PXD027754`; the front page says "2 public
  proteomics datasets" and "1 of them was searched in parts"; the Datasets tile reads 2. Read by eye.

## Aging's store (`pins.py`, `full.ps1`, `full_log.txt`, `compare_full.txt`)

All 205 bundles of aging's serving catalog `bd0cc5ef03ab5111` (built by 1.4.3), pinned exactly (`served.json`), built by the branch into a
scratch folder. The exe was a copy named `dr145.exe`: aging's publish script refuses to start while any process whose command line
names `datarepo` runs ` build `, whatever it writes (told PXReprise in 106).

- **First build: 686 s**, 407 s of it deriving all 205 deposits (catalog format 16 is in the derivation id). 4,172 checks pass.
- **A build of 204 of them** (new id, every deposit reused): 302 s, most of it `study and engines` (104 s) and `catalog tables` (54 s).
  Its log is not kept; the numbers are from the session.
- **Values:** same bundles; `protein_index` 128,658 rows, `peptide_index` 794,032 and `protein_datasets` 6,759,096 equal the
  serving catalog's in every column, as do `dataset_overview`'s 23 columns. 205 deposits, none split; `accession = dataset_id`
  everywhere. `release_id` differs (`7716cd67090cc1f8` against `c079b266a0b2dca0`): this build left out the study layer.
