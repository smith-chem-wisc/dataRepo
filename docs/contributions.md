# Results saved back: AI contributions

A result an AI model (or a person) computes from a catalog can be saved back into the repository, so the next researcher
or model finds it and builds on it instead of redoing the work. Every later catalog and release carries it, with the model
as its client stated it, the exact data it used, and the queries the server saw it run.

Nothing reaches the repository on its own. An agent's result goes to an **inbox**, and the operator accepts or rejects it.

## The flow

```bash
# 1. Serve a catalog folder with an inbox. The server lists a fourth tool, datarepo_save_result, only then.
datarepo mcp --catalog /data/repo/catalogs --contributions /data/repo/inbox

# 2. The agent asks its questions, then calls datarepo_save_result, citing the datarepo_sql calls it used
#    by their place in the public record (session_call.seq). The result waits in the inbox.

# 3. The operator looks at what is waiting, and accepts or rejects each one.
datarepo contribute inbox  --store /data/repo/store --inbox /data/repo/inbox
datarepo contribute accept 3f9a0c2e1b4d5a67 --store /data/repo/store --inbox /data/repo/inbox --catalog /data/repo/catalogs
datarepo contribute reject 77c1e0a9d2b3f456 --store /data/repo/store --inbox /data/repo/inbox --reason "duplicates 3f9a0c2e1b4d5a67"

# 4. The next build loads every accepted result; every later release carries it.
datarepo build ... --out /data/repo/catalogs
```

`accept` checks the result again in full before anything is written: the catalog it names must exist and hold every bundle
it names, and every query marked observed must match the server's public record on disk. A rejected request is kept under
`rejected/` with the reason beside it. Nothing is ever deleted: a result is withdrawn by a retraction, which is another
contribution.

## What a saved result claims, and what it does not

- **The model** is as the client stated it. No server can see which model is behind a client.
- **No person is named through the server.** Everything an agent sends is in the public record, so the save tool takes no
  name. The person accountable for a result is the operator who accepts it: `accept --by NAME` records a name only if
  given, and the time of acceptance always.
- **`observed`** on a query means only that the server ran it, on that catalog, and it returned rows with that hash. It does
  not mean the result follows from those rows: nothing checks that, and a query such as `SELECT 1` can be cited beside
  any result.
- **`verify` never calls a result reproduced.** It re-runs a result's queries on the exact catalog it was computed from (never
  the latest, which would answer a different question), with the row limit each ran with, and reports whether each returned
  the same rows. A model's judgement is never re-runnable; a result that used randomness reproduces within its tolerance.

```bash
datarepo contribute verify 3f9a0c2e1b4d5a67 --store /data/repo/store --catalog /data/repo/catalogs
datarepo contribute show   3f9a0c2e1b4d5a67 --store /data/repo/store
datarepo contribute list   --store /data/repo/store
```

**Once a result's data leaves the store**, after a whole-store re-ingest removes the old bundles, the result stays readable in
every catalog, and its queries can no longer be re-run. `verify` says so (`basis_in_store: false`, outcome `basis_gone`),
apart from a query that fails for another reason. What to keep is the operator's call.

## Where they live, and what a catalog shows

- Accepted results: `<store>/_contributions/<id>/contribution.json`, beside the bundles. The id is a hash of exactly what was
  submitted, so it never moves, and accepting adds nothing to it.
- A catalog built from a store holding any result has the tables `contributions`, `contributions_current` (neither retracted
  nor superseded), `contribution_basis`, `contribution_queries`, `contribution_items`, `contribution_edges` and
  `contribution_builds_on`. A store holding none builds exactly the catalog it did.
- `describe` tells an agent that saved results exist; `mcp --show-prior` adds the earlier work on the same tables to each SQL
  answer.
- **A release keeps them:** `build --release` records every result it carries, and every later build in that catalog folder
  refuses if one is gone. `--keep` never prunes a catalog file a result was computed from.

The public record of every call is described in [mcp.md](mcp.md#the-public-session-record).
