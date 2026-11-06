# Split-deposit trial, 2026-11-06 (PXR-R30 to R32; G95, G126)

**Question:** can one search folder be ingested and built under a split key (`<accession>-<group>`) on released datarepo 1.4.3,
and what breaks? **Answered to PXReprise in thread 093.**

**How:** the released binary (`F:\aging_batch\datarepo-1.4.3`), a scratch store under the session's scratchpad, aging's search folders read
in place. Nothing was written under `F:`. The scripts here are the ones run; their paths name that scratchpad, and the bundles are not kept.

## Results

| key | bundle | meaning |
|---|---|---|
| `PXD017944` | `3cd52dd1b39472d8` | control: the served id reproduces |
| `PXD027754` | `2799534125b81db3` | bare deposit: the served id reproduces |
| `PXD027754-rat` | `6f88a1ee622775bf` | same folder, split key; every table's row count equals the bare bundle's |
| `PXD027754-mouse` | `5a6fd7af5b7544f5` | **stand-in:** no mouse search exists, so this is the same folder again. It tests collisions, not a real half |

- **Time:** about 6.5 minutes per split key (`run_log.txt`).
- **Build of `-rat`, `-mouse` and the control:** 91 checks, all pass, no id collides.
- **Ids carry the key** (`PXD027754-rat:PCA_LOLA1`, `PXD027754-rat:PCA_LOLA1:10000:1`). USIs name `PXD027754` on all 1,498,854 PSMs.
- **Reconciliation:** each key gets the bare bundle's verdicts: 4 `agrees`, 1 `explained` (PSMs 116,756 against 116,780).
- **Retiring:** `status: superseded` is skipped by a default build, and naming it in `ingest` or `build` is refused with its reason.
- **Trap:** with the bare entry still `include`, the bare bundle and both halves are all served, 107 checks pass, and nothing complains.
- **Non-content fields:** `split_reason` and `superseded_by` on the control leave its id at `3cd52dd1b39472d8`.

## What a served split gets wrong today

| place | what happens |
|---|---|
| site's PRIDE link (`Site.cs:195`) | `.../projects/PXD027754-rat`, which is no PRIDE project |
| site's headline | "3 public proteomics datasets" for 2 deposits |
| a half's page | names no sibling; `datasets/PXD027754.html` no longer exists |
| `protein_index.n_datasets*`, `peptide_index.n_datasets` | count keys: in the stand-in, `A0A8I5Y9S1` reads `n_datasets_1pct = 2` from one deposit |
| census check, `dataset_candidates` (`Catalog.cs:1797-1823`) | read from the code, not run: aging's manifest names no `candidates` |

**Also read from the code, not run:** a re-key leaves `curated_run_design` rows dangling, so the `study-reference` check fails (`Integrity.cs:154-156`). In catalog
`53f5ff162ba37e84`, PXD052189 has 32 curated runs and PXD057407 has 10.

## A second store (PXR-R34, thread 095)

`compare_stores.py` compares the scratch bundles with the served ones file by file. Served: written 10-29 by 1.4.0. Scratch: written 11-06 by 1.4.3, on another drive.

| bundle | files | byte-identical | differs |
|---|---:|---:|---|
| PXD017944 `3cd52dd1b39472d8` | 26 | 25 | `bundle.json` |
| PXD027754 `2799534125b81db3` | 24 | 23 | `bundle.json` |

`bundle.json` differs in exactly three fields on both: `ingester.version`, `manifest` and `written_utc`.

## Per-run MS2, the same day (PXR-R51, G125)

Asked of catalog `53f5ff162ba37e84`: results.txt's `ms2_scans` equals the QC report's `ms2` on 5,051 of 5,051 runs, across all 196 deposits.

```sql
WITH a AS (SELECT scope_id, value FROM metrics WHERE scope='run' AND name='ms2_scans' AND source='results.txt'),
     b AS (SELECT scope_id, value FROM metrics WHERE scope='run' AND name='ms2' AND source='qc_report.json')
SELECT count(*), count(*) FILTER (WHERE a.value = b.value) FROM a JOIN b USING (scope_id);
```
