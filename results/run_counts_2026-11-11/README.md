# Per-run counts (1.5.0 build list item 7), 2026-11-11 and 2026-11-12

**The question.** 43 of the 187 deposits aging served on 2026-11-11 had no per-run PSM, peptide or protein-group row in
`metrics`, and nothing said so. Their searches set `WriteIndividualFiles = false` (PXReprise's `@14` profiles). MetaMorpheus
writes results.txt's per-file lines only when that setting is true and two or more files were searched
(`PostSearchAnalysisTask.cs:91-101`, `:1221` at `6e152da70`).

**The user's ruling (2026-11-12):** no dataRepo recount. PXReprise already counts each run's share of the whole search's 1% set
(`pxreprise:DEF-PSM-1PCT-RUN`, `DEF-PEPTIDE-1PCT-RUN`, `DEF-PROTEINGROUP-1PCT-RUN` v1, defined 2026-10-11) in `05_qc/qc_payload.json`.
The ruling has four parts:
- read those counts, under PXReprise's definitions and names of their own;
- relabel results.txt's per-run rows with aging's per-file definitions;
- keep the note;
- tell PXReprise its builder misses the isobaric searches' protein groups.

Everything here is read-only over `F:/aging_data`; the scratch stores are under `F:/datarepo_scratch_150/`.

## Measurements (read-only)

| file | what it shows |
|---|---|
| `runcounts_q.py`, `short43.txt` | Catalog `fe6a49db1fd6fddc` (2026-11-11, 187 deposits). 43 deposits have no per-run results.txt PSM/peptide/group rows: 5 on MetaMorpheus 1.1.13 with no per-run line at all, and 38 on 1.1.14. 37 of the 1.1.14 ones keep the precursor and MS2 lines (MetaMorpheus #2955). The 38th, PXD027232, is a one-run search. The QC report's `ms2` covers every run of all 43 |
| `runcounts_q_2026-11-12.out` | The same query on catalog `1e8c7c9d1821d38e` (2026-11-12, 191 deposits): **47** short. 8 are on 1.1.13 with no line, 38 on 1.1.14 with the scan lines, and 1 is a one-run 1.1.14 search. The 4 deposits added since the first count are PXD006570, PXD006571, PXD031710 and PXD053611. **All 47 have a `qc-payload/2` payload naming their search:** each run gets PSM and peptide counts. 8 also get protein-group counts; the other 39 are isobaric and get none (below) |
| `qc_payload_q.py`, `.out` | Which deposits have a payload, of which schema, and with which per-file counts and definitions. No bundle copied one |
| `groups_q.py` | Side check: every served deposit has `protein_groups` rows. Isobaric searches are read from `AllProteinGroups.tsv` |
| `payload_survey.py`, `.out` | Catalog `1e8c7c9d1821d38e` (2026-11-12, 191 deposits), with each payload found the way ingest finds it. Counts are below |

What `payload_survey` found:
- 68 deposits have a `qc-payload/2` payload whose stage names their search. In all 68, every file is a run of the bundle, except PXD023647's twelfth file, which has no counts.
- 118 deposits have a `/1` payload, which counts under aging's per-file definitions, so ingest reads nothing from it.
- 4 have no payload stage: PXD027318, PXD032202, PXD036557 and PXD052189.
- PXD014274 has two `/1` stages, `05_qc` and `05_qc.bak-20261012-excluded-true`.

**43 of the 68 `/2` payloads give no per-run `protein_groups`.** All 43 are isobaric searches (40 TMT, 3 iTRAQ) that wrote only `AllProteinGroups.tsv`.
- That file has `Unique Peptides` and `Shared Peptides`.
- PXReprise's builder reads only `AllQuantifiedProteinGroups.tsv` (`QcPayloadBuilder.cs:652` at `15ff335`), and its note blames the columns.
- This is PXReprise's bug, asked as PXR-R60.

## Scratch ingests

| file | what it shows |
|---|---|
| `ingest_item7.log`, `show_note.py`, `show_note.out` | The first half (2026-11-11, `store_item7`, CLI `cli_item7`): the `run_counts_missing` note alone on PXD027232, PXD021757, PXD007758, PXD058775 |
| `ingest_item7b_{a,b,c}.log`, `compare_item7b.py`, `compare_item7b.out` | The whole item (2026-11-12, `store_item7b`, CLI `cli_item7b`) on eight deposits. Each new bundle is compared table by table with its `store_item7` bundle where one exists |

Results of the eight ingests (`compare_item7b.out`):

| deposit | new bundle | what it shows |
|---|---|---|
| PXD021757 (1.1.14 TMT, 8 runs, `/2`) | `2e123f04bccb92ff` | Gains `psms_` and `peptides_1pct_whole_search` on all 8 runs; the PSMs sum to results.txt's 33,860. No protein groups (PXR-R60). Against `store_item7`, only these change: 16 metric rows, 2 definitions, the payload stage's provenance record, the reworded note, and the two sources |
| PXD027232 (1.1.14 TMT, one run, `/2`) | `3092c336f84cc096` | Its one run: 772 PSMs and 580 peptides, results.txt's deposit-wide counts exactly |
| PXD007758 (1.1.13, 9 runs, `/2`) | `61b79edd1c53f5d6` | All three counts on all 9 runs. The PSMs sum to 223,894, the bundle's own count; results.txt says 223,901, the usual small mismatch. 27 metric rows, 3 definitions |
| PXD005035 (1.1.13, 141 runs, `/2`) | `0dd30b36e0a39c27` | All three counts on all 141 runs; PSMs sum to 4,158,349 (results.txt 4,160,371) |
| PXD023647 (TMT, 11 runs, `/2`) | `06509b9b02d0e8a3` | PSMs and peptides on 11 runs. The payload's twelfth file has no counts, names no run, and gives no finding |
| PXD058775 (`/1`, per-file lines) | `0b92797364a7e76f`, unchanged | Only its 54 per-file rows change: they now cite `aging:DEF-*-1PCT-RUN`, beside 3 new definition texts. The `/1` payload is not read and is no source, so the id holds. That is right only because `cs-1.3.0` has never been released |
| PXD001054 (`/1`, per-file lines) | `9e29e01d0522ff35` | Per-file rows relabelled, nothing read from the payload. The per-file PSMs sum to 55,787 against 55,832: per-file FDR, never summed |
| PXD014274 (two `/1` stages) | `610cb3c006b2da3b` | Nothing read and no finding, since neither stage gives a count |

No `qc_payload_*` finding fired on any of the eight. Full test suite (non-RealData): 828 passed, 1 skipped, 1 failed. The failure is
`TheTutorialPrintsWhatTheProgramPrints`, which fails until the release reruns the tutorial.
