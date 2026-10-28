# AI contributions: results saved back into the catalog, carried into every release

Branch `feat/ai-contributions`, started 2026-10-28 by PXReprise (pxreprise-31) at the user's request: "you better
start building it or I am a liar". PXReprise owns the pipeline's architecture (PXReprise D41); dataRepo owns this
code, so this is a proposal on a branch until dataRepo's session and the user accept it.

## Why

The SCP renewal (Task 3.3, `E:\Proposals\2026_NIH_Payen_SCP_renewal\Task3.3_draft_2026-10-26.docx`, paragraph 3)
promises:

> When an AI model produces a new result [...] that result will be saved back into the catalog. A record of which model
> made it, how, and from which data will be saved with it. The next researcher, or the next AI model, can then look up
> and build on that result instead of redoing the work. Each release of the catalog will be frozen once published, so
> any result can be cited and reproduced exactly.

On 2026-10-28 none of that existed: the MCP server is read-only, and nothing records a model. The user's question was
whether such results are preserved across new releases. This design makes the answer yes, and makes a release build
REFUSE to drop one.

Four expert reviews, run in parallel, are kept verbatim in `design/ai_contributions/experts/`: provenance
(`design-provenance.md`), MCP interface (`design-mcp.md`), scientific integrity (`design-integrity.md`) and the
test-driven plan (`tdd-plan.md`). This file is the merged design; where they disagree, it says which choice was taken
and why.

## What the code forced (all four agreed)

1. **Not a core LinkML table.** A new core table means a new `SchemaContract.Version`, and `BuildCatalog` refuses every
   stored bundle of the old version (`Catalog.cs:1387-1391`): a full re-ingest, which is the 1.4.0 release the user
   holds (dataRepo D49). Contribution tables are built by the catalog build itself, like `catalog_engine_artefacts`.
2. **Not the engine-artefact selection.** `SelectArtefacts` drops an artefact whose input bundle was re-searched
   (`Catalog.cs:1066-1069`), skips one of another schema version (`:1070-1074`), and fails on two artefacts for one
   input (`:1080-1087`). Each of those would silently lose an AI result at the next release. Contributions get their
   own selection: **every contribution in the store, always**.
3. **Not the artefact id.** `EngineRunner.ArtefactId` hashes the runner and schema versions (`EngineRunner.cs:69`), so
   the id would move at a schema bump. A contribution's id hashes only what its submitter stated.
4. **Reused:** the atomic write into a staging directory then a rename, and the "already exists" refusal
   (`EngineRunner.cs:86-130`); the census rule for the catalog id ("no line without one", `Catalog.cs:1015-1019`), so
   every existing catalog id stays put until the first contribution exists.

## Decisions taken on the branch (provisional; each is listed for the user and dataRepo)

| # | Decision | Why |
|---|---|---|
| A1 | Stored at `<store>/_contributions/<id16>/contribution.json`, beside the bundles, never inside one, outside `_engine/`. | `Runner.DiscoverArtefacts` and `SelectArtefacts` never see it, so none of finding 2's rules can touch it. |
| A2 | The id is the sha256 of the canonical JSON of the validated submission (keys sorted, basis bundles sorted). The folder is the first 16 hex; the full 64 hex is stored and compared, and a prefix collision is refused. | Outsiders supply this content, so 64 bits is too short to trust (provenance review). The time and the datarepo install are recorded, never hashed. |
| A3 | The same submission twice returns the existing id ("already saved"); nothing is rewritten. | Idempotent, as the runner is. |
| A4 | A save names its basis: a `catalog_id` and the exact `(dataset_id, bundle_id)` pairs it used. Both are checked against that catalog's own file (`catalog-<id>.duckdb` in the catalog folder) before anything is written. An unknown catalog or a bundle that catalog does not hold is refused. | "From which data" must be verified, never stated (integrity review C3). |
| A5 | Model identity is required and labelled: `{provider, id, stated_by}`; `stated_by` is `client` or `operator`. The server never invents it. | MCP's `clientInfo` names the client app, not the model (MCP review, protocol citations there). |
| A6 | A named accountable human (`submitted_by.name`, ORCID optional) is required. | ICMJE/COPE: AI cannot be accountable (integrity review section 5). |
| A7 | Prompts and transcripts are NOT stored, only the executed SQL and the stated method. | Personal data (integrity review section 5). |
| A8 | Licence: `CC-BY-4.0` (default) or `CC0-1.0`. | Matches the catalog's D3. |
| A9 | Every catalog build loads every contribution in the store. Tables exist only when there is at least one (census rule), so no `CatalogVersion` bump and no catalog id moves until then. | The user's question: carried forward, always. |
| A10 | `catalog_id` gains one line, `contributions/<set id>`, when there are any. `release_id` does not change: it names the measured data. | A catalog that serves different contributions answers differently (`Catalog.cs:992-999`'s rule); "computed on the same data" stays an equality test on `release_id` (provenance review section 4). |
| A11 | A re-searched deposit never removes or re-points a contribution. `contribution_basis` shows `in_this_catalog = false` and the bundle the catalog now serves. | Nothing is dropped (provenance review section 3). |
| A12 | Retraction and supersession are new contributions (`kind = retraction`, `target`; `supersedes`). Nothing is deleted. The build derives `status`: `active`, `superseded`, or `retracted`. A view `contributions_current` shows the active ones. | Rule 1 of the public-data plan: add-only. |
| A13 | **The guarantee:** a `--release` build records the contribution ids it carries in `catalog_meta.notes.contributions`. Every later build in that catalog folder refuses if any contribution an earlier release carried is missing from the store. | This turns "preserved across releases" from a habit into a check. |
| A14 | `--keep` never prunes a catalog file a contribution names as its basis. | Today only `--release` files are spared (`Catalog.cs:1668-1682`); a pruned basis would make reproduction impossible. |
| A15 | Writing goes through `datarepo contribute` (the operator's verb). The MCP server gains a save tool ONLY under an opt-in flag, and it writes to an inbox the operator accepts (MCP review section 1). The read-only server's tool list stays byte-identical. | dataRepo D19 (no fourth read tool without evidence), and the sandbox lockdown (`Sandbox.cs:111-149`) is never loosened. |
| A16 | Each recorded query is labelled `observed` (seen by the server in this session, with its result hash) or `stated`. A CLI save has only stated queries. | Never promote stated to observed (integrity review section 2; dataRepo learned this with `tables_touched`). |
| A18 | **The server keeps every session itself (the user, 2026-10-28: "the server side should independently choose to keep any interaction and the users be given the option to have previous interactions be exposed to them").** Every MCP tool call (its SQL or search, the catalog it ran on, the time, a hash of the answer) is written by the server, not by the agent's choice, to an add-only, hash-chained session log in the store, carried into every release like a contribution. It holds no prompt and no model prose: the server never sees them. **Public by default (the user, 2026-10-28: "this is a public repo. no question is private")**: the server says so to every client at connection (MCP `instructions`), and records no person unless one chooses to give a name or ORCID. Users opt in to be shown earlier sessions on the same tables or deposits. A contribution cites log entries, which is what makes a query `observed`. | The record of "how" no longer depends on the AI choosing to save. Public data, public questions; the notice at connection means nobody is recorded without being told. |
| A17 | Reproducibility class per contribution: `query` (re-runs exactly), `code` (released code + pinned inputs), `stochastic` (seeds; within a tolerance), `judgement` (a model's verdict: frozen, not re-runnable). Only the first two may be called reproduced. | Integrity review section 2. |

## Slices and their status

The full test list for each slice is `design/ai_contributions/experts/tdd-plan.md`; decisions above override its
DECISION points.

| Slice | What | Status |
|---|---|---|
| S1 | Submission validation (required fields named, unknown fields refused, kinds, hex ids, licence, CRLF = LF) | done 2026-10-28 (`ContributionSubmissionTests`) |
| S2 | Id: canonical, order-insensitive, every stated field moves it, time and install never do | done (same class) |
| S3 | Save: beside the bundles, atomic, already-saved, basis verified against the catalog file | done (`ContributionStoreTests`) |
| S4 | Catalog build: tables, catalog id line only when there are contributions, release id unchanged | done |
| S5 | Carry-forward across releases: re-searched deposit, release guard (A13), prune protection (A14) | done |
| S6 | Retraction and supersession, `contributions_current` | done |
| S7 | Session log kept by the server itself (A18): add-only, hash-chained, private by default, opt-in to see shared sessions; observed vs stated | next (redesigned by A18) |
| S8 | MCP save tool under an opt-in flag, inbox, `contribute accept` | next |
| S9 | Discovery through `describe`/`search`/`sql` | next |
| S10 | CLI `datarepo contribute save|list|show|retract|verify` | `save` and `list` done (a retraction is saved as a contribution); `show`, `verify` later |
| S11 | `contribute verify`: re-run recorded queries on the frozen basis catalog | after S7 |

## Open for the user

1. Grant wording: the integrity review proposes four factual corrections to paragraph 3 (its section 4), e.g.
   "reproduced exactly" holds for query and code results, not for a model's judgement. The PIs write the prose.
2. Who may submit, and whether a public write endpoint is ever wanted (PLAN rules 7-8 forbid servers today).
3. Whether contributions on a working build (not a release) are accepted (today: yes, and A14 keeps their basis file).
4. Who reviews a contribution before the next model is told to build on it (status `unreviewed` -> `reviewed`).
