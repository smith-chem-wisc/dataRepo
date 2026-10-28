# AI results in the catalog: what the grant claim requires (integrity review, 2026-10-28)

Grant context: Task 3.3 draft (`E:\Proposals\2026_NIH_Payen_SCP_renewal\Task3.3_draft_2026-10-26.docx`, para 3) and outline rule L9 ("LLMs stay off the path that produces numbers", `Aim3_outline.md:76`). The draft's own notes list write-back, hosting and DOI releases as unbuilt.

## 1. Claims, what exists, acceptance tests

**C1. An assistant turns plain-English questions into database queries.**
Exists: three MCP tools, `describe`, `search` and read-only `sql` (`dataRepo\docs\mcp.md:64-130`), over local stdio only (`PLAN_public-data.md:30`). P11: 17/2/0/1 on the 32-dataset catalog, one agent invented a dataset (`Aim3_outline.md:56`). Not hosted.
*Test:* run the benchmark against a named release. Every graded answer's log contains at least one `datarepo_sql` or `search` call, and the answer cites that call's `catalog_id`.

**C2. "Every answer is calculated from the actual data, not from memory."**
Exists: data provenance on every answer (`catalog_id`, bundles, `catalog_kind`; `mcp.md:132-172`), plus guards for empty tables and NULLs (`mcp.md:191-217`). Missing: anything that ties the assistant's prose to the rows. The server cannot stop a model adding a number from memory.
*Test:* an automated audit of N benchmark transcripts. Every number and identifier in the final answer must match a value in a tool result from the same session. Unanswerable questions must answer "no data". Report the miss rate; the bar is zero silent misses (`mcp.md:257-264`). As worded, this claim fails if one answer has a remembered number.

**C3. A new AI result is saved back into the catalog.**
Exists: study bundles (`dataRepo\docs\study.md`). They are content-addressed and add-only, delivered by the operator, opt-in at build, pinned by `--study`, and refused with `--release` + latest (`study.md:118-127`). Missing: an AI-results layer. MCP is SELECT-only (`mcp.md:231`), and dataRepo D19 rules out a fourth tool. Write-back must therefore go through the operator's `datarepo study`-style path, never through an agent writing directly.
*Test:* submit result R (for example, 200 nominated sites) from model M against release v0.3. The writer refuses R if any input cannot be resolved. Otherwise R gets a content id, and `build --release v0.4 --study ai=<id>` lists R with status `unreviewed`.

**C4. A record of which model made it, how, and from which data.**
Exists: data identity (`catalog_id` = hash of the dataset/bundle set; release pins). The runner records an engine's release and the sha256 of each input (`CHARTER.md:98-107`). Age effects carry `method` and `method_version` (`study.md:66-68`). Missing: model identity, the queries run, the code and parameters, and who is accountable.
*Test:* R's record holds the source catalog_id or release, each executed SQL statement with its result sha256, the model identity with its source label (section 3), the code commit or prompt hash, the parameters and seeds, and the submitter's ORCID. `describe("ai_results")` documents every field.

**C5. The next researcher or model can look it up and build on it.**
Missing: results discoverable through `search` (a `kind="result"`), lineage (`derived_from`), and status.
*Test:* model M2 finds R through `search` on release v0.4, uses it, and submits R2. R2's lineage names R's id. If R is later retracted, R2 shows `input_retracted` and is not deleted.

**C6. Each release is frozen once published.**
Exists: `--release` requires every dataset to be pinned (`operating.md:301-305`). One release exists, v0.1 (2026-09-19). It is private, not hosted and has no DOI (`F:\aging_data\repo\releases\v0.1\RELEASES.md:125-126`). Freezing today is a folder convention on one disk. Working builds are deleted (five in `catalogs\` now). A superseded bundle may be deleted once no release names it (`PLAN_public-data.md:54-55`), so a result computed on a working build can lose its inputs.
*Test:* release v0.3 is deposited (Zenodo DOI) with its bundle list and checksums. Re-downloading it gives the same catalog_id. A result saved against a working build is refused, or it pins its bundles, so cleanup cannot delete them.

**C7. Any result can be cited and reproduced exactly.**
True only for deterministic computations.
*Test:* re-running R's recorded queries on v0.3 with the recorded DuckDB version returns byte-identical rows, whose sha256 matches the record. This needs an `ORDER BY` on every saved query: DuckDB's row order and parallel float sums are not otherwise stable. A model's judgement cannot pass this test (section 2).

## 2. What makes an AI result trustworthy enough to build on

- **Origin class, on every row and in every view:** `pipeline`, `released_engine` (the runner), `human_curated` or `ai_model`. AI results live in their own layer and never in core tables (`study.md:28-29`). The `describe` and `search` output must label them.
- **Status, never deleted:** `unreviewed` → `reviewed` (by whom, with ORCID, and when) → `superseded_by:<id>` or `retracted:<reason>`. A release freezes each result's status as of that release. A later release changes the status by adding a row, never by editing one.
- **Observed vs stated provenance:**
  - *Observed:* what the server or operator saw, namely the SQL executed, the catalog_id, the result hash and the time. The server must emit a receipt per call. Today an answer carries only the catalog's provenance (`mcp.md:134-139`).
  - *Stated:* what the client asserts, such as the model, the prompt and the intent.
  - Store the two in separate columns and never promote a stated field to an observed one. dataRepo learned this with `tables_touched` (`mcp.md:141-189`).
- **Refuse, don't drop:**
  - inputs that do not resolve to a retained catalog or release;
  - queries that do not re-execute to their recorded hash at submission;
  - an id (site, protein, cell) that the source catalog does not hold, as the `study-reference` check already does (`study.md:144-148`);
  - an undeclared definition or method id.
- **Reproducibility class, required on every result:**
  - R1, a deterministic query: exact re-run.
  - R2, released code with pinned inputs: exact re-run.
  - R3, a stochastic computation (embedding training, for example) with seeds and environment recorded: re-runnable, equal within a stated tolerance, not bitwise.
  - R4, a model's judgement (an LLM nominating sites): the inputs and the verdict are frozen, and the verdict cannot be regenerated.
  - Grant language must say "reproduced" for R1 and R2 only.
- **Evidence beside the claim.** An R4 nomination should carry the R1 queries that support it, so a reviewer can check the evidence even when the judgement cannot be re-run.

## 3. "Which model"

- **LLMs:** provider; the exact model id as the API returns it (for example `claude-opus-5-5`); the snapshot or date if the provider versions one; the access route (API or consumer app); the call time in UTC; sampling settings if known; and hashes of the system prompt and tool list.
- **Trained models:** the checkpoint sha256, the code commit, the release of the training data and the held-out split, and the seeds.
- **Honesty about identity.** An MCP server sees the client's name and version, not which model is calling. Record `model_identity_source`:
  - `observed_by_operator_harness` when our own harness made the API call and logged the response's `model` field;
  - `client_stated` otherwise.
  - Show the label beside the identity everywhere it appears.
- **Expected deprecation.** Providers retire model ids. Say that an R4 result's model may no longer be available. That is why the verdict is frozen and the evidence is kept.

## 4. What must not be claimed yet, and wording fixes

Nothing beyond C1 (local) is built:
- no hosted assistant;
- no write-back;
- no model record;
- no public release, and no DOI.

The paragraph must read as proposed work. It also overreaches in three places:

1. "so every answer is calculated from the actual data rather than from the assistant's memory": unenforceable, and contradicted by P11's invented dataset.
   *Replace:* "Numbers in its answers come from queries it runs on the catalog, and each answer shows the query and the catalog release used, so the reader can check it."
2. "that result will be saved back into the catalog": implies automatic write.
   *Replace:* "results that pass validation will be added to the catalog as a separate, clearly labelled layer, marked as AI-produced and as reviewed or unreviewed."
3. "so any result can be cited and reproduced exactly": false for model judgements.
   *Replace:* "so every result can be cited. Results computed by queries or released code can be re-run exactly. A model's judgement is kept with the exact data and evidence it used, so it can be inspected and tested."

Also add "where the model can be identified, its provider and version" to the sentence about which model made a result.

These are fact corrections. Per NOT-OD-25-132, the PIs should write the final prose themselves.

## 5. Policy considerations

- **Journals (ICMJE, COPE, Nature, ACS, Elsevier):** an AI cannot be an author, its use must be disclosed, and humans stay accountable. Every stored AI result therefore needs a named accountable person (ORCID), and a citation should cite the result id, the release DOI and the model disclosure. The `ai-research-policy` skill has the current texts.
- **NIH:**
  - Under the Data Management and Sharing Policy (NOT-OD-21-013), contributed results are shared scientific data, and they need metadata and a repository with persistent identifiers. That means the Zenodo releases, not one local disk.
  - NOT-OD-25-132 governs the application's prose, not the stored outputs.
- **Licence:**
  - Catalog data are CC BY 4.0 (`architecture.md:12`). A contributor must grant CC BY 4.0, or CC0, at submission.
  - Check each model provider's terms. Most assign outputs to the user, but some restrict using outputs to develop competing models, which matters for "the next AI model can build on" if that means training.
- **Personal data:**
  - Store the SQL that was executed (observed) and never conversation transcripts or prompts: those may hold unpublished data or personal details.
  - Store no IP addresses or account ids.
  - The only person recorded is the accountable submitter, by ORCID.
  - Results must add no donor-level identifiers beyond what the public deposits already carry, and must never ingest controlled-access data.
