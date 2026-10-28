# Design: AI results saved back into the catalog through MCP (dataRepo `datarepo mcp`)

Status: proposal, 2026-10-28. Read-only review of the code; no repo file was edited.
Paths below are relative to `E:\CodeReview\dataRepo` unless they start with `PXReprise/`.

## 0. What the grant promises, and what exists today

Grant text, in four parts: (a) answers are calculated from the data; (b) an AI result is saved back into the catalog;
(c) the record says which model, how, and from which data; (d) each release is frozen, so a result can be cited and
reproduced exactly.

Today:

- (a) is built. Three read tools (`Mcp.cs:32-72`). Every answer carries a provenance block that the query cannot
  change (`CatalogServer.cs:289-330`; `docs/mcp.md:132-172`).
- (b) and (c) are absent. The `sql` tool's own description says "The catalog is derived and cannot be written to"
  (`Mcp.cs:62-63`).
- (d) is half there. `release_id` hashes the bundles, study bundles **and engine artefacts** (`Catalog.cs:1651-1661`).
  A result stored as an engine artefact is therefore frozen by any release that names it.
- Gaps found on the way:
  - The MCP provenance block has no `release_id`. `CatalogIdentity.Base` carries only `catalog_id`
    (`CatalogServer.cs:26-36`), although PUBLIC_DATA step 1d says both ids go into MCP provenance.
  - No tool declares `annotations` (`Mcp.cs:153-160`). By the spec's defaults (`readOnlyHint` false,
    `destructiveHint` true), a client must assume today's three read tools may be destructive.
  - The server reads neither `clientInfo` nor a session id.

## 1. The write path

### 1.1 Where writing lives

**The decision has two halves.** An opt-in server mode writes a *submission* to an inbox. A separate operator verb,
`datarepo contribute accept`, re-checks it and turns it into a store artefact. No agent-reachable code ever writes the
store or the catalog.

| option | verdict |
|---|---|
| Always on, in the normal server | **No.** It breaks the promise `--install` registers today: read-only by default (`McpCommand.cs:127-136`). Every existing registration would silently gain a write tool. |
| A separate CLI (`datarepo contribute`) that the MCP tool shells out to | **No, as the only path.** The session ledger (section 3) exists only inside the server process. A CLI that accepts a ledger excerpt on stdin will take a forged one from anyone with a shell. The server is the only witness. |
| **Opt-in server mode `--contributions <inbox-dir>`, plus the operator verb `datarepo contribute accept/reject/list`** | **Yes.** |

Why the opt-in mode keeps the lockdown intact:

- The sandbox locks the **DuckDB connection**:
  - `ACCESS_MODE=READ_ONLY` (`Sandbox.cs:112`);
  - `disabled_filesystems` or `allowed_directories` -> `enable_external_access=false` -> `lock_configuration=true`
    (`Sandbox.cs:131-149`);
  - SELECT/EXPLAIN/PRAGMA/SHOW only (`Sandbox.cs:81`).
- A submission is written by ordinary C# file I/O on a different code path. No DuckDB statement is ever
  writable. The inbox is outside `allowed_directories`, so `sql` still cannot read the inbox.
- The inbox is named by explicit path and never discovered, as the catalog is (D13, `docs/mcp.md:46-51`,
  `McpCommand.cs:120-124`). Without the flag:
  - the tool list is byte-identical to today's;
  - the Python-parity test still passes (`McpTests.cs:341-350`).
- `--install --contributions <dir>` writes the flag into the entry's `args`, so the choice is visible in the client
  config.

Why the store write is a separate operator step:

- The charter says dataRepo "operates nothing" and the operator RUNS everything on stored data
  (`design/CHARTER.md:48`, `:56`, `:76`). An agent session is not the operator.
- The store is add-only (`PXReprise/design/PLAN_public-data.md:54-55`).
- `accept` reuses the runner's guarantees unchanged:
  - release builds only (`EngineRunner.InstallIdentity`, `EngineRunner.cs:41-59`);
  - a content-addressed id (`EngineRunner.cs:66-74`);
  - an atomic staged write that refuses an existing id (`EngineRunner.cs:86-130`).
  The artefact goes to `<store>/_engine/ai.result/<id>/` with `run.json` (`Runner.cs:53-55`).

### 1.2 Tools, only when `--contributions` is set

**`datarepo_save_result`**

- Annotations: `{readOnlyHint:false, destructiveHint:false, idempotentHint:true, openWorldHint:false}`.
  - destructive false: it is additive;
  - idempotent true: the id is content-addressed;
  - open-world false: the inbox is a closed domain.
- These are hints only. The spec says "Clients should never make tool use decisions based on ToolAnnotations received
  from untrusted servers" (schema reference, `ToolAnnotations`).

Input schema:

```json
{"type":"object","required":["kind","title","model","method","calls","payload"],"additionalProperties":false,
 "properties":{
  "kind":{"enum":["site_list","protein_list","relation_graph","table"]},
  "title":{"type":"string","maxLength":200},
  "summary":{"type":"string","maxLength":4000},
  "model":{"type":"object","required":["id"],"additionalProperties":false,"properties":{
     "id":{"type":["string","null"],"maxLength":200,"description":"The exact model id you are running as, from your own system prompt. null if you do not know it. Never guess."},
     "provider":{"type":["string","null"],"maxLength":100},
     "source":{"enum":["system_prompt","user_told_me","unknown"]}}},
  "method":{"type":"object","required":["description"],"properties":{
     "description":{"type":"string","maxLength":8000},
     "code":{"type":"string","maxLength":262144},
     "language":{"type":"string"},
     "software":{"type":"array","items":{"type":"object","required":["name","version"]}},
     "parameters":{"type":"object"}}},
  "calls":{"type":"array","minItems":1,"maxItems":500,"items":{"type":"integer"},
     "description":"The `call.seq` numbers of this session's tool calls whose answers this result was computed from."},
  "builds_on":{"type":"array","items":{"type":"string","pattern":"^[0-9a-f]{16}$"},"maxItems":50},
  "stated_inputs":{"type":"array","maxItems":50,"items":{"type":"object","required":["description"]}},
  "payload":{"type":"object","description":"Rows in the kind's schema; describe('ai:<kind>') gives it."}}}
```

Output: `{result_id, status:"pending_review", inbox_path, catalog_id, release_id, catalog_kind, observed_calls:[...],
checks:[...], labels:{model_id_status, inputs_truncated, keys_observed}, provenance}`.

- A refusal returns `{error, message, hint}`, like every other `DataRepoException` (`Mcp.cs:91-129`).
- Because `isError` is false on a refusal, the agent can fix the call and send it again (`McpTests.cs:363-365`).

**`datarepo_session`**

- Annotations: `readOnlyHint:true`, `openWorldHint:false`.
- Input: `{"from_seq":int?, "limit":int<=200, "pending":bool}`.
- It returns the ledger entries (seq, tool, arguments, hashes, catalog_id) and, with `pending`, the inbox submissions
  of this instance. Each submission is labelled "pending review: in no catalog, not citable".
- Needed because an agent loses its earlier `call.seq` values when its context is compacted.

**Every tool**, read tools included, in both modes, gains annotations:

- `readOnlyHint:true` and `openWorldHint:false` on describe, search and sql.
- This is a free correctness fix; the spec defaults currently say "destructive".

**Reading accepted results needs no new tool.** `docs/mcp.md:64-68` adds a fourth tool only when a benchmark shows a
wrong answer. Accepted results instead become catalog tables, reached through the three existing tools (section 5).

## 2. Model identity

**Protocol facts:**

- `initialize` carries `clientInfo: Implementation {name, title?, version}` (schema, `InitializeRequest`,
  `Implementation`). That identifies the client application, not the model.
- The C# SDK 2.2.0 exposes it as `McpServer.ClientInfo`, plus `McpSession.SessionId` (checked in
  `ModelContextProtocol.Core.xml`).
- `sampling`'s `CreateMessageResult.model` is "The name of the model that generated the message". It names the model
  the client chose for the *server's* request, steered by `ModelPreferences` hints. That may not be the agent's model.

**Record kept (`model` block of `run.json`):**

| field | from | label |
|---|---|---|
| `model.id`, `provider` | the agent's argument | `"stated_by": "agent"`, with `source` (`system_prompt`, `user_told_me`, `unknown`) |
| `client.name`, `client.version`, `client.title` | `McpServer.ClientInfo`, captured at initialize | `"observed_by": "server"` |
| `model.confirmed_by_user` | elicitation, if the client declared the `elicitation` capability | `accept`, `edited`, `decline`, or `not_asked` |
| `model_id_status` | computed | `stated`, `stated_and_user_confirmed`, `stated_inconsistent_with_client`, or `unknown` |

**Rules:**

- **The server never fills `model.id`.** It does not copy it from `clientInfo` or from a sampling reply. A sampling
  probe is not used: it would record a model the client picked, labelled as if it were the author.
- **Cross-check:**
  - A small, versioned table maps known client names to the providers they run.
  - A stated provider that contradicts it gives `stated_inconsistent_with_client`. That is a label, not a refusal:
    clients can route models in ways we cannot see.
- **Unknown:**
  - `id: null` with `source:"unknown"` is **accepted into the inbox but refused by `accept`**. The grant promises
    "which model made it".
  - Before acceptance the operator can supply the id only through `accept --model-id ... --model-id-source operator`,
    recorded as such.
- **Elicitation:** the confirmation asks "Save '<title>' as made by <model.id>?" with an editable model field.
  - This is allowed: the spec forbids requesting *sensitive* information, and a model id is not sensitive.
  - The server checks the client capability first; clients "MUST declare the `elicitation` capability"
    (spec, elicitation page).

## 3. "How": the session ledger

**Session:**

- `session_id` is 128 random bits generated at process start. For stdio, one process serves one client and is one
  session.
- Over Streamable HTTP, use `Mcp-Session-Id`, which "SHOULD be globally unique and cryptographically secure"
  (transports, Session Management).

**Entry.** One per `tools/call`, written in `CallTool` (`Mcp.cs:187-237`) after the answer is serialized:

```
seq (1,2,3... monotonic; the existing semaphore, Mcp.cs:152, already serializes calls),
utc, tool, arguments (canonical JSON; the SQL text in full, at most 64 KB),
args_sha256, catalog_id, release_id, result_sha256, row_count, truncated, truncated_by,
tables_touched (+ undetermined), error (name) | null, prev_hash, entry_hash = sha256(prev_hash || canonical(entry))
```

- **`result_sha256`** hashes the structured content minus `provenance` and `elapsed_seconds`. Its rows are hashed
  as a **sorted multiset**, so a query without ORDER BY reproduces.
- **Hash chain:** an excerpt cannot be reordered, and entries cannot be dropped silently.
- **Envelope:** in contributions mode every answer gains `call: {session, seq, entry_hash}`. The agent cites seq
  numbers, never content.

**Spill:**

- The full answer of each call is kept in `<inbox>/sessions/<session>/<seq>.json.zst`.
- Caps: 200 MB per session, then the oldest are dropped. A dropped call can still be cited but is labelled
  `body_evicted`.
- The ledger itself is appended to `sessions/<session>.jsonl` for audit, with a cap of 20,000 entries per session.

**At save:**

- The server copies the cited entries (the agent cannot edit them) into `observed_calls`.
- Whatever the agent did outside the server goes into `stated_inputs`, labelled "stated, not observed". Examples: a
  local clustering, an external table.
- `method` is labelled "stated" too. The server cannot see the computation; it can only bind the computation's inputs.

**Anti-fabrication checks:**

- **Key membership.** For kinds keyed on catalog ids (`site_list` -> `ptm_site_id`; `protein_list` -> accession;
  `relation_graph` node ids), the server checks every key against the catalog by one parameterized query. It also
  counts how many keys appeared in the bodies of the cited calls: `keys_observed: n of m`.
  - A key that is not in the catalog is refused.
  - A key in the catalog but not observed is labelled.
- **Re-execution at `accept`.**
  - `accept` re-runs every cited `sql` call against a catalog with the same `catalog_id`. If that file was pruned
    (`Catalog.cs:1668`), it uses a catalog rebuilt from the recorded bundle list.
  - It compares `result_sha256` and records `reproduced: true/false` per call.
  - Calls that were truncated without ORDER BY are labelled `nondeterministic_truncated` and are not used as proof.
- **Local honesty.** `docs/mcp.md:221-225` already says the local sandbox is not a security boundary, because the
  agent has the filesystem. An agent could therefore edit inbox files. Tamper-evidence locally rests on
  re-execution, not on signatures, and the record says so.

## 4. Validation on save (refuse, don't guess)

1. **Catalog.**
   - Every cited call ran against the served `catalog_id`. One server holds one catalog (D13).
   - A call made while `catalog_file_changed` was set (`CatalogServer.cs:193-219`) is labelled.
   - A citation of any other catalog id is refused.
2. **Bundles.**
   - Every `dataset_id`/`bundle_id` in the payload or `stated_inputs` must be in `Identity.Bundles`
     (`CatalogServer.cs:62-64`); otherwise the save is refused.
   - The record copies the full bundle list, not only `catalog_id`. A working catalog file can be pruned, but its
     bundles are immutable, so the result stays reproducible.
3. **Working build: allowed and labelled.**
   - `docs/mcp.md:53-55` deliberately allows exploring working builds.
   - The record carries `catalog_kind`, `release_id` and `citable:false`.
   - It becomes citable only when a release's `release_id` includes the accepted artefact.
4. **Schema per kind.**
   - Each kind's JSON Schema is generated from `schema/datarepo.yaml`, as the column prose is (`docs/mcp.md:82-85`).
   - `describe('ai:site_list')` returns it.
   - Unknown kinds and extra properties are refused.
   - Every numeric column needs a stated meaning in `method.parameters`.
5. **Calls.**
   - At least one observed call.
   - A call that errored or was refused cannot be cited.
6. **Size.**
   - payload at most 5 MB and 100,000 rows; code at most 256 KB; `builds_on` at most 50.
   - At most 20 saves per session; inbox at most 2 GB (refused when full).
7. **`builds_on`.** Every id must exist as an accepted artefact or as a pending submission. A pending one is labelled
   `builds_on_unreviewed`.

## 5. Discovery

- **Results in the catalog.** `datarepo build` gains a selection path for `ai.result` artefacts. It is separate from
  `SelectArtefacts`, which keys engines on a search database (`Catalog.cs:1056-1089`). The path loads:
  - `ai_results`: one row per result (id, kind, title, model, client, `model_id_status`, `catalog_id_basis`,
    `release_id_basis`, `builds_on`, written/accepted utc, `inputs_all_served`);
  - `ai_result_calls`;
  - `ai_result_bundles`;
  - one row table per kind (`ai_site_lists`, `ai_relation_edges`, ...).
  - **`inputs_all_served`** is false when a cited bundle has since been superseded in this catalog. Such a result is
    shown, never hidden, and the reason is stated.
- **Through the existing tools:**
  - `describe()` lists `ai_results` with a count;
  - `search(kind="result")` matches titles, kinds, accessions and site ids;
  - `describe('<result_id>')` returns the record.
  - The `sql` envelope adds `prior_results_on_these_tables` when the touched tables are the inputs of accepted
    results. This works like `study_tables_on_these_samples` (`CatalogServer.Search.cs:409-419`): a field, because
    an envelope field cannot be skipped.
- **Prompting the agent:**
  - `InitializeResult.instructions` ("MAY be added to the system prompt"): "Before computing a derived result (a
    ranked site list, a relation map), call search(kind='result'): another model may have made it from this catalog.
    Build on it with builds_on rather than recompute, unless its inputs_all_served is false."
  - `datarepo_save_result`'s description repeats this.
- **Text written by a model is data.** Free-text fields come back as `untrusted_text` with a sentence saying so. They
  are length-capped and never placed in `instructions`.

## 6. Security and abuse

**Local stdio (now):**

- **Who may write:** whoever started the client with `--contributions`. The spec's human in the loop applies:
  clients "SHOULD ... Present confirmation prompts to the user for operations" (tools page). Elicitation adds a
  server-side confirmation where the client supports it.
- **Rate limits:** the spec says servers "MUST ... Rate limit tool invocations" (tools, Security Considerations).
  That means 20 saves per session and 60 per hour per inbox.
- **Review queue:** the inbox *is* the queue. `contribute list` shows each submission's checks; `accept` and
  `reject --reason` are the operator's alone; rejected submissions are moved, never deleted.
- **Retraction:** a new artefact with `retracts: <id>`, never a deletion (rule 1).

**Public endpoint (future):**

- `PLAN_public-data.md:115-120` (rule 8; dataRepo D16) allows a hosted MCP "only with evidence that someone wants
  it". Rule 7 says no servers. A public *write* endpoint is therefore a new decision for the user, not an extension
  of this design.
- If it is made:
  - authentication on every connection ("SHOULD implement proper authentication");
  - `Origin` validation ("MUST", transports, Security Warning);
  - per-identity quotas;
  - the session ledger kept server-side, out of the writer's reach, which makes it authoritative;
  - the FRAMEWORK stage-two SQL allow-list (`docs/mcp.md:221-225`) before any anonymous read;
  - submissions from unauthenticated sessions refused outright;
  - nothing reaches a catalog without operator `accept`.

**Tests**, in the pattern of `McpTests.cs:329-380` (in-memory `Pipe` + `McpClient`):

- without the flag, the tool list is unchanged;
- with the flag:
  - the ledger seq is monotonic and the chain verifies;
  - a forged seq is refused;
  - a foreign catalog_id or bundle is refused;
  - a key absent from the catalog is refused;
  - the clientInfo fixture is recorded;
  - elicitation-declined is labelled `decline`;
  - `accept` re-executes and flags a tampered `result_sha256`.

## Open questions

1. **Definition id** (charter S4, `design/CHARTER.md:170`): is an AI result's definition `ai:<result_id>` (the
   result is its own method), or must a kind cite an owner's definition?
2. **Who is the operator for contributions?** PXReprise (D41, publication architecture) or each instance's operator?
   This needs a charter seam (S23).
3. **A release that freezes a result built on a superseded bundle:** include it, labelled, or hold it out?
4. **`release_id` in MCP provenance:** owed by PUBLIC_DATA step 1d; this design needs it first.
5. **Payload kinds for the first release:** are `site_list` and `relation_graph` enough for the grant's two examples?
   Who signs the kind schemas: dataRepo (schema only) or the consumer?
6. **Results computed outside the server:** should `accept` require `method.code` for them, so that the "how" is
   re-runnable, or is the description enough?

## Risks

- **Stated model ids are only as honest as the agent.** The labels make that visible. They do not prevent it.
- **Local tampering.** An agent with filesystem access can forge inbox files. Re-execution catches fabricated
  outputs, but not a dishonest `method` description.
- **Nondeterminism.** Truncated queries without ORDER BY, and future DuckDB versions, can make re-execution fail
  for innocent reasons.
- **Prompt injection.** Model-written titles and summaries enter later agents' context.
- **Scope creep.** A write tool argues for a hosted endpoint, against rule 7 and D16.
- **Byte-parity.** Adding `call` to envelopes in contributions mode is fine. Adding annotations to the read tools
  changes `tools/list`, so the Python fixture (`McpTests.cs:342-350`) must be regenerated or the comparison relaxed.
