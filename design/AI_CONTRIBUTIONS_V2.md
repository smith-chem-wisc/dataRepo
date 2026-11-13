# AI contributions, reworked on 1.5.0

**Status: started 2026-11-13 (D71) on `feat/ai-contributions-v2` (worktree `code/_wt_ai`), from `feat/1.5.0` at `91901d0`.**
The user: "answer that way and start the work". Its own release, right after 1.5.0 is live, on the user's word.

## Where it comes from

- **PXReprise built the first version** on `feat/ai-contributions` (2026-10-28, `1db8a53`, 29 files, about 4,500 lines), at the
  user's request: "you better start building it or I am a liar". Its design is `design/AI_CONTRIBUTIONS.md` on that branch (A1-A18,
  slices S1-S12), with four expert reviews in `design/ai_contributions/experts/`. That branch is the specification we read from.
  It is 239 commits behind master and is not merged.
- **Our review said: not as it stands** (our PXReprise 097, 2026-11-06, ten findings, G129). Take the contributions after three
  fixes, redo the public session record, and build the host last.
- **The user's rulings since:**
  - **D57 (2026-11-07):** no host for now; the users are the user and Alex, on this machine. An AI's result arrives in the
    operator's inbox and a person reviews it. Saving asks nobody to fill anything in: the server records what it can itself (the
    model as its client states it, the session's queries, the bundle ids they read, a hash of the rows). Old results keep pointing
    at the data they used, and the build carries them across a re-ingest. What `observed` and `reproduced` may claim was not
    answered, so the narrow meanings stand.
  - **D60 (2026-11-11):** 1.5.0 first; contributions alongside on their own branch.
  - **D71 (2026-11-13):** their own release right after 1.5.0; rework from 1.5.0.
  - **A18 (2026-10-28, on PXReprise's branch):** the server keeps every session itself, public by default ("this is a public repo. no
    question is private"), and tells every client so.

## Scope

**In:** the contribution store and its build tables (A1-A4, A9-A12), the operator's inbox and `accept`/`reject` (A15), the save tool
under an opt-in flag, `contribute save|list|inbox|accept|reject|verify|show`, discovery in `describe` and `--show-prior` (S9), and
the public session record, redone.

**Out:** `datarepo-host` (S12) and anything served over HTTP. No host for now (D57); built last, under PXR-R39's conditions, when the
user says.

## What changes from PXReprise's branch, finding by finding (097)

| # | finding | the rework |
|---|---|---|
| 1 | the store could be written through the read-only server | **fixed in 1.4.4** (G128). The rework only re-runs that release's write probes against the new tools. |
| 2 | an anonymous HTTP client skipped the inbox | no HTTP in this release. A save only ever reaches the inbox; only the operator's `accept` writes `_contributions/`. Tested. |
| 3 | `observed` and `reproduced` certified nothing | **The narrow meanings, in code and in every description.** `observed`: this query ran in a recorded session and returned rows with this hash. `reproduced`: running this query again on that catalog returns the same rows hash. Neither says the result follows. A cited call must be one the server recorded, in the session that saves; `SELECT 1` cites nothing about data. `stated_by: operator` from a client is refused. A judgement is never `reproduced` (A17). `max_rows` and CRLF no longer break a genuine query. |
| 4 | one host record per call | gone with the host; stdio keeps one record per MCP session, and the test holds two calls in one session to one session id. |
| 5 | "unchanged" was false; the one-file catalog could not serve | **The session record leaves the catalog id** (097's proposal): it is served as a view over the record files, like the store's other companions, so a served store rebuilds as `unchanged`. A one-file catalog serves without a record folder. |
| 6 | one bad value stopped everything | non-finite numbers and wrong types refused at save, naming the field; `inbox`, `accept` and `build` check each file alone, name the one that is bad and go on with the rest. |
| 7 | the host had no limits | out of scope with the host. Saves get size limits (a record line, a submission). |
| 8 | A13 and A14 were not guarantees | A13: the release guard records the carried ids on every `--release` build, also on an existing id, and the chain check compares against the recorded head, so dropping or editing released lines fails the build. A14: see the open item below. |
| 9 | a recording failure lost the answer | a failed record line never loses an answer: the answer goes back with `recorded: false`, and the failure is named. |
| 10 | a person's name went into the public record | no person is kept in the session record. D57: the AI fills nothing in, so `submitted_by` is not asked of the client; the accountable person is the operator who accepts, recorded by `accept` from the operator's own command. |

## Slices, in order

| slice | what | test first | state |
|---|---|---|---|
| V1 | port A1-A4 (submission, id, save, basis check) from the branch onto 1.5.0; non-finite numbers and wrong types refused (6) | the branch's `ContributionSubmissionTests` and `ContributionStoreTests`, plus 6's cases | **done** (`ea539c8`, `2dbe460`) |
| V2 | build tables (A9-A12), every file checked alone (6); the guard (A13) on every `--release` (8) | the branch's carry-forward tests, plus 8's drop and edit cases | **done** (`647a2b7`) |
| V3 | the session record redone: per MCP session, outside the catalog id, no person, a failed line never loses the answer (5, 9, 10) | 5's `unchanged` rebuild; 9 simulated; 10's notice | **done** (below) |
| V4 | the save tool and the inbox: cited calls copied from the record, narrow meanings, `accept` records the operator (2, 3, 10) | 3's forged cases all refused; `max_rows`, CRLF | **done** (below); `max_rows` is V5's, in `verify` |
| V5 | `verify`, `show`, discovery (S9, S11) | a judgement never reproduced; a missing catalog reported |
| V6 | docs (`docs/mcp.md`, `docs/cli.md`, a contributions page), CHANGELOG, a scratch run on a copy of aging's catalog | a stranger agent saves, the operator accepts, the next catalog serves it |

## How V3 keeps the record (2026-11-13)

- **Written** by `datarepo mcp` itself, one file per MCP session, `<store>/_sessions/<date>/<id>.jsonl`, a hash chain, as
  PXReprise built it. A folder catalog's server writes beside the bundles of the store it reads; `--sessions <folder>` names
  another place; a one-file catalog names no store, so it serves with no record and says so on stderr.
- **A record that cannot be written never loses an answer** (9): the answer goes back with `session_call.recorded = false` and
  the reason, and a server whose record cannot be opened at all still serves, unrecorded, and says why.
- **Served** by two views, `sessions` and `session_calls`, over the record files, read when queried. They are not in the
  catalog id (5). One constant line, `sessions/views`, enters the id from the store's first record on, since DuckDB refuses a
  file pattern that matches nothing: the catalog that first shows sessions is a new one, and every later session leaves the id
  alone, so a served store rebuilds as `unchanged`. Measured on DuckDB 1.5.5: an empty pattern is an error in every form tried
  (a list, a macro, a subquery), and a half-written last line reads as a null row, which the views leave out.
- **Held** by a release (8): `--release` records each session's id, line count and last hash in `catalog_meta.notes.sessions`,
  and every later build in that folder refuses a record that no longer holds those lines, whether edited, re-chained or removed.
  A session recorded after the release is free.
- **No person** (10): the record holds the client application as the client reported it, never a model or a person; the save
  tool (V4) takes no name.

## How V4 takes a result (2026-11-13)

- **`datarepo mcp --contributions <inbox>`** lists a fourth tool, `datarepo_save_result`, and only then; a server that takes
  results must keep a record, since a result cites its queries from it. The result goes to the inbox, never the store (2).
- **The tool takes no person** (10): `submitted_by` is refused, and withheld from the record even on a refused call. The
  person accountable is the operator who accepts (D57); `contribute accept --by NAME` records a name only if given, and
  `accepted_utc` always. Neither is hashed, so accepting moves no id.
- **It passes on only what its client states** (3): `model.stated_by` must be `client`, `client` is taken from the
  connection, and a query is observed only when the tool copies it from this session's record. `observed` is described
  everywhere as "this query ran on that catalog and returned rows with that hash", never as support for the result.
- **`accept`** checks each observed query against the record on disk again, comparing SQL with line ends made LF (3: a CRLF
  query was refused). `datarepo contribute save|list|inbox|accept|reject`; `inbox` names unreadable files with the reason.

## Open for the user (asked when we reach it, one at a time)

1. **A result's basis after its bundles are deleted** (finding 8, A14). After the 1.5.0 swap the old bundles are removed, so a result
   computed on 1.4.5 data can be read but not re-verified. Proposed: `verify` says "basis no longer in the store", distinct from
   "differs", and `datarepo contribute pins` lists the bundles results rest on, so the operator sees them before deleting. Keeping
   such bundles is the operator's call.
2. **The grant wording** (the branch's open item 1): "reproduced exactly" holds for query and code results, not a model's judgement.
   The PIs write the prose.
