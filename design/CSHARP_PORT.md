# Porting dataRepo to C# (D41)

**Status (2026-10-04, end of the first port day): every module is ported and verified against Python 0.32.0 on real data. Nothing is released; the operator stays on Python 0.32.0.**

| phase | state | measured against Python 0.32.0 |
|---|---|---|
| 1 schema and bundle | **done** | all 88 current-schema bundles in aging's store round-trip: 95,328,025 rows, 0 differences, every id recomputes |
| 2 ingest | **done** (parity mode `IngestRules.Python0320`) | test dataset: 17/17 tables identical; corpus: **85 of 85** datasets identical, every table and row (2026-10-04) |
| 2 G76 / G81 / D37 | **built** under `IngestRules.Current` | G76 reproduces aging 075's fibronectin case; 46 of 937 within-gene merges rest on an Ensembl id alone (DATAREPO-70) |
| 3 study layer | **done** (`DataRepo.Study`) | ids identical to Python's; aging's stored study bundle reproduced |
| 3 catalog | **done** (`DataRepo.Catalog`) | 27M rows identical (13 aging datasets with study layer and 8 engine artefacts; 20-dataset reference); one view lists in undefined order in Python's own SQL |
| 4 MCP server | **done** (`DataRepo.Mcp`, `datarepo mcp`) | 367 + 367 fixture calls and 427 calls on aging's serving catalog byte-identical to Python's server; tools/list identical over real stdio; timeout watchdog verified on DuckDB 1.5.5. Not yet done: the stranger-agent check (a subagent with only the tools) |
| 5 site | **done** (`DataRepo.Site`) | byte-identical: 1,321 files / 41 MB from aging's 85-dataset serving catalog |
| 5 runner + logs engine | **done** (`DataRepo.Runner`) | aging's stored rat resolution re-run with its inputs: every row identical |
| 5 CLI | **done** (`DataRepo.Cli`, `datarepo.exe`): every command of the Python release | CI runs ingest/build/query/site end to end on Linux |
| 5 binaries | **built and verified** in CI (`dotnet-binaries.yml`): win-x64, linux-x64, osx-arm64, osx-x64, each running the fixture end to end with no .NET | artifacts only, no release |
| 5 release, operator switch | not started: the user decides the release; aging re-runs its benchmark on both catalogs first (084) | |

Decided by the user on 2026-10-04: "any code of substance must
be in C# and in our production code. python is only acceptable for quick work." Asked whether that covers
dataRepo's own package, they chose the port. This supersedes D36, which made the executables from the
Python code.

## Why this is more than a language change

The port removes three problems the Python version could only work around:

1. **No bridge between us and mzLib.** dataRepo reads producer files through pyMzLib, which runs mzLib in a
   subprocess and sends results back as one JSON string. That string is capped at about 1.07 billion
   characters, so PXD032044's 1.83 GB `AllPSMs.psmtsv` cannot be read whole (our 008; pyMzLib's DATAREPO-M3).
   We read it in windows instead, and each window parses the whole file again (about 494 s instead of 50 s).
   In C# the reader is a library call, so the limit and the windowing both go away.
2. **The readers we wrote ourselves can go** (G14). In 0.4.0 pyMzLib reads `AllQuantifiedPeaks.tsv`,
   `AllQuantifiedPeptides.tsv`, `AllQuantifiedProteinGroups.tsv` and the protein database, and `pro_forma` is
   filled (2,462 of 2,502 PSMs on PXD036557, checked 2026-10-04). In C# we call mzLib's own types directly.
   `proforma.py`, the reader table in `readers.py`, and `protein_db.py` become mzLib calls.
3. **PXReprise can call it in-process.** PXReprise is net10.0 on mzLib 1.0.593, and its rules (D8) allow
   .NET, git and MetaMorpheus only. A C# dataRepo is a library it can reference directly. A `dotnet publish`
   self-contained build meets PXR-D1 without the PyInstaller packaging and its executable-bit problems.

## What must NOT move

These are contracts other projects and stored data rely on. The port reproduces them; it does not
redesign them.

| contract | where it is today | rule for the port |
|---|---|---|
| the schema | `schema/datarepo.yaml` (LinkML, core 0.0.13) | still the source of truth. C# types and Arrow schemas are **generated** from it, as `tools/build_tables.py` generates `_tables.py` today |
| the bundle | Parquet per table plus `bundle.json` | same layout, same column types, same `bundle.json` keys |
| the content hash | `manifest.CONTENT_FIELDS` / `NON_CONTENT_FIELDS`, `INGESTER_VERSION`, schema version | the same rules. The C# ingester starts a new `INGESTER_VERSION` line, so bundle ids change **once**, on purpose (see "Parity") |
| the catalog | DuckDB file, views, `catalog_id`, `CATALOG_VERSION` | same views and the same SQL a caller can run |
| the MCP tools | `describe`, `search`, `sql`; D12, D14, D19, D20 | the same tool contract; **certification comes from the engine, never from the query** (D20) |
| the site | `datarepo site` output, `.datarepo-site.json` marker | the same files; the marker's `generator` names the C# version |
| definitions | `definitions.py`: owners' text, copied word for word | same texts. D37's ten `pxreprise:` texts are already transcribed on `wip/d37-g81-python` |

## Shape

One .NET solution in this repository, `dotnet/`, beside `src/` until the Python is retired.

| project | replaces | depends on |
|---|---|---|
| `DataRepo.Schema` | `_tables.py`, `_schema_docs.py` (generated) | the LinkML YAML |
| `DataRepo.Bundle` | `bundle.py`, `integrity.py`, `_tables.py`, `errors.py` (phase 1); `manifest.py`, `definitions.py` (phase 2) | Schema; writes Parquet through **ParquetSharp + Apache.Arrow**, the same Arrow C++ writer pyarrow uses, so column types and required/optional flags match a Python bundle exactly. (Changed from DuckDB `COPY` on 2026-10-04: DuckDB writes every column optional.) |
| `DataRepo.Ingest` | `ingest.py`, `sources/*`, `readers.py`, `proforma.py`, `modlist.py`, `usi.py`, `reconcile.py`, `integrity.py` | Bundle; **mzLib NuGet** |
| `DataRepo.Study` | `study.py` (phase 3, done 2026-10-04: same study bundle ids, rows and `study.json` as Python 0.32.0) | Bundle; Ingest (`PyYaml`, `Sdrf.NotAvailable`). Its own project so the writer did not wait on the catalog's DuckDB work. |
| `DataRepo.Catalog` | `catalog.py` | Bundle; Study; `DuckDB.NET.Data.Full` |
| `DataRepo.Mcp` | `mcp.py`, `sandbox.py` | Catalog; the official `ModelContextProtocol` C# SDK |
| `DataRepo.Site` | `site.py` | Catalog |
| `DataRepo.Runner` | `runner.py`, `engines/logs.py` | Bundle |
| `DataRepo.Cli` | `cli.py` | all of the above; `System.CommandLine` |
| `DataRepo.Tests` | `tests/` (6,500 lines) | NUnit, as mzLib uses |

Size: about 15,000 lines of Python. The largest modules are `catalog.py` (1,918 lines), `mcp.py`
(1,616), `site.py` (1,499) and `ingest.py` (1,205).

## Order

Each phase ends on a parity check against real data. The operator stays on Python 0.32.0 until phase 2 passes.

1. **Schema and bundle.** Generate the C# types from the LinkML schema, write a bundle, and compute the
   content hash.
   **Done when:** every table of a stored 0.32.0 bundle round-trips, read and rewritten, with identical
   rows.
2. **Ingest, plus the release that was due.** Port each source onto mzLib's types: identifications, quant,
   occupancy, the protein database, SDRF, provenance, runs and go. Build the three pending items here, in C#:
   - **D37:** the `definitions` namespace in each stage's provenance, plus the ten `pxreprise:` texts;
   - **G76:** `PeptideUniquenessClassifier` mapped by D40;
   - **G81:** pep 005's `iterative` rule.

   **Done when:** the parity run below passes on aging's store.
3. **Catalog and study layer.**
   **Done when:** a catalog built by C# from the same bundles answers the benchmark SQL identically.
4. **MCP server.**
   **Done when:** a subagent with only the tools, and no source, answers the same questions (`scratchpad/ask.py`
   rewritten against the C# server).
   **Built 2026-10-04** (`DataRepo.Mcp`, `datarepo mcp` in `DataRepo.Cli`): every answer to a 367-call corpus is
   byte for byte the Python 0.32.0 server's on the two fixture catalogs (CI), and 427 calls on aging's serving
   catalog (RealData); see `dotnet/tests/DataRepo.Tests/Fixtures/mcp/PROVENANCE.md`. The subagent check above is
   still to do.
5. **Site, runner, CLI, binaries, release.** The operator switches once. The Python package is then
   deleted, and the docs say so.

## Parity: how "the same" is measured

We test by consuming the output, not by validating it (this repo's first rule). For every dataset in
aging's store, run both:

- **Python 0.32.0** with the parked D37/G81 changes applied, so both sides implement the same rules;
- **C#.**

Then compare every table **row by row**: order-insensitive, typed, with floats compared exactly where the
producer printed them. Bundle ids will differ, because the ingester line is new. That is the one deliberate
re-identification, and the operator re-ingests once, at phase 5. Every row difference is either a C# bug
or a Python bug, and each gets a named finding before the switch. The Python bug is not carried forward.

## What happens meanwhile

- **Python is frozen at 0.32.0.** Only fixes for defects that hit the operator go in, each the smallest
  possible.
- **D37, G76 and G81 ship in C#, not Python.** PXReprise was told not to wait for the definitions release
  (our 007), so nobody is blocked. They are told the plan and its new timing.
- **pyMzLib stops being a dependency** once ingest is ported. Their DATAREPO-M1 answer says so. Our needs
  move to mzLib itself, through `/oracle mzLib`.

## The switch: what is left, and whose step each is

Every module is ported and verified. What remains moves the operator (aging, through PXReprise's batch) from
Python 0.32.0 to the C# release. **Nothing here has been done; each step marked "user" waits for the user.**

1. **Corpus ingest parity: DONE 2026-10-04.** All **85 of 85** `include` datasets in aging's live manifest,
   ingested by Python 0.32.0 (pyMzLib 0.4.0) and by the C# ingester (`IngestRules.Python0320`): every table, every
   row identical. 84 matched on the first pass. PXD077298 differed only because aging edited its manifest entry
   (PXR-A17, `run_enrichment` for a mixed deposit) between the two ingests; both sides re-ingested from one
   snapshot of the manifest are identical. Rerun this step at the switch if the C# code changes before then.
2. **Decide the first C# version number** (user). Recommendation: **1.0.0**. It is a new implementation line,
   and bundle ids change for every dataset anyway (the ingest path is new), so a major version says so
   honestly. 0.33.0 would suggest a compatible step.
3. **Changes that only make sense at the release** (dataRepo, in the release commit):
   - `BundleWriter.IngesterVersion` from `cs-0.0.0-dev` to the release's ingest path (e.g. `cs-1.0.0`);
   - the schema's `peptidoforms.is_unique` / `is_isoform_specific` descriptions rewritten for G76 (D40: one gene
     / one sequence, I = L, contaminants count, from mzLib's classifier), and the site tile's definition
     (aging 084), plus `pep:DEF-PEP`'s version key gaining `iterative` (G81);
   - `OccupancyState` gains `covered_zero` (QuantProject 009, DEF-OCC-COVERED-ZERO; the C# already writes it under
     `IngestRules.Current`), its description and `ptm_stoichiometry.occupancy_state`'s / `intensity_is_floor`'s
     descriptions updated, and the schema version bumped (0.0.13 -> 0.0.14). The release re-ingests everything
     anyway, so this costs the operator nothing extra;
   - retire the Python CI jobs' `--check` against the schema (the Python is frozen and its generated files would
     go stale on the first schema edit), keeping the Python package in the repo until the switch is done;
   - README and docs: the C# `datarepo` replaces `pip install`; the tutorial ids rerun (CLAUDE.md: a catalog id
     hashes the package version, so every release makes printed ids stale).
4. **Publish the release** (user: tag push and `gh release edit --draft=false`, as for 0.31/0.32). A release
   workflow attaches the four `dotnet-binaries` builds to the draft; today that workflow uploads artifacts only.
5. **aging's benchmark on both catalogs** (aging 084): build a C# catalog from the same bundles they serve, run
   `results/eval/` on both, and send every differing answer. Our side: the MCP calls already match on 427 real
   calls, so a difference would be news.
6. **The operator switches** (aging/PXReprise), in the order PXReprise agreed (DATAREPO-71, their 011):
   1. PXReprise drains its batch with STOP. This can take hours, because it waits for the search under way.
   2. aging installs the release at a FIXED path (PXReprise pins a path, never a build folder) and re-ingests the
      store once. Every bundle id changes, by design; about 2 h 20 min for 85 datasets here.
   3. Repoint both callers:
      - PXReprise's `machine.toml` `{datarepo}`, through a new pin; its first `batch.log` lines show it;
      - **aging's own `$DataRepo` in `publish_catalog_and_site.ps1`**, which does not read PXReprise's pin.
   4. aging rebuilds the catalog and the site, and repoints `.claude.json` at
      `datarepo.exe mcp --catalog <catalog.duckdb>` (aging 084 asked for exactly this line).
   5. PXReprise resumes; from v0.3.7 it writes `"definitions": "pxreprise"` in provenance (D37).
7. **Retire the Python** (dataRepo): delete `src/datarepo`, the Python CI jobs and the PyInstaller workflow once
   the operator has run on the C# release for a while. The parity tool keeps `IngestRules.Python0320` so the old
   rows stay reproducible without the Python.

The half-written `manifest.yaml` seen on 2026-10-04 was PXReprise's in-place rewrite. It is fixed in their
source (write beside, then rename; their 011) and ships in their next release.

## Requirements peers have handed the port (carry them to the phase named)

- **aging 084** (answers DATAREPO-68): no Python imports of datarepo anywhere; they run `ingest`, `build`,
  `study`, `site`, `manifest` and the MCP server (`python -m datarepo.cli mcp` today). **Phase 4/5:** keep a
  way to start the MCP server they can point `.claude.json` at (an exe is fine) and tell them the new
  command line at the switch. **The command line (phase 4):** `datarepo.exe mcp --catalog <catalog.duckdb>`,
  registered by `datarepo mcp --catalog <path> --install` as
  `{"command": "<path>\\datarepo.exe", "args": ["mcp", "--catalog", "<absolute catalog path>"], "env": {}}`
  (under the shared .NET host: `"command": "dotnet"`, `"args": ["<path>\\datarepo.dll", "mcp", ...]`). Same
  options as the Python (`--list`, `--check`, `--name`, `--config`, `--force`). **Phase 5 (site):** the "Unique peptides" tile's definition must say I and L
  are equivalent and contaminants count (G76). They re-run their `results/eval/` benchmark on both catalogs
  from the same bundles before switching, and send every differing answer.
- **go 020** (D39): once go's D39 is in an mzLib release, a shuffled partner (`Random_<acc>_f<n>`) in
  `accession_used` can only be a go bug, so the 018 section 1.3 check becomes a regression test and the entrapment
  refusal is dropped for files whose `#!mzlib_release` is that release or later. Recommendation: leave
  entrapment groups out of both the hit list and the background of any enrichment input.
- **pyMzLib 019 / DATAREPO-70**: 46 of 937 `SharedWithinGene` peptides on PXD028975 rest on an Ensembl id
  alone (paralogs). Ship with mzLib's rule unless they change it; name the 4.9% in the release notes.

## Open questions (also in OPEN_QUESTIONS.md, each with the default work proceeds on)

- **U16 (answered 2026-10-04: same repo, `dotnet/`):** where the C# lives. Default: `dotnet/` in this repository, so history and the schema stay
  together. Alternative: a new `smith-chem-wisc/DataRepo.NET` repository.
- **U17 (answered 2026-10-04: yes):** whether the docs generator (LinkML's Python tooling) counts as "quick work". Default: yes,
  for now. It is build-time only, emits Markdown, and never runs on data. Replace it if you say otherwise.
- **U18 (answered 2026-10-04: yes):** whether Python 0.32.0 gets operator-blocking fixes during the port. Default: yes, minimal ones,
  each also written into the C# port.
