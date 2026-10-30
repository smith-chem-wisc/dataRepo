# datarepo 1.4.1: contents and the one open question

Started 2026-10-29 on the user's word (D51). Branch `feat/1.4.1`, worktree `code/_wt_141`. Release only on the
user's word.

## Items

| item | where it lands | needs a re-ingest? |
|---|---|---|
| Unique-peptide label by MetaMorpheus release (AGING-R1, QuantProject 064). PXD045861 (1.1.13) is already served | build: derived from `datasets.search_engine_version` (D32) | no |
| DATAREPO-87: count `ET` and `T\|ET` as targets (mzLib `DecoyContaminantTargetLabel`), `T\|C` still uncounted | `Identifications.ProducerCounts` (ingest) | see below |
| DATAREPO-86 (a): each count check carries its explained bound; `ok` = inside it; `reconciliation_failed` names only unexplained checks | see below | see below |
| DATAREPO-86 (c): PXD027971 `protein_groups_1pct` 1,184 vs `results.txt` 1,185 | investigation | no |
| G110: no `go_annotation.tsv` copy in a go artefact (`GoEngine.cs:362`) | runner: `RUNNER_VERSION` bump | no |
| ptmQtl D60 (S2c gates), D70/P36 (key sites by `sequence_window`, S5 where NULL) | engines | no |
| Docs: a schema bump needs `logs.register_orthology` again (PXReprise 069) | `docs/` | no |

## The open question: ingest or build for reconciliation

Reconciliation is computed at INGEST today (`Ingester.cs:670`, `Reconcile.Build`) and written into the bundle's
findings and `bundle.json`. A bundle id hashes the ingest path, not the code, so changing what ingest writes needs an
ingest-path bump (cs-1.2.0 -> cs-1.2.1) and a whole-store re-ingest at PXReprise (about 5 h, one swap gap).

- **(A) Build-side, no re-ingest (recommended).** The stored rows already hold every input of the PSM count and its
  bound: `psms.target_decoy` (already reads `ET` as target and `T|C` as contaminant, `Identifications.TargetDecoy`),
  `q_value`, `q_value_notch` and `notch_ambiguous`. aging 122 found the ingest count equals that predicate in all 179
  bundles. So build recounts, computes the bound (rows with `q_value = 0.01` exactly, i.e. printed `0.010000`; passing
  rows with an ambiguous notch), and writes the verdict to a catalog table. The ingest-time check stays in the bundle
  as recorded and the catalog says which one it serves. The ingest fix for `== "T"` waits for the next ingest-path
  bump. No stored bundle carries an entrapment label, so nothing is wrong today.
  - **Gap:** the peptidoform bound's notch term needs each peptide's own notch ambiguity, which `peptidoforms` does
    not keep (only `best_q_value`, `best_q_value_notch`). Without it the lower bound is the `0.010000` term alone.
    aging's 20 of 20 includes PXD067102's +20, all `0.010000` rows; whether the other 19 fit without the notch term
    must be measured before we say (a) is met for peptidoforms.
- **(B) Ingest-side.** Fix `ProducerCounts`, add the bound to `Reconcile`, bump to cs-1.2.1, and ask PXReprise for a
  second whole-store re-ingest window. Exact for peptidoforms; costs the operator a gap.
