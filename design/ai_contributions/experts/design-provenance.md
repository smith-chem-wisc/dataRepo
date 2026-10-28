# AI contributions: provenance and carry-forward design (dataRepo)

Status: design only, 2026-10-28. No code written. Read against dataRepo master (`E:\CodeReview\dataRepo`) and
PXReprise `design/PLAN_public-data.md`.

The promise (SCP renewal): an AI result is saved back into the catalog with a record of which model made it, how, and
from which data; the next researcher or model can look it up; each release is frozen once published, so any result
can be cited and reproduced exactly. The user's question: are such results preserved across new catalog releases?
This design makes the answer yes, and gives a build check that refuses a release when it is not true.

## 0. Verdict on the prior ("an AI result is an engine artefact")

**Half right.** Reuse the engine-artefact STORAGE. Do not reuse its SELECTION rules or the `datarepo run` WRITE
path.

What is reused as is:
- Layout `<store>/_engine/<engine>/<id>/` with `run.json` and one Parquet per table (`DataRepo.Catalog/Runner.cs:6-16, 53-55`).
- The atomic write: staging dir, then rename, refusing an existing id (`DataRepo.Runner/EngineRunner.cs:86-130`). Verbatim
  extra files via `files` (`EngineRunner.cs:82-84, 103-108`).
- `written_utc` recorded but not hashed (`EngineRunner.cs:109-118`).
- The "already done" test on `run.json` (`GoEngine.cs:217-223`).
- The release-build-only refusal for the datarepo writing it (`EngineRunner.cs:41-59`).
- Discovery (`Runner.cs:79-95`) and the `catalog_engine_artefacts` row (`Catalog.cs:2607-2631`).
- `DataRoot` already requires artefacts to live in the one store the MCP sandbox may read (`Catalog.cs:1620-1644`).

What the code shows is WRONG for contributions, if they were dropped into `SelectArtefacts` unchanged:
1. **Input matching drops them.** An artefact loads only when its input matches a bundle in the catalog: the logs
   artefacts by searched-database sha256 (`Catalog.cs:1066-1069`), go by the bundle's protein-group file
   (`Catalog.cs:1189-1198, 1208-1211`). A contribution computed on PXDn's old bundle would silently disappear from
   release N+1 once PXDn is re-searched. That is the exact failure the user asked about.
2. **A schema bump drops them.** Artefacts of another schema version are skipped (`Catalog.cs:1070-1074`, go `1214`).
   Every contribution would vanish at the next schema change.
3. **Two on one input is refused.** `Catalog.cs:1080-1087` and `1233-1235` fail the build when two artefacts share an
   input. Two models' site lists on the same deposits are normal, not a conflict.
4. **`datarepo run` is the wrong verb.** It runs a released engine INSIDE datarepo on stored data, and the operator
   supplies every input (RUNNER.md "What it will not do"). An AI result is computed elsewhere and DELIVERED. That is
   `datarepo study`'s shape: a delivery manifest checked on the way in, with every manifest field classified as
   content or not (`DataRepo.Study/StudyWriter.cs:146-149`, docs/study.md "Content addressing").
5. **Study bundles are wrong too.** A catalog loads ONE delivery per layer (`--study aging=<id>`), and a new one
   replaces the old (a re-fit). Contributions accumulate.

So: engine name `ai.contribution` under `_engine/`; a new verb `datarepo contribute <contribution.yaml>` (study-style
validation, runner-style storage); a new `SelectContributions` in the build that loads ALL of them, always.

## 1. The stored unit

```
<store>/_engine/ai.contribution/<id16>/
    run.json                   the record (section 1.2); written by EngineRunner.WriteArtefact
    contribution_items.parquet lists: sites, proteins, genes, cell types... (long form)
    contribution_edges.parquet maps/graphs: cell-cell, protein-protein, site-process
    contribution_queries.parquet  one row per query receipt the result was computed from
    files/<name>               the client's own result files and code, byte for byte
    ro-crate-metadata.json     generated from run.json (section 6); not hashed
<store>/_engine/ai.contribution_status/<id16>/run.json   supersession / retraction records (section 3.4)
```

### 1.1 Tables (schema-declared; `ArrowTables.FromRows(name, rows)` needs a schema table, `ArrowTables.cs:62`)

Put them in their own versioned layer (`contrib/1`), like the study layers' `Tables.StudyVersions`
(`Catalog.cs:988-989`), so a core schema bump never touches them.

- `contribution_items`: `item_no` BIGINT, `subject_type` (protein | protein_group | site | peptide | gene | cell_type
  | dataset | sample | other), `subject_id` VARCHAR (a catalog key, e.g. `ptm_site_id`, accession, Ensembl id),
  `subject_dataset_id` VARCHAR NULL, `value_name` VARCHAR NULL, `value` DOUBLE NULL, `rank` BIGINT NULL, `label`
  VARCHAR NULL, `attributes` JSON NULL.
- `contribution_edges`: `edge_no`, `source_type`, `source_id`, `target_type`, `target_id`, `relation`, `weight`
  DOUBLE NULL, `directed` BOOLEAN, `attributes` JSON NULL.
- `contribution_queries`: `seq`, `tool` (sql | search | describe | other), `statement` VARCHAR, `catalog_id`,
  `result_sha256`, `row_count`, `truncated` BOOLEAN, `tables_touched` JSON.

### 1.2 `contribution.yaml` / `run.json` fields

Content fields (hashed): marked H. Everything else is recorded, not hashed.

| field | type | req | notes |
|---|---|---|---|
| `contribution_manifest_version` | int | yes, H | 1 |
| `kind` | enum | yes, H | `site_list`, `cell_cell_map`, `protein_set`, `association_table`, `annotation`, `other` |
| `kind_version` | int | yes, H | which tables the kind requires |
| `definition_id` | string | yes, H | the method's definition, owned by whoever states it (D24: dataRepo defines no one's number; `GoEngine.cs:188-191`) |
| `title`, `summary` | string | yes / no | prose, not hashed (study.md: "rewording a label must not re-identify rows") |
| `agent.model.provider` | string | yes, H | `anthropic`, `openai`, ... |
| `agent.model.id` | string | yes, H | exact pinned id (`claude-opus-5-5`); aliases (`*-latest`) refused |
| `agent.model.stated_by` | enum | yes, H | `client` (always today: nothing verifies it) |
| `agent.model.evidence` | map | no | e.g. provider response id, API `model` field echoed |
| `agent.client` | {name, version} | yes | from the MCP `initialize` clientInfo the SERVER saw, attached to receipts (not captured today: `Mcp.cs` has no clientInfo) |
| `agent.software` | list {name, version} | yes, H | client harness, libraries, R/Python/.NET versions |
| `method.receipts` | list | yes (>=1), H | the MCP envelopes the result used (section 5) |
| `method.code` | list {path, sha256, language, entrypoint} | if any code ran, H | files kept in `files/` |
| `method.parameters` | map | no, H | thresholds, seeds |
| `method.prompt.mode` | enum | yes, H | `full`, `summary`, `withheld` |
| `method.prompt.text` / `.sha256` | string | per mode, H | the full text's sha256 always |
| `basis.catalog_id` | 16-hex | yes, H | must equal every receipt's `catalog_id` |
| `basis.release_id` | 16-hex | yes, H | data identity of that catalog (`Catalog.cs:1651-1661`) |
| `basis.release` | string | no, H | release name when the catalog was one |
| `basis.bundles` | list {dataset_id, bundle_id} | yes, H | the datasets the contributor relied on; checked to be a subset of the basis catalog's `catalog_bundles` |
| `basis.contributions` | list id | no, H | earlier contributions it builds on |
| `supersedes` | list id | no, H | |
| `licence` | SPDX | yes, H | default `CC-BY-4.0` (dataRepo D3); others refused unless allowed |
| `result.files` | map {name: sha256} | yes, H | the delivered tables and any extra files |
| `submitted_by` | {name, orcid?} | yes | the accountable human; not hashed |
| `submitted_utc` | string | written | not hashed |
| written by datarepo | | | `contribution_id`, `content_sha256` (full 64 hex), `datarepo_install`, `runner_version`, `contrib_layer_version`, `tables` row counts |

## 2. Identity and idempotency

- `content_sha256` = sha256 over canonical text, in the style of `EngineRunner.ArtefactId` (`EngineRunner.cs:66-74`):
  `contribution/<ContributionWriterVersion>\ncontrib-layer/<v>\n` + each H field in sorted key order (JSON, sorted
  keys, `ensure_ascii`) + `file/<name>\t<sha256>\n` per delivered file. Files are hashed as delivered bytes, as
  `StudyWriter` hashes delivered files (study.md line 96), never the written Parquet (writer-version dependent).
- Folder id = first 16 hex, matching every other id in the store. **But** the full 64 hex is stored and compared:
  the existing ids are 64 bits (`[..16]`, `EngineRunner.cs:73`), fine for our own outputs and too short for
  content an outsider supplies (a crafted collision costs about 2^32 work).
- Same content twice: the existing folder is found, its full hash compared, "already done" returned with its id
  (`GoEngine.cs:217-223` pattern). Differing full hash under the same prefix: refuse loudly.
- Who and when are NOT content: the same result submitted twice by two people is one contribution. (Open question.)

## 3. Carry-forward across releases

### 3.1 Selection: all, always
`SelectContributions(store)` = `Runner.DiscoverArtefacts(store, "ai.contribution")` plus every status record. No
input matching, no schema filter, no duplicate refusal. Contribution tables are read through their own layer
version; an old layer version is upgraded by a VIEW at build, never rewritten.

### 3.2 The guarantee, as a check
- **Invariant:** contributions(release N+1) contains contributions(release N), and the same for status records.
- `datarepo build --release vN+1 --previous-release <releases/vN/catalog>` reads vN's `catalog_contributions` and
  REFUSES if any id is missing from the store or the selection. A release with no previous release is the first.
- **Pinning:** a release writes its frozen list (`catalog_contributions`, plus `releases/<v>/contributions.lock`).
  Rebuilding an old release passes `--contributions <lock>`, mirroring the `--bundle` pins a release requires
  (`Catalog.cs:748-781`), so it does not pick up later contributions.
- Working (scheduled) builds load everything present: a contribution is served at the next publish (PLAN rule 6).

### 3.3 A re-searched deposit
The contribution is never deleted or re-pointed. The build compares `basis.bundles` with the bundles it serves and
writes `basis_status`:
- `current`: every basis bundle is the one served;
- `older_data`: a basis dataset is now served from a newer bundle (`contribution_basis.current_bundle_id` names it);
- `withdrawn_data`: a basis dataset is now held or excluded by the manifest;
- `depends_on_retracted`: a contribution in `basis.contributions` was retracted.
Its rows stay queryable; its `basis.catalog_id` still names the frozen catalog it was computed on.

### 3.4 Supersession and retraction without deletion
- A new contribution may name `supersedes: [ids]` in its content.
- A status record (`ai.contribution_status`, also content-addressed, own `run.json`): `{target, action:
  retract | supersede | note, reason, by, utc, superseded_by?}`. Written by the contributor or the operator.
- The build derives `status` = active | superseded | retracted. Nothing is removed from the store or the catalog.
- A legal takedown is the one exception (see open questions): serve a tombstone row, keep `run.json`.

### 3.5 Retention (what makes "reproduced exactly" true)
- `Prune` keeps release files only (`Catalog.cs:1668-1682`, `ReleaseOf`). Extend it: never delete a catalog file
  whose `catalog_id` any contribution cites, nor its derived directory.
- PLAN rule 1 ("the old one stays until no release names it") becomes "until no release AND no contribution basis
  names it". Any store cleanup (PXReprise has deleted superseded folders and pin folders before) must check it.

## 4. How contributions appear in the catalog; what happens to the ids

Tables (all with `contribution_id` as their provenance column, like `EngineProvenanceColumns`, `Catalog.cs:315`):
- `catalog_contributions`: id, content_sha256, kind, kind_version, definition_id, title, summary, model_provider,
  model_id, model_id_stated_by, client_name, client_version, submitted_by, submitted_utc, licence, basis_catalog_id,
  basis_release_id, basis_release, basis_status, status, superseded_by, path, record JSON.
- `contribution_basis`: contribution_id, dataset_id, bundle_id, current_bundle_id, drifted.
- `contribution_items`, `contribution_edges`, `contribution_queries` (views over the artefacts' Parquet in a folder
  catalog).
- View `contributions_current` (status active).
- `describe()`'s ReadFirst (`CatalogServer.cs:110-122`) gains: "`contribution_*` rows are claims an AI model made
  from this catalog's data, not measurements; check `basis_status` and `status`."

**Identity, decided:**
- `catalog_id` MUST change when the contribution set changes. That is the code's standing rule: anything a reader
  can query is hashed (`Catalog.cs:992-1019`: study rows, engine artefacts, notes, exclusions, census). Two
  catalogs that differ by a contribution answer differently.
- Add `contribution_set_id` = sha256 over the sorted contribution and status-record ids. `catalog_id` hashes one
  line, `contributions/<set id>`, and none when the set is empty (so today's ids do not move).
- **`release_id` should NOT include contributions.** It names the measured data (rule 9; `Catalog.cs:1646-1661`).
  Keeping contributions out means:
  - two catalogs that differ only by contributions share `release_id`, so "computed on the same data" is an
    equality test;
  - a contribution's `basis.release_id` does not churn;
  - there is no circularity: a contribution never sits inside the catalog it cites.
  `ai.*` artefacts are therefore excluded from `ReleaseId`, which today hashes every engine artefact
  (`Catalog.cs:1658-1659`).
- MCP provenance gains `release_id` and `contribution_set_id`. Today `CatalogIdentity.Base()` carries neither
  (`CatalogServer.cs:26-36`; PUBLIC_DATA step 1d said `release_id` would be there).

## 5. Reproduction

What is enough:
1. The basis catalog file with that `catalog_id` (kept, 3.5). It cannot be REBUILT from the store alone, because
   `catalog_id` hashes the manifest's notes, exclusions, restrictions and census (`Catalog.cs:1000-1019`), which are
   not in the store. Keep the file.
2. The datarepo release that served it (`catalog_meta.builder_version`; the record's `datarepo_install`).
3. Query receipts. The MCP `sql` envelope already returns `sql`, `row_count`, `truncated`, `tables_touched` and the
   provenance (`CatalogServer.Search.cs:368-380`). Add `result_sha256`: rows canonically sorted (a query without
   ORDER BY has no defined order), values in the envelope's own JSON form. A truncated receipt cannot be verified
   and is flagged.
4. Code, a lockfile and seeds, in `files/`.

`datarepo contribution verify <id>`:
- re-runs each receipt against the basis catalog and compares hashes;
- re-hashes every file;
- checks that `basis.bundles` are in that catalog.

That reproduces the DATA and the COMPUTATION exactly. The model's own choices are not reproducible: LLM sampling is
not deterministic, and model ids are retired. The record says so.

## 6. W3C PROV / RO-Crate (for interoperability)

- Contribution = `prov:Entity` (RO-Crate root `Dataset`).
- Model = `prov:SoftwareAgent`, `prov:actedOnBehalfOf` the submitter (`prov:Person`, ORCID).
- The computation = `prov:Activity`. In RO-Crate it is a Process Run Crate `CreateAction`: `instrument` = the model
  and the code, `object` = the basis catalog (identified by `catalog_id`) and its bundles, `result` = the files.
- Receipts = `prov:used`. Building on others = `prov:wasDerivedFrom`. Superseding = `prov:wasRevisionOf`.
  Retraction = `prov:wasInvalidatedBy` a status activity.
- `ro-crate-metadata.json` is generated deterministically from `run.json` and is not hashed. It travels with the
  artefact in any hosted copy, as PLAN rule 5 requires of `run.json`.

## 7. Write path

The MCP server is read-only, and D19 allows no fourth tool without benchmark evidence (`docs/mcp.md:66`; Sandbox
`READ_ONLY`, `Sandbox.cs:112`). Hosting is static (PLAN rule 7), and one publisher writes the store (PLAN line 221).
So:
- clients write `contribution.yaml` plus files to an INBOX outside the store;
- the publisher runs `datarepo contribute` at the scheduled publish: it validates, refuses or accepts, and writes
  the artefact.
- A separate, opt-in `datarepo-contribute` MCP server with one `submit` tool writing to the inbox is possible later;
  it never touches the store.

## 8. Open questions for the user
1. Who may submit (operator, lab, anyone)? Through what channel for the public (a GitHub PR to a contributions repo,
   Zenodo)?
2. Is a named human required for every contribution? (Recommended: yes; journals do not accept AI as an author.)
3. Prompt storage: full, summary, or withheld by default? (Recommended: summary + sha256 of the full text.)
4. Accept contributions computed on WORKING catalogs, which pins those files forever, or only on releases?
5. Confirm: contributions are in `catalog_id` but not `release_id`.
6. A review gate (`unreviewed` until someone accepts it) before a contribution is served to the next model?
7. Takedown: what happens on a legal or ethics request (tombstone versus true deletion)?
8. Who owns each `kind` and its `definition_id`?
9. A DOI per contribution, or only per release?
10. Same result submitted by two people: one id (as designed), or one per submitter?

## 9. Risks
- **Self-declared model identity.** Nothing in MCP carries the model id. It is recorded as stated, never as
  verified.
- **Pruning and store cleanup** can break reproduction (`Catalog.cs:1668-1682`; the 10-12 pin deletion incident).
- **64-bit ids on outsider content** (`EngineRunner.cs:73`).
- **AI claims read back as facts** by the next model: labels in `describe`, `status` and `basis_status` are
  essential.
- **Volume and spam** in an add-only store.
- **Sensitive text** in prompts.
- **Provider terms on output licensing.**
- **Unordered or truncated receipts.**
- **Retraction cascades** through `basis.contributions`.
- **Contribution-layer schema evolution** must never filter old ones out (the trap in `Catalog.cs:1070`).
