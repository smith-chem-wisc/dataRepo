# TDD plan: AI contributions saved back into the dataRepo catalog

Written 2026-10-28 from a read of `E:\CodeReview\dataRepo\dotnet` (no code was run or changed). All paths below are
relative to `E:\CodeReview\dataRepo\dotnet\` unless they say otherwise.

## 0. Three findings that shape the plan (read first)

1. **The contribution tables must NOT go into the core LinkML schema.** `ArrowTables.FromRows(name, rows)`
   (`src/DataRepo.Bundle/ArrowTables.cs:62`) only knows core tables, and `EngineRunner.WriteArtefact` calls it
   (`src/DataRepo.Runner/EngineRunner.cs:100`). Adding a core table means a new `SchemaContract.Version`
   (`schema/datarepo.yaml` is 0.0.15), and `BuildCatalog` then refuses every stored bundle written against the old
   version (`src/DataRepo.Catalog/Catalog.cs:1387-1391`): a full re-ingest of the store, i.e. the 1.4.0 release, which
   the user has put ON HOLD (dataRepo D49). Plan: contribution tables are **catalog-built tables** (like
   `catalog_engine_artefacts` and the `DerivedTables`), with their column specs held in C# and written through
   `ArrowTables.FromRows(label, columns, rows)` (`ArrowTables.cs:31`). This is a design choice the other experts must
   confirm.
2. **The engine-artefact gate would drop contributions at the next schema bump.** `SelectArtefacts` skips artefacts of
   another schema version (`Catalog.cs:1070-1074`), `BuildCatalog` refuses them (`Catalog.cs:1418-1423`), and
   `EngineRunner.ArtefactId` hashes `RunnerVersion` and `SchemaContract.Version` (`EngineRunner.cs:69`). Contributions
   must survive EVERY later release, so they need their own id rule (no schema or runner version in it) and their own
   selection (no schema gate). Reuse the directory layout, the atomic staging-then-rename write and the
   already-exists refusal (`EngineRunner.cs:86-130`). Do not reuse the id or the selection.
3. **Catalog id and tutorial.** `CatalogIdOf` hashes everything served (`Catalog.cs:967-1021`), and
   `DocsTests.TheTutorialPrintsWhatTheProgramPrints` pins the tutorial's catalog id and the `mcp --check` tools line
   (`tests/DataRepo.Tests/DocsTests.cs:127-135, 151-154`). Follow the census precedent: **no line without one**
   (`Catalog.cs:1015-1019`). An empty contribution set then keeps every existing catalog id. Adding new (empty) tables
   to every catalog would by house rule bump `CatalogVersion` 13 -> 14 (`Catalog.cs:217-246`). That moves every
   catalog id and forces the tutorial to be re-run, and `FolderCatalogTests`/`GoEngineTests` assert "13". DECISION
   NEEDED: bump to 14 (and ship with the next release the user approves), or create the tables only when a
   contribution exists (census style, `Catalog.cs:1503`). The plan assumes the bump and lists the tests it touches
   (S4).

## 1. Conventions the new tests must follow

- **Framework:** NUnit 4.3.2, global `using NUnit.Framework` (`tests/DataRepo.Tests/DataRepo.Tests.csproj`),
  file-scoped `namespace DataRepo.Tests;`, one class per feature file, `<summary>` + `<remarks>` on the class citing
  the decision/thread ids (`GoEngineTests.cs:11-21`).
- **Test names** are behavioural sentences in PascalCase, often stating a refusal: `TheSameInputsAreAlreadyDone`
  (`GoEngineTests.cs:171`), `WithoutADefinitionIdNothingRuns` (:184), `TwoArtefactsForOneBundleAreRefusedNotPicked`
  (:278), `AReplacedCatalogFileIsAnnouncedNotSilentlyServed` (`McpTests.cs:306`).
- **Assertions:** the constraint model with a reason string: `Assert.That(x, Is.EqualTo(y), "why")`, and for
  refusals `Throws.TypeOf<RunnerException>().With.Message.Contains(...).And.Message.Contains(...)`
  (`GoEngineTests.cs:186-187`). Each refusal also asserts that nothing was written
  (`Directory.Exists(... EngineDir)` is false, `GoEngineTests.cs:189`). Use `Assert.Multiple` for groups of facts
  (`FolderCatalogTests.cs:109-118`). Use `Assume.That` for environment-conditional tests (`RunnerTests.cs:31`).
- **Scratch store:** `[SetUp]` makes `Path.GetTempPath()/"datarepo-<what>-"+Guid:N`, and `[TearDown]` deletes it
  (`GoEngineTests.cs:63-70`; `FolderCatalogTests.cs:26-45`). `RepoRoot()` walks up to `schema/datarepo.yaml`
  (`FolderCatalogTests.cs:14-19`). `CopyTree(tests/data -> scratch/data)` then
  `Ingester.Ingest(ManifestPath, "PXD999999", Store, rules: IngestRules.Current)` (`FolderCatalogTests.cs:30-37`).
  `tests/data` is a miniature instance (one included dataset, PXD999999, plus excluded PXD000000; ~400 KB, 23 files).
- **Build helper:** `SelectBundles` -> `SelectStudyBundles` -> `SelectArtefacts` -> `BuildCatalog(...)`
  (`FolderCatalogTests.cs:61-69`). Read rows back with `CatalogBuilder.RunQuery(path, sql).Rows`
  (`GoEngineTests.cs:257-262`).
- **A second bundle of the same dataset** ("re-search"): change a content input and fix its sha256 in
  `provenance.json`, then re-ingest (`GoEngineTests.cs:82-108` does this for the database).
- **Released-build gate:** engine tests pass a `StandInInstall` dictionary (`GoEngineTests.cs:26-29`,
  `RunnerTests.cs:10-13`), because `EngineRunner.InstallIdentity()` refuses `-dev` builds.
- **MCP:** the class is `[NonParallelizable]` (`McpTests.cs:20`). A shared catalog comes from a gunzipped fixture in
  `[OneTimeSetUp]` (`McpTests.cs:34-43`). `Unopened()` copies it, because a DuckDB file opened by one `Sandbox` config
  cannot be reopened with another in the same process (`McpTests.cs:51-58`). The in-process SDK round trip uses
  `System.IO.Pipelines` and `McpServer.Create` / `McpClient.CreateAsync` (`McpTests.cs:328-380`). The CLI is driven
  through `McpCommand.Run(args, StringWriter, StringWriter)` (`McpTests.cs:384-390`).
- **Python parity:** parity classes pin `SchemaContract.Python0320()` in `[SetUp]`/`[TearDown]`
  (`McpParityTests.cs:24-25`, `CatalogTests.cs:17-18`). Anything new must be absent in that scope (gate on
  `!SchemaContract.IsPython0320`, as `AnnotationsActive`/`GoActive` do, `Catalog.cs:259-263`). The tool list is
  compared with `Fixtures/mcp/python_tools.json`, with deliberate deltas applied as text replacements (`SinceStep2`,
  `McpTests.cs:321-326`).
- **Whole CLI in process:** `DataRepo.Cli.Cli.Run(argv)` with `Console.SetOut/SetError` and the invariant culture
  (`DocsTests.cs:45-63`).
- **Categories:** `[Category("RealData")]` for anything that reads `F:` (`McpParityTests.cs:85`). CI runs
  `dotnet test dotnet/DataRepo.slnx` unfiltered (`.github/workflows/ci.yml`, job `dotnet`), and RealData tests
  `Assert.Ignore` when their data is absent. The suite's duration is not documented anywhere (CLAUDE.md,
  CONTRIBUTING.md, design/).
- **Id tests** state the hash rule: order-insensitive, and any hashed field moves it (`RunnerTests.cs:16-26`,
  `CatalogTests.cs:300-325`, which recomputes the sha256 text by hand).
- **Docs gates:** every new derived table needs a `DerivedDocs` entry (`CatalogTests.cs:711-722`). A new verb or flag
  must regenerate `docs/cli.md` (CI `build_cli_docs.py --check`) and be added to `Cli.Commands`/`Summaries`
  (`src/DataRepo.Cli/Program.cs:37-55`).

## 2. Slices (each shippable; failing tests first)

Proposed production homes:
- `src/DataRepo.Catalog/Contributions.cs`: `ContributionRef`, `Contributions.Engine = "contribution"`, `Discover`,
  `ColumnSpecs`, `Select`.
- `src/DataRepo.Runner/ContributionWriter.cs`: `Validate`, `Id`, `Save`, `Retract`, `Supersede`.
- `src/DataRepo.Catalog/CatalogIndex.cs`: catalog id -> file in a catalog folder.
- `src/DataRepo.Mcp/SessionLedger.cs`, `src/DataRepo.Mcp/CatalogServer.Contributions.cs`; edits to `Mcp.cs` and
  `McpCommand.cs`.
- `src/DataRepo.Cli/ContributeCommand.cs`.

### S1 Manifest schema validation (`ContributionManifestTests` -> `ContributionWriter.Validate`)

| Test | Arrange / act / assert |
|---|---|
| `AManifestWithEveryRequiredFieldValidates` | minimal manifest (kind, model{name,version}, author, licence, input{catalog_id, bundles[]}, payload) -> no exception; normalised copy returned |
| `EachMissingRequiredFieldIsNamed` (TestCase per field) | drop one -> `ContributionException` message names the field |
| `AnUnknownFieldIsRefusedNotIgnored` | extra key `confidence` -> refused, names it |
| `AKindOutsideTheListIsRefused` | kind `"vibes"` -> lists allowed kinds (e.g. finding, table, annotation, retraction, supersession) |
| `ACatalogIdOrBundleIdThatIsNotSixteenHexIsRefused` | `"ABC"` -> refused |
| `ALicenceMustBeAnSpdxIdentifier` | `"free"` refused, `"CC-BY-4.0"` ok |
| `AStatedTimeIsNotTrusted` | client sends `written_utc` -> refused or ignored (decide); server stamps its own |
| `APayloadPathOutsideTheGivenFilesIsRefused` | payload names `../x` -> refused (no path traversal into the store) |
| `CrlfAndLfManifestsValidateAlike` | same manifest with CRLF -> same normalised object (house rule: normalise at read) |

### S2 Id hashing and idempotency (`ContributionIdTests` -> `ContributionWriter.Id`)

- `TheIdHashesTheCanonicalManifestNotItsKeyOrder`: two dictionaries in different key order give the same id.
- `EveryHashedFieldMovesTheId` (TestCase per field: model, input catalog_id, a bundle, a query's sql, a query's
  result sha256, payload sha256, kind, author, licence): each change gives a different id.
- `TheServersTimeAndInstallAreRecordedButNotHashed`: two saves 1 s apart, or under different `install`, give the same
  id.
- `TheIdDoesNotHashTheSchemaOrRunnerVersion`: hand-written expected sha256 text (style of `CatalogTests.cs:310-315`)
  with no `schema/` or `runner/` line.
- `BundleOrderDoesNotMatter`.

### S3 Store write: beside, never inside; repeat-run refusal (`ContributionWriterTests` -> `ContributionWriter.Save`)

- `ASaveWritesOneDirectoryUnderEngineContribution`: fixture A -> `Save` -> `<store>/_engine/contribution/<id>/`
  holds `contribution.json` (the record), `payload/...` and `queries.parquet`. `Runner.DiscoverArtefacts` does NOT
  treat it as an engine artefact. Choose its record name so it never collides with `run.json`, or decide that it
  does.
- `TheSameContributionTwiceIsAlreadyDone`: the second `Save` returns `AlreadyDone` with the same id and does not
  rewrite (mtime unchanged). Mirrors `GoEngineTests.cs:171-182`.
- `NoBundleFileChangesWhenAContributionIsSaved`: sha256 every file under `<store>/PXD999999/` before and after: equal.
  `Integrity` still passes on the bundle.
- `AFailedSaveLeavesNothingDiscovery`: inject a payload copy failure; there is no `<id>` dir and no `.<id>.writing`
  left (`EngineRunner.cs:91-128`).
- `AnUnknownCatalogIdIsRefusedBeforeAnythingIsWritten`: cite `0000000000000000` -> refused, names the catalog folder
  searched; `_engine/contribution` absent.
- `ABundleTheCitedCatalogDoesNotHoldIsRefused`: b2 exists in the store but A holds only b1 -> refused ("not in
  catalog A"). Also a bundle id that exists nowhere.
- `ACatalogIdIsResolvedFromTheFolderNotTrusted` (`CatalogIndex`): `catalog-<id>.duckdb` whose `catalog_meta.catalog_id`
  differs from its name -> refused.
- `ADevelopmentBuildMay/MayNotSave`: DECISION. The runner refuses dev builds (`EngineRunner.cs:41-58`); a
  contribution records `install` either way.

### S4 Catalog build includes contributions (`ContributionCatalogTests` -> `Contributions.Select`, `CatalogBuilder.BuildCatalog`)

- `ACatalogLoadsEveryContributionInItsTables`: save C on A, build B -> `contributions` has one row (id,
  input_catalog_id=A, kind, model, author, status 'active'); `contribution_inputs` holds (C, A, PXD999999, b1);
  `contribution_queries` holds the trail. `catalog_tables.kind = 'contribution'`.
- `AContributionIsHashedIntoTheCatalogIdButNotTheReleaseId`: B's id differs from a build without C. `release_id`:
  DECISION (D48 rule 9 says it names the data: bundles, study, engines), so the assertion follows the choice.
- `NoContributionsKeepsTheCatalogIdItHad`: with the census rule, the fixture id equals the one built before the
  feature.
- `AParityBuildHasNoContributionTables`: under `SchemaContract.Python0320()`, no tables and an unchanged id.
- `EveryContributionTableIsDocumented`: extend `EveryDerivedTableAndViewIsDocumented`, or add a sibling.
- `AFolderAndAOneFileCatalogHoldTheSameContributionRows`: add to `FolderCatalogTests.AFolderCatalogHoldsWhatAOneFileCatalogHolds`.
- If CatalogVersion goes to 14: update `FolderCatalogTests.cs:146`, the "13" in `GoEngineTests`, and rerun the
  tutorial (`DocsTests`).

### S5 Carry-forward across releases (the user's key question) (`ContributionCarryForwardTests`)

Fixture: ingest b1 -> build folder catalog A (`notes.release = "r1"`) -> save C(A, b1) -> re-search (new content
gives b2) -> build B (pin b2) -> build release C3 (a third build after another change).
- `AContributionIsCarriedIntoEveryLaterRelease`: C is in B and C3 with an identical row, and its id is unchanged.
- `ACarriedContributionStillNamesTheReleaseItWasComputedFrom`: in C3, `input_catalog_id = A` and the input bundle is
  b1, not B or b2.
- `AContributionWhoseBundleWasReSearchedSaysSo`: in B, `contribution_inputs` shows b1 with `in_this_catalog = false`
  and the current bundle b2 beside it (column names: DECISION). The row is kept, not dropped. This is the inverse of
  `SelectArtefacts`, which drops artefacts whose database is not searched (`Catalog.cs:1066-1069`).
- `AContributionIsCarriedEvenWhenItsDatasetLeavesTheCatalog`: build with PXD999999 excluded or not selected; C is
  still listed. DECISION: or listed with `dataset_absent`.
- `AContributionWrittenUnderAnotherSchemaVersionIsStillCarried`: rewrite the record's `schema_version` to "0.0.14";
  the build includes it (contrast `Catalog.cs:1070`).
- `KeepNeverPrunesACatalogAContributionCites`: three builds with `keep: 1`; A survives. Today only `--release`
  catalogs are spared (`Catalog.cs:1663-1682`). DECISION: else A must be built with `--release`.
- `AReleaseBuildNamesExactlyTheContributionsItCarries`: `--release` + pins; `catalog_meta.notes` lists the
  contribution ids (as `notes.study` does, `CatalogCommands.cs:95-97`).

### S6 Retraction and supersession without deletion (`ContributionLifecycleTests`)

- `RetractingWritesANewRecordAndDeletesNothing`: `Retract(C, reason)` writes R (kind retraction, target C); C's
  directory is byte-identical.
- `ARetractedContributionStaysInTheCatalogMarkedRetracted`: the build shows `status = 'retracted'`, `retracted_by = R`;
  a `contributions_current` view excludes it.
- `SupersedingLinksOldToNew`: S2 supersedes C; C's status is 'superseded', with `superseded_by`.
- `RetractingAnUnknownOrAlreadyRetractedContribution`: unknown -> refused; twice -> AlreadyDone (same R id).
- `ASupersessionCycleIsRefusedAtBuild`: the build fails loudly, naming the ids.
- `TwoRetractionsOfOneContributionAreRefusedNotPicked`: different reasons, different ids. Either refuse at the second
  save or refuse at build (mirrors `GoEngineTests.cs:278-286`).

### S7 Session ledger: observed vs stated (`SessionLedgerTests` -> `SessionLedger`, `CatalogServer.Sql`)

- `EverySqlCallIsLoggedWithTheCatalogItRanOn`: two `Mcp.Call(server,"sql",...)`; the ledger has 2 entries (ordinal,
  sql, catalog_id, row_count, truncated, result_sha256, utc).
- `ARefusedOrFailedQueryIsLoggedAsSuch` (DROP; bad column).
- `TheResultHashDoesNotDependOnTheSessionTimeZone`: the same TIMESTAMPTZ query under
  `Sandbox.TimeZoneOverride = Chicago` and UTC gives the same hash.
- `AnUnorderedResultHashesAsAMultiset`: the same rows in a different order give the same hash. DECISION: or require
  ORDER BY.
- `SaveMarksEachStatedQueryObservedOrStatedOnly`: state 3 queries, 2 run in session -> `queries.parquet.observed` =
  [true, true, false]. Observed queries the agent did not state are appended as `observed_unstated`. Nothing stated
  is dropped.
- `TheLedgerIsPerServerAndForgetsNothingMidSession`: a new `CatalogServer` starts empty.
- `TheClientsSelfReportedIdentityIsKeptApartFromTheModelItStates`: in the SDK round trip (`McpTests.cs:328`), the
  `clientInfo` from `initialize` is recorded as `client_observed`, and the tool argument `model` as `model_stated`.

### S8 MCP save tool, opt-in write mode (`ContributionMcpTests`)

- `ReadOnlyModeListsExactlyTheToolsItDidBefore`: without `--contribute`, the tool list equals `python_tools.json`
  through the existing deltas. `McpTests.ThreeToolsShip...` and `CheckOpensTheCatalog...` stay green.
- `CallingSaveOnAReadOnlyServerIsRefused`: `CallTool(server,"datarepo_save_contribution",...)` -> "Unknown tool" error
  (as `Mcp.cs:190`); nothing written.
- `WriteModeNeedsAStoreAndListsTheSaveTool`: `McpCommand.Run(["--catalog",F,"--contribute"])` without `--store` ->
  exit 2, with a message.
- `SaveThroughTheSdkWritesTheSameContributionAsTheWriter`: pipe round trip; the id equals `ContributionWriter.Id` of
  the same manifest + ledger.
- `WriteModeLeavesTheSandboxReadOnly`: in write mode, `DROP TABLE` is still QueryRefused, and `COPY TO` is still
  refused.
- `SavingAgainstTheServedCatalogDoesNotReopenIt`: the save validates through the server's own `Box`, not a second
  DuckDB open with another config (`McpTests.cs:51-58` lock).
- `ASaveErrorIsAPayloadNotATransportError`: a bad manifest -> `IsError` false, with `{error, message, hint}`
  (`McpTests.cs:363-365`); `ErrorName` maps `ContributionException`.

### S9 List / get / search (`ContributionReadTests` -> `CatalogServer.Contributions`)

- `ListReadsTheServedCatalogsContributions` (frozen).
- `ListInWriteModeAlsoShowsSavedButNotYetBuilt`: rows flagged `in_catalog=false`. DECISION.
- `GetReturnsTheManifestPayloadAndQueryTrail`.
- `SearchFindsContributionsByDatasetAccessionModelAndText`.
- `OnACatalogWithoutContributionTablesTheAnswerSaysNotDeliveredNotNone` (D19 "empty is not negative").
- `ParityFixtureAnswersAreUnchanged`: `McpParityTests` stays green. Any `describe()`/`search()` additions appear only
  when the tables exist.
- DECISION (D12: "a fourth tool only where the benchmark shows a wrong answer"): one `datarepo_contributions` tool, or
  reads through `describe`/`search kind='contribution'`/`sql`. A new search kind changes the input-schema enum, so
  `python_tools.json` needs a `SinceContributions` delta.

### S10 CLI parity (`ContributionCliTests` -> `ContributeCommand`)

- `ContributeSaveListShowRetractPrintOneEnvelopeWithJson`: `Cli.Run(["contribute","save",manifest,"--store",S,"--catalog",F,"--json"])`;
  stdout holds exactly one JSON object (CI pattern in `ci.yml`, "PXReprise 009").
- `TheCliAndTheMcpToolGiveTheSameIdAndRows`: save via CLI and via MCP with the same manifest -> same id, AlreadyDone
  the second time; `list --json` data == MCP structured content.
- `ACliSaveHasNoObservedQueries`: the trail is all `stated_only`; there was no session.
- `ExitCodes`: 0 ok, 1 refused, 2 usage (`McpCommand.cs:51-98`).
- Docs: the `docs/cli.md` regeneration is checked by CI's `build_cli_docs.py --check`; `DocsTests` link test.

### S11 Reproduction (`ContributionReproductionTests` -> `ContributionWriter.Reproduce` / `contribute verify`)

- `RerunningTheRecordedSqlOnTheFrozenCatalogGivesIdenticalRows`: save C on A with 2 observed queries; build B, move
  latest.json; `Reproduce(C)` opens catalog-A, reruns each query, and every result hash matches.
- `ReproductionUsesTheCitedCatalogNotTheLatest`: a query whose answer differs between A and B reproduces on A.
- `AMissingCitedCatalogIsReportedNotSilentlyRerunOnLatest`: delete A -> "catalog A not found".
- `ATruncatedOrUnorderedQueryIsReportedAsNotReproducibleByHash`.
- `ReproductionSurvivesAServerHoldingTheCatalog`: a `CatalogServer` on A stays open.

## 3. Fixtures

- **No new checked-in binaries.** Build from `tests/data` per class in `[OneTimeSetUp]` (ingest b1, then folder build
  A), and per test where the store is mutated.
- **Re-search bundle b2:** reuse `GoEngineTests.IngestWithGo`'s technique (edit `test_human.xml`, rewrite its sha256
  in `provenance.json`, re-ingest). Lift `CopyTree`/`RepoRoot`/`IngestWithGo` into a shared `TestStore` helper:
  today each class copies its own.
- **Folder catalogs are not relocatable:** views name the store by absolute path and `data_root` is hashed into the
  id (`Catalog.cs:981-985`). Never copy a built folder catalog to another scratch dir. Either rebuild it per test or
  share one read-only `[OneTimeSetUp]` fixture for read-only tests. One-file (`.duckdb`) catalogs are relocatable;
  use them for reproduction and copy tests.
- **A contribution fixture** written by the code itself, never by hand (house rule: a reader is not mocked).
- **MCP:** use the built folder catalog. The gunzipped `Fixtures/site/catalog.duckdb.gz` is Python 0.32.0 (schema
  0.0.13) and has no contribution tables: good for "unchanged in read-only" tests.

## 4. Risks

- **Schema bump = full re-ingest** (finding 1); **artefact schema gate drops contributions** (finding 2).
- **CatalogVersion 14** moves every id: the tutorial must be rerun (DocsTests fails until it is), and the "13"
  assertions change. Schedule it with a release the user approves (1.4.0 is on hold, D49).
- **DuckDB locks on Windows:** one database instance per file per process, so a `Sandbox` and `CatalogBuilder.Open`
  with different configs collide (`McpTests.cs:51-58`). Teardown can fail on a still-mapped file (`DocsTests.cs:159-160`
  swallows `IOException`). Dispose servers before deleting the scratch dir.
- **Parity with frozen Python `mcp.py`:** `McpParityTests` and `TheSdkServesTheToolsAsThePythonServerDoes` compare
  tool lists, schemas and answers byte for byte. Anything new must be absent in read-only mode or on catalogs without
  the tables, or be added as an explicit delta.
- **Slow builds:** each folder build of the fixture runs DuckDB plus derivation. Many tests each building 2-3 releases
  could add minutes; the suite time is undocumented. Share fixtures, and never run two `dotnet test` at once.
- **Result hashing:** time zone (`Sandbox.TimeZoneOverride`), float rendering, row order, truncation at 1,000
  rows / 50,000 characters.
- **`--keep` prunes cited catalogs** unless they were built with `--release` (`Catalog.cs:1675-1680`).
- **Model identity** is unverifiable: keep `model_stated` and `client_observed` apart, and never let the id depend on
  the server clock.
