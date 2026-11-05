# 1.5.0: fragment ions in every bundle, deposit facts, PRIDE records, channel designs

**Status: decided by the user 2026-11-05 (D53, D54), not built.** It closes U20-U23 and answers G116 (PXR-R44), G117
(DATAREPO-88), G120 and PXR-R46/R47. The reader fix (PXR-R48) went first, as 1.4.3.

## What the user decided

| Question | Decision |
|---|---|
| Where fragment ions live (U22) | **A table inside every bundle** |
| Which rows (U23) | **1% PEP q-value**, and for a search with no PEP, **the q-value notch fallback** |
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
values that mean nothing. The fallback gives it 252 rows. In the four trained deposits checked, every target row reading
`PEP_QValue` 2 fails the notch too, so a per-row fallback would add nothing there.

**What it measures** (zstd Parquet, the six ion columns):

| deposit | 1% PEP q-value rows | MB | bytes/row | `peptidoforms_1pct` rule | in that rule, no ions | ions, outside that rule |
|---|---:|---:|---:|---:|---:|---:|
| PXD082596 | 36,911 | 7.0 | 190 | 23,266 | 650 (2.8%) | 14,295 |
| PXD034590 | 121,681 | 23.7 | 195 | 90,744 | 1,707 (1.9%) | 32,644 |
| PXD025315 | 150,529 | 34.6 | 230 | 127,677 | 3,846 (3.0%) | 26,698 |
| PXD036557 | 1,678 | 0.2 | 146 | 1,451 | 21 (1.4%) | 248 |
| PXD034564 (TMT) | 65,671 | 32.2 | 491 | 44,059 | 951 (2.2%) | 22,563 |

Across the store this is an estimate of **about 2 GB**, beside 86 GB. TMT rows cost more; only four deposits are TMT today.

**Two things a reader must be told.** The two 1% rules are different rows:

- 1.4% to 3.0% of `peptidoforms_1pct` rows have no ions.
- Each deposit also has ions for rows `peptidoforms_1pct` does not hold.

The table's description says so. `peptidoforms` holds no PEP q-value today, so a reader could not see why from that table alone.

**For the build to settle:**

- Drop the always-null `psms.matched_ion_*`: a schema bump is the only time to do it. Agent's recommendation.
- Add `peptidoforms.best_pep_q_value`, so `peptidoforms` can state the rule the ions follow. Agent's recommendation; say if not.
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
