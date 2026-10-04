# Porting dataRepo to C# (D41)

**Status: PHASE 1 BUILT, 2026-10-04** (`dotnet/`: `DataRepo.SchemaGen`, `DataRepo.Bundle`, `DataRepo.Parity`, `DataRepo.Tests`; the fixture bundle Python wrote round-trips identically and its id recomputes). The parity run over aging's whole store is in progress; phase 1 is not called done until it passes. Phase 2 started. Decided by the user on 2026-10-04: "any code of substance must
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
| `DataRepo.Catalog` | `catalog.py`, `study.py` | Bundle; `DuckDB.NET.Data.Full` |
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

## Open questions (also in OPEN_QUESTIONS.md, each with the default work proceeds on)

- **U16 (answered 2026-10-04: same repo, `dotnet/`):** where the C# lives. Default: `dotnet/` in this repository, so history and the schema stay
  together. Alternative: a new `smith-chem-wisc/DataRepo.NET` repository.
- **U17 (answered 2026-10-04: yes):** whether the docs generator (LinkML's Python tooling) counts as "quick work". Default: yes,
  for now. It is build-time only, emits Markdown, and never runs on data. Replace it if you say otherwise.
- **U18 (answered 2026-10-04: yes):** whether Python 0.32.0 gets operator-blocking fixes during the port. Default: yes, minimal ones,
  each also written into the C# port.
