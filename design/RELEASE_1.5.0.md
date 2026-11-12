# 1.5.0: fragment ions in every bundle, deposit facts, PRIDE records, channel designs

**Status: decided by the user 2026-11-05 (D53, D54, D55); building since 2026-11-11 (D60: "1.5.0 first") on `feat/1.5.0`
(worktree `code/_wt_150`).** It closes U20-U24 and answers G116 (PXR-R44), G117 (DATAREPO-88), G120 and PXR-R46/R47. The reader
fix (PXR-R48) went first, as 1.4.3.

## Build list (2026-11-11)

The sections below hold the reasoning; this is what is built, in order. **The schema stays unpushed until its list is closed:** a
pushed schema version is frozen, so 0.0.17 goes out once, with every column below.

**Ingest (schema 0.0.17, ingest path `cs-1.3.0`, one whole-store re-ingest):**

| # | item | source | status |
|---|---|---|---|
| 1 | mzLib 1.0.595 -> 1.0.597. **It moves peptidoform keys** (mass tag -> Unimod accession for UniProt modifications mzLib #1416/#1524 newly link; 69 of 64,731 in PXD011740, 967 of 360,551 in PXD034564), nothing else, and no bundle id: so it rides `cs-1.3.0`, never alone. Tell ptmQtl/QuantProject/aging at the announcement (`results/mzlib597_2026-11-11/`). A later release carrying #1555/#1557/#1578 is taken if it lands first. **Taken 2026-11-12: mzLib 1.0.598** (released that day with all three; the user: "yes"). It compiles unchanged and moves no row: eight real deposits, chosen to reach SDRF reading, TMT, pooled samples, 1.1.11 and the notch fallback, ingest to equal tables on 1.0.597 and 1.0.598, only `bundle.json`'s `modification_registry.loader` naming the new mzLib (`results/mzlib598_2026-11-12/`). U31 is settled by the same release | | **done** |
| 2 | Per-search confidence rule recorded at ingest (`ChooseTier`) as `datasets.confidence_rule`, `peptidoforms.best_pep_q_value`, the fallback finding, the fewer-than-q-value finding. **Strictly below 0.01, as mzLib's `PassesConfidence` and ptmQtl's S7:** measured 2026-11-11 on aging's 181 served deposits (catalog `cfab8ab81b2673f1`, `results/confidence_rule_2026-11-11/`), 4 of 7,816,802 target peptide rows sit at exactly 0.01 on `PEP_QValue` (PXD011314, PXD012753 x2, PXD047289), and none on `QValue Notch` in PXD058775, the one notch search. Decided from target PSMs only (ptmQtl S7); both findings written (the user, 2026-11-11). Real scratch ingests: PXD058775 reads `q_value_notch` (252 target peptidoforms pass) with `confidence_rule_fallback`; PXD057502 passes 0 against the q-value rule's 5,962, with `confidence_rule_fewer_peptides`; every other moved row is item 1's key change (`compare_item2.out`) | D53, D55 | **built** (local, unpushed) |
| 3 | `peptidoform_ions`: the six `Matched Ion *` columns under the per-search rule, `selected_by`; a bundle with none still builds. **The user, 2026-11-11:** the 138 ambiguous rows kept under their first option (MetaMorpheus writes that option's ions), contaminants left out as `peptidoforms_1pct` leaves them, an empty table builds. Measured on all 181 served deposits (`results/ions_2026-11-11/ion_cells.out`): 7,816,821 rows pass, no blank or `\|` ion cell, every count one whole number (`Matched Ion Counts` is a total, not per product type: the draft's description was wrong). Read verbatim with `TsvReader`, since mzLib's projection leaves the ion fields out. Scratch ingests of PXD058775, PXD057502, PXD011740, PXD034564: ion rows equal the file's passing rows, the peptidoforms with ions equal those passing the rule both ways, nothing else moves; PXD057502 writes no file (an empty table, as for any) and a scratch catalog of the four builds, 79 checks passed (`compare_item3.out`, `build_item3.log`). PXD034564 (TMT): 35.3 MB of a 108 MB bundle, 538 bytes/row | D53, G116 | **built** (local, unpushed) |
| 4 | Drop `psms.matched_ion_series`, `psms.matched_ion_count` (the user again, 2026-11-11). A parity bundle of Python 0.32.0's schema still writes them, where Python did, through `SchemaContract.RemovedColumns`; `McpParityTests` drops only their old descriptions from Python's answers. PXD058775 re-ingested: only the two columns go. **The empty cells were ours, not MetaMorpheus's:** every row of `AllPSMs.psmtsv` carries its ion list and count (PXD058775, PXD011740, PXD034564: 18,011, 176,667 and 495,857 of as many rows), so no MetaMorpheus issue was opened on the user's question | D56 | **built** (local, unpushed) |
| 5 | `gene_resolutions.ensembl_xref_agreement` (nullable, checked against agrees/silent/disagrees); `DefinitionId` v2 only when our mzLib carries #1578. **Built as the user said (2026-11-11):** the column and its enum are in 0.0.17 and empty; `LogsEngine.RowsFrom` refuses a word outside the three and any filled value on a v1 row, so filling it is the runner change that labels rows v2 once an mzLib release carries #1578 (still open 2026-11-11). Every engine artefact is re-run after the re-ingest anyway (a 0.0.16 artefact is refused). A 0.0.17 run on aging's `34a6a17d4cd77e4d` reproduced its stored rows exactly, the new column empty. **Found:** `RunnerTests.ARealResolutionReproducesThePythonRows` names `0138c5d37074ead8`, an artefact replaced at 1.4.0, so it has skipped since; it was pointed at `34a6a17d4cd77e4d` for one run only  **Filled 2026-11-12 with mzLib 1.0.598 (the user: "yes" to taking it):** every run is `logs:DEF-GENE-RESOLUTION v2` (rows, `run.json`, artefact id), `ensembl_xref_agreement` from mzLib's `GeneResolutionTsv.AgreementName`; a resolver writing no such column is refused, and so is a value that breaks logs 034's pairing with `ensembl_xref_agrees`. A scratch v2 run on the inputs of aging's v1 artefacts `34a6a17d4cd77e4d` (mouse proteome) and `399d453367acd65a` (its isoform overlay) equals them row for row on every v1 column; mouse entries agreeing 19,130, agreeing or silent 20,254, exactly logs 034's figures (`results/logs_v2_2026-11-12/`). Diff our first real v2 artefacts with logs, as offered (our 035) | D59, G133 | **built** (local, unpushed) |
| 6 | sha256 per table file in `bundle.json`; `datarepo verify` re-hashes on demand. **Built as the user said (2026-11-11):** a new `table_sha256` key beside `tables` (whose row counts keep their shape); `verify <bundle...>` or `--store` also re-hashes the copied sources (recorded since the first ingest), names each changed, missing or extra file, exits 1 if any; a bundle with no table checksums is "not verified", never passed. Not run by `build`. Engine artefacts not covered (D61 named bundles). A scratch PXD058775 verifies; a one-byte change is caught; all 568 bundles of aging's store read not verified, with every copied source matching (`results/verify_2026-11-11/`) | D61 | **built** (local, unpushed) |
| 7 | Run-scope counts. **No recount (the user, 2026-11-12, in place of our aging 119's promise): PXReprise already counts each run's share of the whole search's 1% set** (`pxreprise:DEF-*-1PCT-RUN` v1, 2026-10-11), in `qc_payload.json`. Built: (a) `QcPayload` reads `psms`/`peptides`/`protein_groups` as `*_1pct_whole_search` (`source = 'qc_payload.json'`) from the payload stage whose `provenance.json` names the bundle's search provenance by sha256 and whose payload is still the file it wrote, only beside a definition text carried at that version (a `/1` payload copies results.txt and gives nothing); payload + stage record are sources only when a count is stored. (b) results.txt's per-run PSM/peptide/group rows cite aging's per-file `aging:DEF-*-1PCT-RUN` (they cited the deposit-wide ones). (c) `run_counts_missing` (info) says which per-run counts results.txt did not write, why (`WriteIndividualFiles = false`, one run, none) and where the QC report's MS2 and the payload's counts are; four `qc_payload_*` findings for what the payload left out. No schema change. Measured on aging's `1e8c7c9d1821d38e` (191 deposits, `results/run_counts_2026-11-11/`): 68 `/2` payloads name their search, 118 `/1`, 4 none, PXD014274 two `/1` stages; the 47 deposits short of per-run results.txt counts all have a `/2` payload (PSMs and peptides on every run, groups on 8); **all 43 `/2` payloads with no per-run groups are isobaric searches with only `AllProteinGroups.tsv`, which PXReprise's builder does not read** (`QcPayloadBuilder.cs:652`; PXR-R60, sent as our 110. **PXReprise 111: fixed in their `9fcc209` for v0.4.47, unreleased; they rebuild the 43 payloads before our 1.5.0 re-ingest, which moves those 43 bundle ids, and want its date.** If v0.4.47 is not out by then, those bundles carry no per-run groups, with the finding). MS2 from the QC report (PXR-R51) and precursors from 1.1.14's lines were already read; `RunCountFindings` points to them | G125, U25 | **built** (local, unpushed) |
| 8 | `samples.condition` and `sample_characteristics.source` descriptions (+ `McpParityTests` masks). **The dropped-factor finding is dropped (D63, 2026-11-12):** factor values are kept instead (item 10). `community sdrf` also added to `runs.fraction_source`, which lists the same words | G127 | **built** (local, unpushed) |
| 9 | **Changed 2026-11-12 (the user: "re-search these files so we are not carrying around a bunch of rules and warnings specific to a handful of files"):** ingest refuses a multiplex search by MetaMorpheus up to 1.1.13 or of unknown release (MetaMorpheus #2941, fixed in 1.1.14), in place of the `isobaric_peptide_q_psm_level` warning and the build's #2941 exception, both removed; isobaric reader 4; dataRepo's note in `DEF-TMT-*` says so (QuantProject's text untouched). PXReprise re-searches PXD027548, PXD034564, PXD043296 and PXD051031 before the re-ingest (PXR-R61); one not re-searched by then is absent from the 1.5.0 catalog until it is. `results/isobaric_refusal_2026-11-12/` | D64, PXR-R61 | **built** (local, unpushed) |
| 10 | **Last:** sample sheets (D63, the user 2026-11-12). (a) In the bundle, only what the search used: the SDRF it read, the one it wrote and its design file, copied content-only (PXReprise v0.4.46 marks the output SDRF read-only), factor values INCLUDED and marked as the grouping the values were computed under (no more characteristics-only SDRFs). (b) Beside the bundle, a companion like items 12-13: every other SDRF made for the deposit (PRIDE's community annotation, sdrf's drafts, PXReprise's checked SDRF, the authors' own), each copy dated and hashed. (c) The catalog serves both together; each row names its sheet; sdrf's per-value source columns verbatim; nothing called verified. (a) and (b) ship together so nothing a bundle holds today is lost. Waits on sdrf's SDRF-D14 and SDRF-D15 and pride's PRIDE-D1. **Moved out of 1.5.0 (D67, the user 2026-11-12: "proceed according to your plan"):** it ships as a release of its own, timed with PXReprise's re-search wave (their 113), which brings the SDRFs it keeps; until then a bundle keeps what it holds today | U30, G130, G134, D63, D67 | **next release** |

**Build side (catalog format 17, no re-ingest):**

| # | item | source | status |
|---|---|---|---|
| 11 | `peptidoforms_1pct` reads the recorded rule; derivation id hashes it; descriptions and the site state the rule. **Built as the agent recommended and the user agreed (2026-11-12):** exactly the ingest's test (target; the value `datasets.confidence_rule` names strictly below 0.01; a NULL value or a rule the view does not name passes nothing, never a fallback); catalog format 17; `dataset_overview.confidence_rule` beside `n_peptidoforms_1pct`; the derivation id hashes the new SQL as it hashes any; the reconciliation and `metrics` stay on the q-value rule. Descriptions (view, overview, MCP `sql` tool, the docs) say it is not the producer's peptide count; the site reads "Peptidoforms at 1% (PEP q-value)" and "N peptidoforms pass 1% on its PEP q-value", and `llms.txt` and `datasets.json` carry the rule; a catalog before format 17 reads as it did. A parity catalog of Python 0.32.0 keeps the q-value view. Tests: every combination of rule, status and value through the view's SQL against the ingest's test; a real fixture ingest in both layouts; `McpParityTests` masks only the new texts. Scratch folder catalog of four real 0.0.17 bundles (`results/peptidoforms_1pct_2026-11-12/`): view = ion rows = a recount from each bundle, on every one (PXD011740 16,644 -> 22,357; PXD057502 5,962 -> 0; PXD058775 226 -> 252 on the notch). At release, the tutorial's printed counts move with the view | D55 | **built** (local, unpushed) |
| 12 | PRIDE records: operator fetch command, `_companion/pride/`, ptmQtl's three tables, the shared-raw-files view. **Built as agreed (the user: "build it", 2026-11-12):** `datarepo pride --store S [PXD...]` (default: every deposit with a bundle) keeps each record through mzLib's `PrideArchiveClient` under `<store>/_companion/pride/<accession>/<fetched>-<sha>/` (`record.json`, `fetch.json`: time, sha256, mzLib), add-only, nothing written when unchanged, `found = false` kept, an outage never kept; `build` reads the newest per deposit (bare accession), fetches nothing, refuses a record edited after its fetch; `deposit_records`, `deposit_contacts`, `deposit_references` (empty string and PubMed 0 are NULL) and the view `shared_raw_files`; each record's sha256 in the catalog id, not the release id. **E-mail is kept (D65, the user: "this is all public ... pride is public")**, reversing our 061's exclusion: `deposit_contacts.email`, free text verbatim (tell ptmQtl). All 194 of aging's deposits fetched, the view finds exactly our 061's cases (`results/pride_records_2026-11-12/`) | U20, U21, G120 | **built** (local, unpushed) |
| 13 | `deposit_facts` companion (`sdrf_column`). **Folded into item 10 (D66, the user 2026-11-12):** PXReprise's evidence now reaches its SDRF for every deposit and a check report, which D63 keeps beside the bundle; a separate table would give two answers. A facts file that still ships on its own goes beside the bundle as one more sheet, quotes verbatim. Asked PXR-R62 (our 114) | PXR-R46/R47, D66 | **folded into 10** |
| 14 | DATAREPO-88: (a) `isobaric_channels` view; (b) `quant_scale` from `qc_report.json`'s `sps_ms3` (PXR-R50; no manifest field); (c) aging layer 0.7.0, method-term table one row per isobaric dataset (aging 135); (d) aging's newest guidance text, re-read first. **Built as recommended and agreed (the user, 2026-11-12), with PXR-R54:** (a) `assays.plex`, `assays.design_sample_type` (verbatim) and the view; an `empty` channel is an assay with its values and no sample (`assays.sample_id` relaxed); (b) `runs.reporter_level` from `sps_ms3` at ingest, `dataset_overview.quant_scale` at build (`reporter_level_mixed` / `_not_recorded` never guessed); the 43 served isobaric searches read 31 MS2, 12 MS3, none mixed or unrecorded; PXD002528 (116 of 200 channels empty) keeps every value, 84 samples in place of 200 (`results/tmt_channels_2026-11-12/`); (c) layer 0.7.0: `method_scope` key, the two counts, `method_term_ids`, `age_effect_method_terms` keyed (dataset, response), two refusal values; a parity scope keeps 0.6.0's table (`SchemaContract.AddedStudyColumns`/`RemovedStudyColumns`); (d) aging's v1.4 sentence (unchanged since 11-09) in the layer's table text, `quant_scale`'s description, `llms.txt` and each dataset page. **aging must re-deliver its 0.6.0 study bundle with `datarepo study` after the swap** | G117, PXR-R54 | **built** (local, unpushed) |

**Not in 1.5.0 unless the user says:** the searched-database pointer (G131, build-side, release not chosen); GO per target set (G111);
the go refusal of isobaric deposits (G132, handed to QuantProject). **Already shipped:** split deposits (1.4.5, D58).

**Then:** tell PXReprise, aging, ptmQtl, QuantProject the shape; measure a whole-store scratch re-ingest; predict ids; PXReprise's week's
notice (PXR-R49); release on the user's word. **The build list is closed (D67, 2026-11-12):** items 1-9, 11, 12 and 14 are built, 13 is folded
into 10, and 10 moves to the next release. The whole-store scratch re-ingest started the same day on `aa9ad4b`.

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

- **As built (item 2, 2026-11-11; the user took all three recommendations):** mzLib's `QuantifiedPsmRule.ChooseTier`
  decides the whole search from its target PSMs (ptmQtl S7's form), not results.txt's PEP block. PEP trained: a target row
  with `PEP_QValue` strictly below 0.01. Not trained: a target row with `QValue Notch` strictly below 0.01. On all 181 served
  deposits, target-only and mzLib's documented every-PSM form give the same tier, and only PXD058775 is off PEP
  (`results/confidence_rule_2026-11-11/tier_targets_vs_all.out`).
- Targets are `T` and `ET` (pep 008; DATAREPO-87).
- A finding (`confidence_rule_fallback`) says when the fallback was used, and why. It cites mzLib's `QuantifiedPsmRule`, not
  MetaMorpheus's `PepQValueElseQValueNotch`: #2909, which adds that name, is still open (checked 2026-11-11).
- A second finding (`confidence_rule_fewer_peptides`) names both counts where the rule passes fewer target peptidoforms than
  1.4.5's q-value rule.

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
  Re-read #2941 for what `PEP_QValue` means in a multiplex `AllPeptides.psmtsv` before rewriting them. **Done 2026-11-12 (item 9):** PSM-level
  too, up to 1.1.13; such a search is now refused, the finding is gone, and QuantProject's sentence stays theirs (tell them at build).

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
  - **Settled 2026-11-12 (build list item 7):** no recount. PXReprise's payload already holds the whole-search counts under its own definitions, so
    the rule is theirs; the per-file rows now cite aging's per-file definitions. The promise in our aging 119 is met by PXReprise's counts, not ours:
    say so to aging at the announcement.
  - The isobaric finding's sentence on per-file `_Peptides.psmtsv` (`Ingester.cs:669`) stops being true under `tmt-dda@3`. Rewrite it with the #2941 re-read above.
    **Superseded 2026-11-12 (item 9):** the finding is removed; a multiplex search up to 1.1.13 is refused and re-searched.
- **Superseded 2026-11-12 by D63 (item 10): factor values are kept, not reported as dropped.** The plan as it stood:
- **A factor column left out with nothing beside it (G127, U27).** A curated SDRF's `factor value[...]` is dropped with only a note in `bundle.json`. Add a finding naming each one with no
  same-named characteristic. It is a row, so it rides this re-ingest. On today's store it fires on 5 deposits, and on PXD011740, PXD022196 and PXD002467 the fact survives only in sample names
  (`results/sdrf_route_2026-11-06/`).
- **`samples.condition`'s description (G127).** It says "e.g. HGPS, caloric restriction", and `Sdrf.cs:277` fills it only from `characteristics[disease]` (5 of 196 deposits). Say what it holds, and
  point a reader to `sample_characteristics` for treatments. A changed description also needs its `McpParityTests` mask.
- **`sample_characteristics.source`'s description (G127, sdrf 035).** Add sdrf's new word, `community sdrf` (bigbio's file on PRIDE), from mzLib #1557. The column is verbatim and not an enum, so no ingest fails without it.
- **A sha256 per table in `bundle.json`? Not decided (G128).** Today it holds row counts and no table hashes, so a rewrite of a stored table cannot be detected from the store, and a re-ingest would replace the only evidence. This schema bump is the free moment to add one. `build` would then be able to check it, at a cost not yet measured. **Raise with the user before building.**
- **SDRF drafts (G127).** If sdrf's drafts become `operator_sdrf` entries, this re-ingest carries them at no extra cost. sdrf's hold and G68 fix come first, and each draft must group files as its
  search's design does. PXReprise is asked to weigh this when answering PXR-R49.
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
