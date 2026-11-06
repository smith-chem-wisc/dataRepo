# 1.5.0: fragment ions in every bundle, deposit facts, PRIDE records, channel designs

**Status: decided by the user 2026-11-05 (D53, D54, D55), not built.** It closes U20-U24 and answers G116 (PXR-R44), G117
(DATAREPO-88), G120 and PXR-R46/R47. The reader fix (PXR-R48) went first, as 1.4.3.

## What the user decided

| Question | Decision |
|---|---|
| Where fragment ions live (U22) | **A table inside every bundle** |
| Which rows (U23) | **1% PEP q-value**, and for a search with no PEP, **the q-value notch fallback** |
| The rule of `peptidoforms_1pct` (U24) | **1% PEP q-value too**, so the view and the ions hold the same rows. **PEP q-value when it was computed, whatever it accepts; the q-value notch when it was not** (the user, 2026-11-05; D55) |
| May an operator command fetch PRIDE records (U20) | **Yes** |
| Which release carries the PRIDE tables (U21) | **1.5.0** |

The agent had recommended a companion store for ions. The user chose the bundle: a bundle then holds everything about its
search.

## What the bundle table costs

A new table is a schema bump, and `build` refuses a store of mixed versions (`Catalog.cs:1414`). So:

- **Every served bundle is re-ingested once** (168 deposits took 5.0 h for 1.4.0), and all 194 ids move. Measure the whole
  store on a scratch copy first and agree the window with PXReprise, as for 1.4.0.
- `logs.register_orthology` runs again, as at 1.4.0 (PXReprise 069).
- The 8 deposits whose served search sits in `<acc>.superseded-*` are pointed there (PXReprise 084).
- **PXD031782 loses nothing.** It is not in the catalog today: its only bundle is schema 0.0.15, so the 1.4.0 bump already
  excluded it. PXReprise 084 counted it as served by reading the store; our 2026-11-05 comparison table repeated that and
  was wrong.

## Fragment ions

**The table, `peptidoform_ions` (schema 0.0.17, ingest path `cs-1.3.0`):**

| column | meaning |
|---|---|
| `dataset_id`, `peptidoform_id` | the join to `peptidoforms` |
| `full_sequence` | MetaMorpheus's own string |
| `selected_by` | `pep_q_value` or `q_value_notch`: which rule let this row in |
| `pep_q_value`, `q_value_notch` | the cells that rule read |
| the six `Matched Ion *` columns | verbatim |

- **The key is `peptidoform_id` with `full_sequence`.** Two engine names can resolve to one ProForma, so one peptidoform can
  hold several peptide rows. On PXD034590 that accounts exactly for 948,253 peptide rows against 948,250 `peptidoforms`.

**The rule, decided per search:**

- `results.txt` has a PEP block (pep 007's test): a target row with `PEP_QValue` at or below 0.01.
- It has none: a target row with `QValue Notch` at or below 0.01.
- Targets are `T` and `ET` (pep 008; DATAREPO-87).
- A finding says when the fallback was used. The text cites MetaMorpheus's own `PepQValueElseQValueNotch` (#2909).

**Why per search, not per row.** PXD058775 (1 of 196 searches, the only one with no PEP block) trained no PEP: its `PEP`
column holds one value. Yet its `PEP_QValue` still holds numbers, 229 of them at or below 1%, so a test on the row would trust
values that mean nothing. The fallback gives it 252 rows. mzLib's `QuantifiedPsmRule` also decides per search. A per-row fallback would
change almost nothing (`rule_uncomputed.py`, all 193 trained deposits): 41,559 target rows read MetaMorpheus's unset 2, and of the 98,964
reading above 1, only 14 pass the notch, all in PXD020462. That deposit's values above 1 are mostly real numbers such as 1.0212, not the unset 2
(`rule_pxd020462.py`), so a value above 1 does not by itself mean "not computed".

**What it measures** (zstd Parquet, the six ion columns):

| deposit | 1% PEP q-value rows | MB | bytes/row | `peptidoforms_1pct` rule | in that rule, no ions | ions, outside that rule |
|---|---:|---:|---:|---:|---:|---:|
| PXD082596 | 36,911 | 7.0 | 190 | 23,266 | 650 (2.8%) | 14,295 |
| PXD034590 | 121,681 | 23.7 | 195 | 90,744 | 1,707 (1.9%) | 32,644 |
| PXD025315 | 150,529 | 34.6 | 230 | 127,677 | 3,846 (3.0%) | 26,698 |
| PXD036557 | 1,678 | 0.2 | 146 | 1,451 | 21 (1.4%) | 248 |
| PXD034564 (TMT) | 65,671 | 32.2 | 491 | 44,059 | 951 (2.2%) | 22,563 |

Across the store this is 8,064,334 rows, so an estimate of **about 2 GB**, beside 86 GB. TMT rows cost more; only four
deposits are TMT today.

**These five deposits were not representative.** None is a low-resolution search, so the "1.4% to 3.0% of rows have no ions"
that PXReprise 089 and aging 129 quote (each saying it was these five) does not describe the store. See the next section.

## The 1% PEP q-value rule across the store

Measured 2026-11-05 on all 194 deposits in catalog `d621ea41cd649681`, from each served `AllPeptides.psmtsv`
(`results/pep_rule_2026-11-05/`). The q-value counts match the catalog's `n_peptidoforms_1pct` to within one row on every deposit.

| | deposits | q-value rule | PEP rule (notch where no PEP block) |
|---|---:|---:|---:|
| gain rows (ratio 1.03 to 3.87, overall median 1.28) | 173 | 6,149,007 | 8,023,817 |
| lose rows (ratio 0 to 0.88) | 21 | 161,117 | 40,517 |
| all | 194 | 6,310,124 | 8,064,334 |

**The 21.** Nothing lies between ratio 0.88 and 1.03, so the two groups are distinct.

- 19 lose more than half. PXD057502 goes from 5,962 to **0**: results.txt reports `round 0: accepted 0`, and its lowest
  target `PEP_QValue` is exactly 0.02, so no target row can pass.
- They are mostly low-resolution searches: 18 of the 32 `label-free-dda-lowres` deposits lose rows (17 lose over half), against 3
  of the other 162.
- The ions follow the rule, so PXD057502 stores no ion rows at all.
- **It is the peptide level only, so the model has not simply failed.** In the same bundles the PSM-level `pep_q_value` gains rows on 18
  of the 21 (`rule_psm_level.py`): PXD022227 goes from 184,016 to 260,862 PSMs while its peptides go from 18,035 to 1,303. PXD057502 and
  PXD027971 lose 10% and 5% of PSMs; only PXD020462 loses heavily (0.10).
- **A 1% cut falls off a plateau.** PXD022227's q-rule peptides have a median `PEP_QValue` of 0.011, just over the line, and 32,534 targets pass
  at 5%, against 1,303 at 1%. These are the same q-rule rows, read on a different ranking.

**No test in the training report separates them cleanly:**

| test | deposits flagged | of the 21 | |
|---|---:|---:|---|
| `LogLoss: Infinity` | 64 | 20 | 44 flagged deposits gain rows |
| `Training Rounds Run: 1` | 27 | 19 | not printed by 1.1.11; misses PXD052189 and PXD027971 |
| training targets / decoys below 0.05 | 24 | 19 | |
| PEP-rule rows below 0.6 of training targets | 54 | 21 | 33 flagged deposits gain rows |

**Which rule is right on the 21 is not settled here.** Nothing in these files is a ground truth; pep's entrapment estimator on a
low-resolution deposit would say. Whether peptide-level `PEP_QValue` is rightly this strict on these searches, or is a defect, is pep's
to say. It may be a finding for MetaMorpheus either way.

**U24, answered by the user 2026-11-05 (D55):** "priority is 1%pep q-value when it is computed. when it is not computed, we fall back to
q-value notch."

- **The fallback asks whether PEP q-value was computed, never how many rows it accepts.** The agent had proposed sending a search to the notch
  when the PEP rule accepted fewer peptides than the q-value rule (171,445 rows on the 21, against 40,517). That test is dropped.
- **So the 21 stay on PEP q-value**, all of them having computed it: PXD057502 serves 0 rows in `peptidoforms_1pct`, and 19 lose over half. Only
  PXD058775 falls back. The store holds 8,064,334 rows.
- **This is mzLib's own rule.** `QuantifiedPsmRule` (mzLib `Quantification/QuantifiedPsmRule.cs`) takes the PEP q-value when PEP was trained,
  otherwise the notch q-value, otherwise the q-value, and says "which tier applies belongs to the whole search, not to one match". A match with
  no value for the chosen tier is not quantified. ptmQtl's S7 already calls it (`PtmQtlBundle.cs:126`).

**What moving `peptidoforms_1pct` changes:**

- `n_peptidoforms_1pct`, `protein_datasets`, `protein_index.n_datasets_1pct`, `peptide_index` and `modifications_placed` all read the
  view, so all move. `dataset_overview` and the site read "at 1% FDR" and must state the rule.
- **It stops matching results.txt.** `aging:DEF-PEPTIDE-1PCT` is that file's q-value line, so the view no longer computes it. aging must be
  told. `metrics` and the reconciliation (`Reconcile.cs`, `CatalogReconciliation.cs`, which restate the q-value rule) stay as they are, or
  nearly every deposit reads `count_mismatch`.
- **Counts compare less well across releases.** Median gain is 13% on 1.1.11, 28% on 1.1.12 and 35% on 1.1.13. 1.1.11 trained PEP once and
  later releases iterate (pep 005, 007), and `psms.pep_q_value`'s own description says a count compares within one release. 10
  deposits are on 1.1.11. The view's description must say so.
- **Staying where they are:** `n_psms_1pct` and `protein_groups_1pct`. The user asked about peptidoforms; PSMs have not been measured. Column
  descriptions state each rule.
- **Peers:** ptmQtl's filter is already its own PEP-first rule (S7) at PSM level, so this change does not reach it, and the PSM level holds on
  these deposits except PXD020462. PXReprise's `tools/ptm-db/BuildPtmDb.cs` restates the
  q-value rule for its PSMs, so it does not follow the view; theirs to decide. aging's dated `results/organelle_ptm_*` scripts read the view.
- The isobaric finding and `DEF-TMT-*` note (`Ingester.cs:668`, `Definitions.Texts.cs:137`) say the view is a PSM-level filter on `best_q_value`.
  Re-read #2941 for what `PEP_QValue` means in a multiplex `AllPeptides.psmtsv` before rewriting them.

**For the build to settle:**

- **Drop `psms.matched_ion_series` and `psms.matched_ion_count`** (the user, 2026-11-05; D56). They are null in every row of every bundle, and a
  schema bump is the only time to do it. No peer's code reads them: PXReprise's only mentions are its 2026-11-03 note that they are empty.
- Add `peptidoforms.best_pep_q_value`. The view now needs it, so this is no longer optional.
- **The q-value count stays readable.** `metrics` keeps it from results.txt on all 194 deposits (`name = 'peptides'`, `scope = 'dataset'`,
  under `pxreprise:` or `aging:DEF-PEPTIDE-1PCT`), which is how a reader compares the two rules.
- **Where the per-search verdict lives.** The view cannot read results.txt, so the ingest must record which rule a search used, for
  the view to read. `DepositDerived.cs:104` hashes the threshold into a derivation id, and must hash the rule too.
- **How "computed" is read.** D53 took pep 007's results.txt block; mzLib's `PepIsUsable` reads the values, decoys included (some PEP q-value in
  [0, 1], and more than one distinct PEP). On all 194 deposits both name only PXD058775. Agent's recommendation: call `ChooseTier`, so that one
  rule lives in one place. Its third tier (no PEP, no notch) reaches no served deposit.
- **A deposit with nothing at 1%.** PXD057502 must build with an empty `peptidoform_ions` and `n_peptidoforms_1pct` = 0. Agent's recommendation: a
  finding on a search whose PEP rule accepts fewer target peptides than the q-value rule, naming both counts. It changes no row; without it a reader
  takes those 21 deposits for small ones.
- **`<=` or `<`.** The views use `<=`. mzLib's `PassesConfidence` and #2909's `pep q-value < 0.01` line use `<`. Now the rule is mzLib's, measure the
  rows at exactly 0.01 before choosing.
- **Run-scope counts (G125, U25; added 2026-11-06).** `metrics` rows with `scope = 'run'` and `source = 'results.txt'` (`psms_1pct`,
  `peptides`, `protein_groups`, `ms2_scans`, `precursors`: 5,051 rows each on all 196 deposits in catalog `53f5ff162ba37e84`) come only from
  results.txt's per-file lines (`Readers.cs:515`, `Ingester.cs:1036`).
  - PXReprise's `label-free-dda@14` and `lowres@7`, live 2026-11-06, turn those lines off, so a bundle from them has none of the five, and no
    finding says so. This is read from the code: no @14 search has been ingested yet.
  - **results.txt is not the only place for per-run scan counts** (the user, 2026-11-06). `ms2_scans` equals the QC report's `ms2` on 5,051 of 5,051 runs, so
    per-run MS2 is safe. A QC report holds no precursor count. PXR-R51 (our 091) asks PXReprise where else to read them; build this item after its answer.
  - MetaMorpheus #2955 (released in 1.1.14, 2026-11-06; PXReprise has not pinned it) brings back `ms2_scans` and `precursors` on a search of two or
    more files, in the form `ResultsScansPerFile` already reads. The other three have no source: they "still need the tables" (QuantProject 077).
  - Our aging 119 promised per-run counts from the whole search's 1% set; aging 120 accepted, and reads no run-scope rows. This re-ingest is the
    time to do it: one definition for every deposit, rather than per-file FDR for old bundles and nothing for new ones.
  - To settle: which rule counts peptides now that the view moves, and the definition ids, which are their owners' (D24). Today's rows cite dataset
    definitions for per-file-FDR counts.
  - The isobaric finding's sentence on per-file `_Peptides.psmtsv` (`Ingester.cs:669`) stops being true under `tmt-dda@3`. Rewrite it with the #2941 re-read above.
- **MetaMorpheus 1.1.14's #2936 (QuantProject 077).** PEP now computes for a search with over 1000 PSMs and only 100 to 1000 peptides. PXD058775, the
  only deposit on the notch, reads 1,859 PSMs and 226 peptides at 1% (results.txt), so a re-search would probably leave the fallback. D55 does not change,
  since it is decided per search, and no re-search is implied. The code path must still exist, and a fixture must still reach it.
- What else rides on the one re-ingest (the mzLib 1.0.597 bump, whose parity tests must be re-run, is the obvious candidate).
- **Reader:** a second pass with `TsvReader` (1.4.3), which reads these columns from a table one row at a time.

## `deposit_facts` and PRIDE records: a companion beside the bundle

Both have their own cadence and must not move a search bundle's id, so these two stay out of the bundle.

- **Where:** `<store>/_companion/<kind>/<accession>/<id>/`, beside `_engine/` and `_study/`. Add-only. Newest per accession is
  served. Its version is its own, so a core schema bump does not stale it.
- **`deposit_facts` (PXR-R46, R47):** yes, in PXReprise's shape and name, with `column` renamed `sdrf_column` (`COLUMN` is a
  SQL keyword). Nothing merges facts into `sample_characteristics`.
- **PRIDE records (U20):** an operator command, through mzLib's `PrideArchiveClient`, stores each record with its sha256, fetch
  time and mzLib version. E-mail is never stored. U14 stays true: the runner fetches nothing. `build` reads them into ptmQtl's
  three tables (`deposit_records`, `deposit_contacts`, `deposit_references`; our 061).
- **Shared raw files:** ptmQtl's served view, derived at build from `runs.sha256`: one row per run whose sha256 appears more
  than once, saying whether the other copies are in the same accession (their 062).

## Split deposits: the catalog side (G126, U26; proposed in PXReprise 093, not built)

A split key already ingests and builds on 1.4.3 (`results/split_trial_2026-11-06/`), so none of this needs the re-ingest. It rides 1.5.0 by default only because
1.5.0 bumps the catalog format anyway; the release is the user's word (U26).

- `dataset_overview` gains `accession`, `split_group` (both derived from the key, `Usi.DepositAccession`) and `split_reason` (a non-content manifest field, checked against
  `species`, `enrichment`, `label`, `chemistry`, as `restrictions` is at `Manifest.cs:82`).
- One deposit-level view, one row per accession, listing its keys. Name to settle.
- The site: a deposit page at `datasets/<accession>.html` that links its halves and keeps today's address, sibling links on each half, the PRIDE link from the accession (`Site.cs:195`),
  and a headline that counts accessions.
- `protein_index.n_datasets*` and `peptide_index.n_datasets` count accessions (`DepositDerived.cs:62-64,84`). `dataset_ids*` keep the keys. No value moves until something is split.
- The census compares by accession (`Catalog.cs:1797-1823`).
- A build refuses a bare key served beside its own halves. Tested today: 107 checks pass and nothing complains.

## DATAREPO-88 (aging 126)

- **(a) Channel design.** All four TMT deposits show one sample per assay (360/360, 320/320, 216/216, 264/264). The cause is
  PXReprise's default design, not our reader: `Isobaric.cs:167` shares a sample across fractions as soon as the design repeats
  a `Sample Name`.
  - **To aging's question:** we read the `TmtDesign.txt` the search used, and every bundle keeps a copy. An SDRF sample wins
    where one names that run and channel. So a real design fills `sample_id` with no change of ours.
  - **To build:** a view `isobaric_channels` from that copy (assay, run, plex, channel, sample, `Sample Type`). The roles
    `sample`/`reference`/`empty` are QuantProject's to define (REQ-QP-15 d); until then the cell is carried verbatim.
- **(b) `quant_scale`.** Derived at build: `label_free_apex`, or `reporter_*`. MS2 against MS3 is in no bundle and raw files are
  deleted (D59), so PXReprise records it in the manifest. Until then the value reads `reporter_level_not_recorded`, never a
  guess. It is a non-content field taken at build, as `restrictions` is (`Manifest.cs:82`), so recording it moves no id.
- **(c) `age_effect_meta` for v1.3.** Aging layer 0.7.0: `method_scope` replaces `quant_method` in the key
  (`schema/study/aging.yaml:349`), with the count columns and a method-term table. Nothing converts: all three age-effect tables
  hold 0 rows in catalog `d621ea41cd649681`.
- **(d) The guidance.** It lives in `schema/study/aging.yaml:328` and `:349` and `Integrity.cs:115`. Copy aging's newest v1.3
  wording when building, and re-read it first, since copied text has been retracted before.

## Order

1. Send the shape to PXReprise and aging; agree the window. Nothing is built until PXReprise has answered.
2. Build on `feat/1.5.0`; measure a whole-store scratch re-ingest; predict ids.
3. Release on the user's word; PXReprise swaps the pin and re-ingests.

GO per target set (G111, unblocked by mzLib 1.0.597) gets its own plan.
