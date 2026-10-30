# Reconciliation bounds from stored rows (1.4.1 option A, DATAREPO-86)

2026-10-30. `measure.py` over aging's serving catalog `d6a40f203c73306d` (179 bundles, datarepo 1.4.0), compared with
aging's exact terms read from the producer files (`aging/results/reconciliation_2026-10-29/recon_band.tsv`).
Output: `bound.tsv`. Wall 1 min 50 s, sequential Python.

## PSMs (`psms_target_1pct`)

- The recount from `psms.parquet` (target, q <= 0.01, notch q <= 0.01, notch resolved) equals the ingest's recorded
  count in **179 of 179** bundles. A build-side recount reproduces the ingest number, and already reads `ET` as target
  (`Identifications.TargetDecoy`), so DATAREPO-87 is met at build.
- The ambiguous-notch term (passing rows with `notch_ambiguous`) equals aging's in **140 of 140**.
- The rounding term (counted rows whose q or notch q is exactly 0.01, i.e. printed `0.010000`) is SMALLER than aging's
  in every bundle: aging's predicate counted every target row with q <= 0.01 whose q or notch q exceeds 0.0099995,
  including rows the count excludes (notch q > 0.01, ambiguous notch). Ours counts only rows inside the count.
- All **140 of 140** recorded failures lie inside [count - rounding, count + ambiguous]. Median width 0.29% of the count.

## Peptidoforms (`peptidoforms_target_1pct`)

- The count is the ingest's, from `AllPeptides.psmtsv`; the bundle keeps no peptide file, so it cannot be recounted.
- The rounding term (`best_q_value` or `best_q_value_notch` exactly 0.01) equals aging's in **20 of 20**.
- The ambiguous-notch term has no stored source. Its stand-in, "the best-scoring target PSM of the peptidoform is
  notch-ambiguous", is 5-70x aging's exact count (any passing PSM: 20-100x). The peptide file's own notch is not the
  best PSM's.
- All **20 of 20** lie inside [count - ambiguous(best PSM) - rounding, count], but that bound is loose. 16 of the 20 are
  exactly +1.
- Exact for peptidoforms needs the peptide row's notch ambiguity in the bundle: the next ingest-path bump.

## The build, on aging's store (branch `feat/1.4.1`, before the protein-group term)

Scratch folder build of the 179 served deposits (`--latest`, folder layout): 3,668 checks passed; every deposit's
derived rows computed once (205 s, as on any derivation change). `catalog_reconciliation`:

| check | agrees | explained | unexplained |
|---|---:|---:|---:|
| psms_target_1pct | 39 | 140 | 0 |
| peptidoforms_target_1pct | 159 | 20 | 0 |
| protein_groups_1pct | 178 | 0 | 1 (PXD027971) |
| runs, ms2_spectra | 179 each | 0 | 0 |

- The PSM bounds equal `bound.tsv`'s in every bundle; the recount equals the ingest's in every bundle.
- 62 peptidoform lower bounds sit a few rows below `bound.tsv`'s, because the build counts a tie at the best score as
  ambiguous when any tied PSM is (no dependence on row order).
- PXD027971 (aging 122 c): MetaMorpheus 1.1.11 wrote group `A0A0G2JZW2|D4A2S8` (Senp5l1|Senp5) twice, byte for byte,
  and counted both (1,185); the ingest kept one (1,184) and recorded the other in `bundle.json` `collapsed_duplicates`.
  The protein-group bound added after this build explains it, so the build leaves no bundle flagged.
