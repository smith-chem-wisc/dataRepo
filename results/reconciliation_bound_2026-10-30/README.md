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
