# dataRepo's part of the public-data contract (D48, G94)

**Status, 2026-10-19: step 1 is BUILT on master, not yet released** (`5afea11`, then the site's finding order). Measured
on aging's store, pinned to the serving catalog's 169 bundles:
- the build took 8.4 minutes against 1 to 3 hours, and the catalog file is 298 MB against 62.4 GiB;
- all 47 tables and views both hold are equal (counts, plus checksums below 10M rows);
- the site regenerated from it is byte-identical apart from a one-time reordering of tied findings;
- `mcp --check` on the folder answers in 0.6 s.

What is not built: `--data-root` for a hosted URL (the views name the local store; hosting is PXReprise's step 3), and
the per-deposit derived tables of step 2. The largest copied tables are `protein_datasets` (5.0M rows) and
`protein_genes` (2.6M), both per-deposit work for step 2.

**Original status: PLAN, 2026-10-11.** The contract is PXReprise's
`design/PLAN_public-data.md` (efb70cb), decided by the user as PXReprise D41 and adopted here as D48. PXReprise owns the
architecture. This file is how dataRepo meets the rules the contract assigns to it (rules 3 on the catalog side, 4,
5, 9 and 10), in what order, at what cost, and where we would refine a rule rather than let it lapse. The answer to
PXReprise's PXR-R15 and PXR-R16 is taken from here.

## 1. Measured first (2026-10-11, aging's real store, scratch only)

A throwaway prototype (`results/public_data_2026-10-11/views_proto.py` and `derived_proto.py`, Python, never shipped)
built a catalog of views over the newest bundle of every deposit, on DuckDB 1.5.5. The store was read only.

| fact | value |
|---|---|
| bundles (newest per deposit, schema 0.0.15) | 109 |
| Parquet in them | 8.65 GB: PSMs 6.97, peptidoforms 1.25, everything else 0.43 |
| the catalog as built today | 28 GB, about 45 min per publish (PXReprise's figures) |
| **a catalog of views** (16 tables, PSMs left out) plus one corpus index (`protein_index`, 81,132 accessions) | **0.5 s to build, 1.3 MB** |
| `count(*)` over a view (protein groups 527,405; peptidoforms 22.4M; quant values 41.3M) | 0.02 s each, from Parquet metadata |
| one dataset's quant values (`WHERE dataset_id = ...`) | 0.01 s. The plan shows **1 of 109 files scanned**, even though `dataset_id` is derived from the path |
| one protein (P04406) across every dataset: its quant values, joined to its groups | 0.28 s; 1,622 values in 42 datasets |
| one protein in the corpus index | under 0.01 s |
| **today's derived tables** (`BuildDerived`'s SQL unchanged, over the views, PSM counts left out) | **17.1 s, catalog 39.3 MB** |

The derived tables, one by one: `dataset_overview` 1.0 s (109 rows); `protein_datasets` 5.9 s (2,703,590 rows);
`protein_index` 2.9 s (127,865); `search_modifications_placed` 2.3 s (3,468); `peptide_index` 5.0 s (542,368). No ART
indexes were built.

**At scale.** Linear in deposits, 4,350 deposits would take about 11 minutes and 1.6 GB, just over both of the
contract's limits (10 minutes, 1 GB). Most of it is per-deposit: `protein_datasets` is one row per dataset and
protein, and `search_modifications_placed` and `dataset_overview` are per dataset. Computed once per deposit and
stored beside the bundle (step 2), the publish only aggregates the corpus-wide indexes (`protein_index`,
`peptide_index`) from those per-deposit tables.

Two facts about the bundles that the design has to absorb:
- **10 of the 17 bundle tables carry no `dataset_id`**, and **none carries `bundle_id`** (assays, definitions,
  metrics, proteins, psms, ptm_stoichiometry, quant_values, ...). Today's build adds both while copying. A view
  derives them from the file's path, `<store>/<dataset>/<bundle>/<table>.parquet`. File pruning still works (above).
- **A table with no rows is not written.** `sample_characteristics` is absent from 93 of 109 bundles. A view unions
  the files that exist, and a table that no selected bundle has becomes a typed empty view, so D10's "every schema
  table exists even when empty" still holds.

And one about D14's sandbox, which the MCP server must keep:
- With `enable_external_access = false` alone, every view fails: the store is external.
- `SET allowed_directories = ['<store>/']`, then `SET enable_external_access = false`, then
  `SET lock_configuration = true`, in that order, gives:
  - files under the store read;
  - a file outside, `..` out of the store, unlocking, and `ATTACH` are all refused.
  - (`allowed_directories` cannot be passed when connecting: DuckDB refuses it before the database starts.)
- **But the check runs on the path as written.** A view with paths relative to the store, resolved through
  `file_search_path`, is refused. So the views carry absolute paths under one data root (section 3).

## 2. What exists today (`CatalogBuilder.BuildCatalog`, 1.3.2)

- **Copied:** 30 core tables, each `CREATE TABLE AS ... UNION ALL BY NAME` over the bundles' Parquet, with
  `dataset_id` and `bundle_id` restated (`Catalog.cs` `LoadTables`). A table no bundle has is created empty and typed.
  - `samples` then gains four `*_name` columns by ALTER and UPDATE (G74, D32).
  - The three go tables gain the go artefacts' rows by INSERT. `dataset_candidates` gains the census's rows.
- **Derived at build** (`BuildDerived`):
  - views: `psms_1pct`, `peptidoforms_1pct`, `protein_groups_1pct` (D10's acceptance rule), `ptm_sites_by_chemistry`;
  - tables: `dataset_overview` (reads PSMs), `protein_datasets`, `protein_index`, `search_modifications_placed`,
    `peptide_index` (all four read `peptidoforms_1pct`).
  - From engines: `dataset_databases`, `protein_genes`, `gene_resolutions`.
- **From the manifest:** `dataset_annotations`, `run_exclusions`, census rows. **Study layer:** 9 aging tables.
- **Metadata:** `catalog_meta`, `catalog_bundles`, `catalog_study_bundles`, `catalog_engine_artefacts`,
  `catalog_tables` (a `count(*)` of every table and view), `catalog_checks`.
- **ART indexes** on 21 columns, PSMs included, after the checks pass.
- **Checks:**
  - `CheckRowCounts` (`count(*)` per bundle and table);
  - `CheckIntegrity`, a whole-table re-run of ingest's own `Integrity.Check` lists (uniqueness and references; the
    catalog skips the composite identifiers and compares typed values where ingest compares strings);
  - the engine, go, orthology, study and run-exclusion checks, which are small.
- **The MCP sandbox** opens the file READ_ONLY with `enable_external_access = false` and
  `disabled_filesystems = 'LocalFileSystem'` (D14). The second also refuses ATTACH. **Both refuse views over the
  store**, so the sandbox changes (section 1: `allowed_directories`, measured).
- **Assumes one self-contained file:** `ReplaceFile`; the file-changed check (one file's write time and length);
  the comment at `Catalog.cs:147` ("It is one file ... D1: it has to move").
- **The site** opens the catalog read-only with no sandbox. It never queries `psms`, but shows `n_psms_1pct` and
  `n_psms_all` from `dataset_overview`. For Croissant it opens bundle Parquet files directly, PSMs included.

## 3. Step 1: the catalog as views, versioned files, a `latest` pointer (no re-ingest)

- **One file per build:** `catalog-<catalog_id>.duckdb`, beside a small `latest.json` naming the current file,
  its `catalog_id` and `release_id`, and when it was built. A build writes a new file and then rewrites
  `latest.json` (write to a temporary file, then rename; a pointer is tiny, so the swap is atomic where a 28 GB
  file was not). **No file a reader may hold is ever replaced.** `--out` naming a `.duckdb` file keeps today's
  behaviour, for the tutorial and for anyone who wants one movable file.
- **Views, not copies.** Each bundle table becomes a view over the selected bundles' files, with `dataset_id` and
  `bundle_id` derived from the path where the Parquet lacks them. The selection rules stay D10's and D11's: the
  manifest is the contract, a dataset with several bundles is pinned or taken newest, and a release pins every
  bundle.
- **Absolute paths under one data root.** `build --data-root <dir or URL>` (default: the store) writes the views'
  paths, and the MCP server allows exactly that root (section 1). A local catalog and a hosted catalog are two
  builds of the same release: same `release_id`, different `catalog_id`, each about a megabyte and seconds to
  write.
- **What stays materialised:** the corpus-wide derived tables (the indexes, `dataset_overview`, the catalog's own
  metadata and checks, the manifest-derived tables). They are small. Section 2 says which they are and what they
  read.
- **Checks move to where they are cheap.** Every per-bundle uniqueness and reference check already runs at ingest
  (`Integrity.cs`) and is recorded in `bundle.json`. The build keeps the cross-bundle checks: one bundle per
  dataset, one schema version, each table's row count from Parquet metadata against `bundle.json`. It drops the
  full-table re-scans.
- **Identity (rule 9).** Two ids, because they identify two different things:
  - `release_id`: the hash of the sorted bundle ids and the schema version, as rule 9 says. It names the data.
  - `catalog_id`: today's hash, which includes the builder's version and `CATALOG_VERSION`. It names one catalog
    file, whose views and derived tables are code. Our standing rule is that anything reaching a written row is an
    input to its hash; dropping the builder from it would give two builders' different indexes one id.
  - MCP provenance (D20) carries both.
- **Old files.** `datarepo build --keep <n>` deletes catalog files older than the newest n that no release names.
  Deleting a file a reader holds is allowed on Windows when the holder permits it, and DuckDB does (measured for
  1.3.2). The reader keeps its copy.
- **Format.** `CATALOG_VERSION` 10 to 11 (the ptmQtl branch's 11 moves to 12). No schema change, no re-ingest.

## 4. Step 2: PSMs out of the catalog; per-deposit work done once

**Measured before building it (2026-10-19, aging's store, 170 bundles, pinned to aging's first folder catalog
`32c632fd8bc361d4`).** `build` now prints how long each phase took. A 1.3.5-code folder build took 573 s:

| phase | seconds |
|---|---:|
| tables (views) | 3.8 |
| derived | 77.9 |
| study and engines | 21.8 |
| manifest | 0.8 |
| **checks** | **431.7** |
| indexes | 11.0 |
| catalog tables | 24.2 |
| move | 0.1 |

Three quarters of a publish was the row-count check: `count(*) ... WHERE bundle_id = ?` over a view, once per bundle and
table (3,310 times), listing every bundle's file each time (0.13 s each). A Parquet file's footer holds its row count, so
2a reads all footers in one query instead. PSM counts: `bundle.json` already holds both of `dataset_overview`'s, and on
all 170 bundles they equal what 1.3.5's views counted (`n_psms_1pct` = the reconciliation's `psms_target_1pct`,
`n_psms_all` = `tables.psms`).

**2a built and measured (2026-10-19, same inputs): 144 s against 573 s.** The engine and go row checks had the same
shape (one `count(*)` per artefact and table over a view, 72 s) and read footers too. Every table both catalogs hold has
the same rows; the site is identical apart from `llms.txt`'s PSM sentence. What is left, by phase:

| phase | seconds |
|---|---:|
| derived: protein_datasets | 21.4 |
| derived: protein_index | 19.2 |
| derived: peptide_index | 18.3 |
| derived: modifications | 9.4 |
| derived: overview | 5.8 |
| study and engines | 23.7 |
| catalog tables (`count(*)` of every table and view) | 18.8 |
| indexes | 11.9 |
| everything else | 15 |

Linear in deposits, that is about an hour at 4,350, so 2b is what meets the contract at scale: the derived tables are
per deposit except `protein_index` and `peptide_index`, and those aggregate per-deposit rows.

**2b built and measured (2026-10-19, same inputs).** A folder keeps each deposit's derived rows under
`derived/<derivation id>/<dataset>/<bundle>/`, computed once from that deposit's files with the corpus build's own SQL,
and reused while the derivation id (that SQL, the catalog format, the schema, DuckDB's version) is the same. The two
indexes aggregate per-deposit partial rows.
- The first build derived all 170 deposits once: 155 s in all, 90 s of it the deposits. **A rebuild took 61 s**, with
  every deposit reused in 1.0 s.
- `dataset_overview`, `protein_datasets`, `protein_index`, `peptide_index` and `search_modifications_placed` have the
  same rows as 2a's (checksums). The site regenerated from it is identical.
- The derived directory is 155 MB (0.9 MB a deposit); the catalog file is 132 MB, against 298 MB.
- What is left in a warm publish: study and engines 17 s, `catalog_tables`' counts 15 s, `peptide_index` 9 s,
  `protein_index` 7 s. Projected to 4,350 deposits, the two indexes and the counts grow with the rows; the per-deposit
  work is done once per deposit.

Not done in 2b: the engine-derived tables (`protein_genes`, `dataset_databases`) are still built at every publish, and
`--keep` does not prune derived directories of an older derivation id.

ptmQtl answered PXReprise's PXR-P14 on 2026-10-11 (ptmQtl 014 in the PXReprise thread): it needs every target PSM of a
search, one deposit at a time, and removing `psms` and `psms_1pct` from the catalog breaks only its own two exporters and
two scripts. Tell ptmQtl before releasing 2a.

- **PSMs leave the catalog.** No `psms` view. They stay in every bundle, readable with DuckDB over the store.
  Everything that reads PSMs at build moves to the counts each bundle already recorded at ingest (`bundle.json`
  table counts and the reconciliation's `psms_target_1pct`). Section 7 lists every reader.
- **Peptidoforms stay as a view** in the local catalog. For hosting (contract step 3), the peptide tier can be a
  second catalog over the same release.
- **Per-deposit work runs once (rule 5), and we would refine its wording.** Gene resolution (`logs.resolve_genes`)
  and GO annotation (`go.annotate_groups`) become steps the batch runs right after each ingest, instead of at every
  publish. Their results stay content-addressed artefacts beside the bundle, keyed to it, rather than inside it.
  The bundle is immutable and its id hashes its inputs. GO's result depends on go.obo and the category map, which
  change on go's schedule, not the deposit's. Inside the bundle, every go.obo release would make a new bundle of
  every deposit. The catalog reads artefacts as views too.
- **Nothing else per-deposit exists yet** on our side. QuantProject's statistics, when they come, follow the same
  pattern.

## 5. DuckLake (PXR-R16): adopt later; the release stays a frozen list of bundle ids

- **Maturity: real, and moving.**
  - Spec and extension 1.0 shipped 2026-04-13, declared production-ready, with backward compatibility promised.
  - Spec 1.1 and extension 2.0 are due 2026-10-21, tentatively.
  - The extension loads on our DuckDB 1.5.5, though the compatibility matrix stops at 1.5.2.
- **Fit: partial.**
  - Registration without a rewrite works, and snapshots as releases work.
  - But DuckLake **takes ownership of every file it registers**. One routine `CHECKPOINT`, with default settings,
    merged the registered bundle files into its own files and scheduled the originals for deletion, including a
    bundle outside its data path. A later cleanup deletes them. That is the opposite of rule 1 (nothing published
    is ever modified).
  - Static hosting worked only after hand-editing its metadata to relative paths, which its API cannot write.
- **Recommendation:**
  - Do not put DuckLake under the immutable store now.
  - Keep rule 9's frozen list of bundle ids as the release, written into the catalog (step 1).
  - Re-test after spec 1.1, on its ownership model and on relative paths.
  - If adopted later, DuckLake should hold copies or a mirror, never the store itself.

The evidence is in section 8.

## 6. Order and size

One release per step. Each is verified the way the C# port was: the new catalog must answer like the old one, row
by row, on aging's real store (`DataRepo.Parity compare`), before anyone switches.

| step | work | rough size |
|---|---|---|
| **1a** | views instead of copies: path-derived ids, typed empty views, `samples` names as a view, go and engine rows as views over artefacts | 2 days |
| 1b | `catalog-<id>.duckdb` plus `latest.json`, `--data-root`, `--keep` | half a day |
| 1c | checks: row counts from Parquet metadata; drop the re-run of ingest's integrity checks | half a day |
| 1d | `release_id` beside `catalog_id`; both in MCP provenance (D20) | half a day |
| 1e | MCP: open through `latest.json`; the sandbox with `allowed_directories` in place of `disabled_filesystems`; tests that a file outside, `..` and ATTACH stay refused (D14's class) | 1 day |
| 1f | parity against today's catalog on aging's store; the site byte-compared | 1 day |
| | **step 1 total, released as the next minor version (no re-ingest)** | **about a week** |
| **2a** | PSMs out: `dataset_overview` takes its PSM counts from `bundle.json`; no `psms` or `psms_1pct` view, no PSM indexes; MCP and site prose; docs | 1-2 days |
| 2b | per-deposit derived tables (`protein_datasets`, `search_modifications_placed`, the `dataset_overview` row) computed once per bundle and stored beside it; the publish aggregates `protein_index` and `peptide_index` from them | 2-3 days |
| 2c | the batch runs `logs.resolve_genes` and `go.annotate_groups` after each ingest (PXReprise's batch; no dataRepo code) | none here |
| | **step 2 total** | **about a week** |

**Acceptance (the contract's section 7), and how we will show each:**
- A publish under 10 minutes, and a catalog under 1 GB: measured on aging's store after each step, and projected
  to 4,350 deposits from the per-deposit cost.
- A build succeeds with readers attached: a test with a DuckDB reader and a running MCP server (1.3.2 already holds
  this class; step 1 removes the replace altogether).
- A stranger with no download, and a second question without a second copy: PXReprise's tests (hosting and the
  corpus manifest).

## 7. Readers of PSMs today (step 2a's list)

- **Catalog:** the `psms_1pct` view; `dataset_overview.n_psms_1pct` and `n_psms_all`; the four PSM indexes;
  `CheckRowCounts`; `CheckIntegrity`'s `psm_id` uniqueness and `psms.run_id` / `protein_accessions[]` references;
  the `catalog_tables` counts; the `DerivedDocs` prose.
- **MCP:** the sql tool's description names `psms_1pct`; `describe` reports `n_psms_1pct`; `DescribeTable`'s
  `see_also` for psms; `RunRelativeColumns` (`pep`); `search` by dataset reads `n_psms_1pct`; `mcp --check` prints it.
- **Site:** `n_psms_1pct` and `n_psms_all` on the front page and dataset pages; Croissant opens `psms.parquet` for
  its schema.
- **Sources that need no PSM rows:** the `metrics` row `psms_1pct` (results.txt), the reconciliation's
  `psms_target_1pct` in `bundle.json`, and the table counts in `bundle.json`.

## 8. DuckLake evaluation, evidence (2026-10-11)

The setup:
- DuckDB 1.5.5 in Python; `INSTALL ducklake` took the `core` build `d8a1881e`, and the metadata records version 1.0.
- Three bundles were copied to scratch (schema 0.0.15, 2-3 MB each). Nothing was written under `F:\`.
- The scripts are `results/public_data_2026-10-11/ducklake/`.

1. **Registration without copying** (`ducklake_add_data_files`):
   - `protein_groups`, `quant_values` and `psms` of two bundles registered. Row counts matched (604, 28,939, 42,898),
     and a full-content difference on protein groups was 0 rows.
   - The sha256 and modification time of all 48 store files were unchanged.
   - Files need not sit under DATA_PATH. Every path is stored **absolute**, even inside DATA_PATH, and a relative
     argument is stored as given and resolves against the working directory.
2. **Ownership** (the docs: "The ownership of the Parquet file is transferred to DuckLake"). Reproduced twice,
   independently (`t6_maint.py default1`):
   - **One default `CHECKPOINT`** wrote merged `ducklake-*.parquet` files and scheduled all four registered bundle
     files for deletion. One of the four was outside DATA_PATH. `auto_compact` defaults to true.
   - `cleanup_old_files`, or a later `CHECKPOINT` once `delete_older_than` passes, then deletes them.
   - `delete_orphaned_files` deletes every untracked Parquet file under DATA_PATH: a bundle's 14 other tables.
     `bundle.json` and `sources/` survive.
   - `auto_compact = false` stops the merge, not the orphan deletion.
   - Never call: CHECKPOINT, merge, rewrite, cleanup, orphan deletion, flush. Never DELETE or UPDATE.
3. **Snapshots:**
   - Each committed registration is one snapshot, and `ducklake_set_commit_message` stores an author and a message.
   - `AT (VERSION => n)` and `ATTACH ... (SNAPSHOT_VERSION n)` returned exactly that snapshot's rows.
   - Snapshots are kept until expired. Rows carry `snapshot_id` and `filename`, but no `bundle_id`.
4. **Static hosting**, over a local HTTP server with Range support:
   - Read-only attach worked with `DATA_PATH` and `OVERRIDE_DATA_PATH true`: tables and time travel were
     row-identical to local Parquet, read by range GETs. But only after `ducklake_data_file` was rewritten by hand
     to relative paths.
   - Files registered by absolute `http://` URL could not be opened on Windows (the URL was mangled to backslashes).
   - `count(*)` still answered on that broken catalog, from metadata, without opening a file.
   - An attach took 17-42 GETs. `hf://` and Linux were not tested.
5. **Schema evolution:**
   - A file with an extra or a missing column is refused by default.
   - `ALTER TABLE ... ADD COLUMN` then accepts new files, and old files read NULL.
   - `allow_missing` with `ignore_extra_columns` accepted a protein_groups file into `psms` without complaint.
     Never use them.
6. **C#:** DuckDB.NET 1.5.5 carries the same native engine and extension cache, so we expect the same behaviour; it
   was not built. Our MCP sandbox would refuse `LOAD` and the data reads, as it refuses views (section 1).
