# 1.5.0's whole-store scratch re-ingest (2026-11-12)

The measurement 1.5.0's date waits on (PXReprise 098: a week's notice after the store is measured on a copy). Every
`include` deposit of aging's manifest was re-ingested with the 1.5.0 branch and compared with the bundle aging serves.
Each difference is traced to one of 1.5.0's items, or to an input that changed on disk.

**Result:**
- **192 of 197 deposits re-ingested.** The five refused are the four MetaMorpheus 1.1.13 TMT searches item 9 refuses
  (PXD027548, PXD034564, PXD043296, PXD051031; PXReprise re-searches them, PXR-R61) and PXD060120, which has never been
  served (below).
- **Every difference in rows is explained** by items 1, 2, 3, 7, 9 and 14. No input changed on disk since it was served.
- **Wall time: 6 h 14 min**, three ingests at a time, beside PXReprise's running batch (1.4.0: 5.0 h for 168 deposits).
- Every bundle id moves, as a new ingest path must. The new ids are `compare_deposits.tsv`'s `new_bundle`. They hold for
  unchanged inputs, **except the 39 isobaric deposits**, whose QC payloads PXReprise rebuilds before the re-ingest
  (PXR-R60, v0.4.47): a rebuilt payload is a new source, so those 39 ids move again.

## How

- **Code:** `feat/1.5.0` at `aa9ad4b`, published self-contained as `datarepo 1.5.0-scratch.aa9ad4b` (ingest path `cs-1.3.0`,
  schema 0.0.17, mzLib 1.0.598). The commits after it on the branch change only the plan.
- **Inputs:** a snapshot of `F:\aging_data\batch\manifest.yaml` taken at 23:33 UTC (263 entries: 197 `include`, 60 `exclude`,
  5 `hold`, 1 `superseded`).
  - Called as PXReprise calls it: `ingest <manifest> <accession> --store <scratch> --json`, three at a time, largest first
    (`one.sh`, `order.txt`).
  - It read `F:\aging_data` only and wrote only under `F:\datarepo_scratch_150\reingest150`.
  - Before starting, `inputs.py` found every include entry's search folder, `search_results` folder and searched databases
    present (1.4.0 had found 24 deposits reading deleted pin folders).
- **Baseline:** each deposit's bundle in aging's serving catalog `75e1c0c82f8dc965` (release `d77dcedec4be665a`, built by
  1.4.5, format 16; `prep.py`, `baseline.tsv`). 196 served; PXD060120 never was.
- **Comparison:**
  - `compare.py`: both ids, rows per table, sources changed (by role and sha256), finding codes gone or new.
  - `explain.py`, `explain2.py`, `explain3.py` (with their `.out`): the cause of each difference, and exact checks.
- **Not covered by row counts:** values that change inside an unchanged count, such as a peptidoform key written with a
  Unimod accession where it had a mass (item 1), and the new columns (`assays.design_sample_type`, `runs.reporter_level`,
  `assays.plex`, `datasets.confidence_rule`, `peptidoforms.best_pep_q_value`). These were measured where they were built.

## Timing

- **Wall time:** 23:34 to 05:48 UTC, 6 h 14 min, three ingests at a time.
- **Serial time:** 18.7 h, about 90 s per GB of source (743 GB).
- **Per deposit:** median 199 s, 90th percentile 812 s.
- **Longest:** PXD034029 3,262 s; PXD002467 2,941 s (1.4.0: 6,521 s); PXD017505 2,077 s; PXD048079 1,904 s; PXD045806
  1,817 s.
- **Output:** 36.3 GB of bundles where the served ones are 33.2 GB: +3.1 GB, of which `peptidoform_ions` is 2.7 GB.
- **Disk:** F: had 161 GB free at the end. A real re-ingest writes the new bundles beside the old ones, so it needs about
  37 GB until the old ones are removed.

## Engines and the catalog (the rest of the window)

After the re-ingest, an operator must run every engine again, since the build refuses a 0.0.16 artefact beside 0.0.17
bundles. Then they build. Both were run on the scratch store with the same binary (`engines.py`, `engines_fix.py`, `build.sh`).

- **Engines** use the fixed inputs each serving artefact's `run.json` records (go.obo, aging's organelle map, logs' Ensembl
  116 gene sets and cross-references, the Compara 116 snapshot):
  - `logs.register_orthology`: 3 s.
  - `logs.resolve_genes`: about 2 min for three species.
  - `go.annotate_groups`: 1,538 s (26 min) for 153 label-free searches.
  - Total: about 28 min, almost all of it GO.
- **First build:** 377 s (6.3 min), 260 s of it deriving all 192 deposits. 3,979 checks passed. An unchanged rebuild says
  `unchanged` in 1 s. The rebuild after the gene fix (below) reused every deposit: 118 s, 3,981 checks passed, folder
  catalog `9e936aa4e7e255d0` (release `fe86c87399cfe502`), format 17, 554 MB with its derived tables.
- **So the whole window is about 7 h:** 6 h 14 min of ingest, then 28 min of engines, then 6 min of build. This assumes
  three ingests at a time, as here. aging's study bundle must also be delivered again at layer 0.7.0 (its rows are not
  re-derived), and that is aging's step.
- **Against the serving catalog, on the 192 deposits both hold** (`compare_catalog.py` + `.out`):
  - Equal in every deposit: `protein_genes` (3,314,410 rows), `protein_localizations` (17,295,199) and
    `protein_groups_1pct` (696,304).
  - `peptidoforms_1pct` goes from 6,714,143 to 8,407,134 rows: the per-search confidence rule (items 2 and 11, D55), on 191
    deposits by PEP q-value and on one by the notch.
  - New tables: `peptidoform_ions` (8,407,167 rows), `isobaric_channels` (15,758), `deposit_records`, `deposit_contacts`,
    `deposit_references`, `shared_raw_files` (8) and `age_effect_method_terms`. New overview columns: `confidence_rule` and
    `quant_scale` (153 `label_free_apex`, 29 `reporter_ms2`, 10 `reporter_ms3`).
  - go covers 153 of 192 bundles. The 39 it does not are the isobaric ones, as on the serving catalog (QuantProject's
    DATAREPO-D15).
- **`peptidoform_ions` has 33 rows more than `peptidoforms_1pct`**, one in each of 33 deposits. In each, an ambiguous row
  (`A|B`) whose first option is another row's sequence gives one key two ion rows, as the table's description says (the key
  is `peptidoform_id`, `full_sequence`). Every ion row's peptidoform is in the view, and every view row has ions (`gaps.out`).
- **An operator trap, found by making it.** `engines.py` first replayed each serving logs artefact for the deposits it was
  first requested for. Three of those had been requested only for deposits now excluded, so two databases went unresolved
  and six deposits (PXD005035, PXD005123, PXD006578, PXD006589, PXD025315, PXD027895) lost almost all their gene names
  (21,791 to 70 rows for PXD005035).
  - The build still passed all its checks. It named the gap only in a `note`: "logs.resolve_genes coverage (databases with
    an artefact): 39 of 41; no artefact for ...".
  - Running `logs.resolve_genes` on every re-ingested deposit of each species (`engines_fix.py`) closed it, and the rebuild
    above equals the serving catalog.
  - **For PXReprise:** after the re-ingest, run each engine on every deposit, not on the deposits the old artefacts name,
    and read the coverage notes before pointing `latest.json`.
- **PRIDE records:** the scratch store carries a copy of the records fetched in an earlier trial (`datarepo pride`), which
  never asked for PXD045806, so 190 of 191 deposits have one. A real `datarepo pride --store <store>` with no accessions
  fetches all of them.

## Every difference, by cause

| cause | deposits | what changed |
|---|---|---|
| item 3 (`peptidoform_ions`) | 191 | the new table. PXD057502 has none: no peptidoform passes its rule (item 2), so it writes no file, as built |
| definitions (items 2, 3, 7) | 192 | the definitions the new rows cite. On 139 deposits results.txt's per-run rows now cite `aging:DEF-PSM/PEPTIDE/PROTEINGROUP-1PCT-RUN` (item 7 b) |
| item 7 (`qc_payload.json`) | 69 | the payload and its stage record become sources; +2 to +480 `metrics` rows, **all** from `qc_payload.json` (no other `metrics` row moves in count, `explain3.out` c); `provenance_records` +1. Label-free: PSMs, peptides and groups per run. **Isobaric (all 39): PSMs and peptides only**, because PXReprise's builder does not yet read `AllProteinGroups.tsv` (PXR-R60) |
| item 7 (`run_counts_missing`) | 53 | a new info finding naming the per-run counts results.txt did not write and where they are |
| item 2 (confidence rule) | 23 | `confidence_rule_fewer_peptides` on 22 deposits (PXD057502 passes 0); `confidence_rule_fallback` on PXD058775 (no PEP trained; the notch rule) |
| item 14 (an empty channel has no sample) | 21 | 8 to 206 fewer `samples`, all isobaric. **Every sample that goes was tied only to channels the search's design marks `empty`**, and no `empty` assay keeps a sample (`explain3.out` d). Assays and values are unchanged in count |
| item 14 (isobaric reader) | 39 | the `isobaric_reader` declaration moves (reader version), as built |
| item 1 (mzLib 1.0.598: keys) | 15 + 4 | `unresolved_modifications` is gone from 15 MetaMorpheus 1.1.14 deposits: the UniProt names (N6-crotonyllysine, 3'-nitrotyrosine, ...) now map to Unimod. Four deposits lose one peptidoform each, a merge (below) |
| item 9 (1.1.13 TMT refused) | 4 | not re-ingested, as built |
| no change but the above | 103 | only definitions and the new ions table |

- **The four merges** (`explain3.out` a). In each, one peptide was written two ways: `K[+86.000394]` (a UniProt malonyl name
  mzLib now links to `UNIMOD:747`) and `K[UNIMOD:747]` (the Unimod name). Both are now one key, with both engine sequences
  and the sum of their PSMs: PXD018999, PXD025240, PXD057545 and PXD077298, each one target row. Every other moved key in
  those deposits is a mass tag written as its accession, one for one.
- **Tables whose row count did not move in any deposit:** `psms`, `proteins`, `protein_groups`, `quant_values`, `ptm_sites`,
  `ptm_stoichiometry`, `runs`, `assays`, `search_modifications_declared`.

## Found on the way

1. **PXD060120's design names 12 of its 18 channels.** It was searched (MetaMorpheus 1.1.14, `tmt-dda@4`, 2026-11-12) with a
   TMTpro 18 kit read from the spectra, and its `TmtDesign.txt` has rows for 126 to 132N only. MetaMorpheus wrote all 18
   channels, so `PeptideQuantification.tsv` has six columns (132C to 135N) that no design row labels. The ingest places a
   column by its file and channel, never by position, so it refuses, as it has since 1.4.1. **For PXReprise:** a design
   naming the six as `empty` would let it ingest; whether that needs a re-search is theirs to say.
2. **None of the four `qc_payload_*` findings fired.** Every payload that names its search was read whole.

## Files

- `prep.py`, `inputs.py`, `one.sh`, `order.txt`, `baseline.tsv`, `progress.log`: the run.
- `compare.py`, `compare_deposits.tsv` (the predicted ids), `compare_tables.tsv`: the comparison.
- `explain.py`, `explain2.py` + `.out`, `explain3.py` + `.out`: the causes.
- `engines.py`, `engines_fix.py`, `engines.log`; `build.sh`, `build_summary.txt` (the full `-v` log lists every check and
  stays in scratch); `compare_catalog.py` + `.out`; `gaps.py` + `.out`: the engines and the catalog.
- The scratch bundles are not kept here; they stay under `F:\datarepo_scratch_150\reingest150\store` until 1.5.0 ships, and
  no scratch bundle is ever served.
