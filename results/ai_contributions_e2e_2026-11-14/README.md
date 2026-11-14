# AI contributions, end to end on a copy of aging's store (2026-11-14)

Slice V6 of `design/AI_CONTRIBUTIONS_V2.md`: the real program, the real MCP server over stdio, and a copy of aging's whole
re-ingested store (`F:\datarepo_scratch_150\reingest150`, the 192 deposits of `results/reingest_150_2026-11-12/` on
`feat/1.5.0`). Nothing of aging's was read or written.

## How

- **Program:** `feat/ai-contributions-v2` at `7054ba1`, published self-contained as `datarepo 1.6.0-scratch.7054ba1`.
- **Catalog:** a folder catalog of the copy's 192 bundles, built into a new folder `F:\datarepo_scratch_150\ai_e2e\catalogs`:
  catalog `5af574ca34ae8c4d`, 3,981 checks passed, 333 s (every deposit derived).
- **Agent 1** (`agent.py`): an MCP client over stdio, `datarepo mcp --contributions <inbox>`. It asked two questions, saved a
  result citing both by `session_call.seq`, then tried to save the same result naming a person. `agent_out.json` is what came
  back.
- **The operator:** `contribute inbox`, `contribute accept`, a rebuild, queries, `contribute verify`.
- **Agent 2** (`agent2.py`): `datarepo mcp --show-prior`, one question on the table agent 1 read, and `describe`; then a rebuild.

The run wrote two folders into the copy's store, `_sessions/` and `_contributions/`. Its bundles are untouched.

## What happened

| step | result |
|---|---|
| the client is told its calls are public | yes: `instructions` is the notice at `initialize` |
| tools listed with an inbox | four: `datarepo_describe`, `datarepo_search`, `datarepo_sql`, `datarepo_save_result` |
| save, citing both queries | `pending_review`, 2 observed queries, 0 stated; the store unchanged |
| save naming a person | refused (`ToolError`), and the name is in no session file (`grep` finds 0) |
| `contribute inbox` | lists the one request, with its session |
| `contribute accept` | accepted `7e65324a72c36f5d`: both observed queries match the record on disk |
| rebuild | a new catalog `6557d7259e60cedb` (the first result and the first record), 3,981 checks passed, 118 s (192 deposits reused) |
| `contributions` | `table`, model `e2e-agent-0.1` stated by `client`, client `e2e-agent`, accepted, no person, `active` |
| `contribution_queries` | both observed, 3 rows each |
| `sessions`, `session_calls` | one session, 4 calls: two `sql` ok, the save ok, the refused save `error` |
| `contribute verify` | both queries reproduced on `5af574ca34ae8c4d`, the catalog the result was computed from, not the latest; exit 0. It says that is all it checks |
| agent 2's answer | carries `prior_work`: agent 1's query on `dataset_overview` and its saved result |
| agent 2's `describe` | 1 active result; the public record holds 2 sessions |
| rebuild after agent 2 | `unchanged`, the same id `6557d7259e60cedb`, while `sessions` already shows both sessions (agent 2: 2 calls) |
