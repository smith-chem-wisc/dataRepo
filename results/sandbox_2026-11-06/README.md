# The MCP sandbox could write into the store, 2026-11-06 (G128)

**Question:** an independent review of `feat/ai-contributions` reported that a client of a folder catalog can overwrite a
bundle's table through the read-only MCP server, on released 1.4.3. Is that true, how far does it go, and does a fix close the
class?

**How:** the released 1.4.3 binary against a scratch store under the session's scratchpad: one copy of PXD017944
(`3cd52dd1b39472d8`) in a folder catalog, driven over real stdio. **Nothing was run against aging's store through a server.**
`store_dates.py` is the one script that reads `F:`, and it only stats files and opens `bundle.json`. The scripts here are the ones
run. They expect the scratchpad layout of `results/split_trial_2026-11-06/`.

## What 1.4.3 does

| statement a client sends | catalog | what happens |
|---|---|---|
| `EXPLAIN ANALYZE COPY (...) TO '<store>/x'` | folder | writes the file (also `ANALYSE`, `(ANALYZE)`, and with comments between the words) |
| the same, to a served table, in two steps | folder | **replaces the table:** sum of `best_q_value` 2705.861329 -> 1352.930665, same 23,700 rows, same catalog id `07f4750ef2fe5111`, and a rebuild passes all 24 checks |
| `SELECT * FROM enable_profiling(format='json', save_location='<bundle>/bundle.json')` | folder | **overwrites `bundle.json`**: the next `datarepo build` crashes, exit 70, `KeyNotFoundException: bundle_id` |
| `SELECT * FROM enable_logging(storage='file', storage_path='<store>/d')` | folder | writes two CSV files in a folder the client picks; also through `query()` and `EXPLAIN ANALYZE` |
| the same with `storage_config={'path': ..., 'normalize': false}` | folder | writes nothing, and every later query in that session fails until it restarts |
| `EXPLAIN ANALYZE CREATE TEMP TABLE metrics AS SELECT 99999 AS n` | **both** | `SELECT * FROM metrics` answers 99999, and `tables_touched` reads `metrics`, 180 rows on the folder catalog and 540 on the one file (D20) |
| `PRAGMA disable_optimizer`, `enable_verification`, `add_parquet_key` ... | both | run, despite `lock_configuration` |
| `SELECT * FROM json_execute_serialized_sql(...)` | both | runs a statement no parse of the outer text can see into |
| anything naming a path outside the store | folder | refused |
| anything that writes | one file | refused: the local filesystem is disabled |

**The review found the first row.** The temp table, the two table functions and the PRAGMAs came from running every function
DuckDB 1.5.5 lists (`enumerate.py`) after a first fix for `EXPLAIN` alone, which still wrote.

**Since when:** folder catalogs and `allowed_directories` arrived in 1.3.5 (`5afea11`), so the writes hold from there. Read from
the code, not run on any release but 1.4.3.

## Was aging's store touched?

`store_dates.py`, read-only, 2026-11-06: 520 bundles, **0 files dated more than an hour after their bundle**, and no stray file at
store or deposit level. So there is no sign of it, which is not proof: `bundle.json` holds row counts and no table hashes, so a
rewrite within that hour, or one that kept a file's date, would not show. It did not look under `_engine`, `_study` or `derived`.

## The fix (branch `feat/1.4.4`)

- **An `EXPLAIN` takes one `SELECT`,** and DuckDB's own parser reads the wrapped text. Option lists and `VERBOSE` are refused,
  not parsed.
- **Allow-lists:** `Sandbox.ReadingTableFunctions` and `ReadingPragmas`. What is not on them is refused. `write_log` is refused.
- **`query()`'s text is checked as a statement of its own,** so it must be one plain string.
- **A statement that cannot be read is refused.** `json_serialize_sql` reports its failures as a document, not an error, so a
  walk over that document would have found nothing to object to.
- **`EveryCallableDuckDbOffersIsADecision`** fails on any function a DuckDB upgrade adds until somebody classifies it.

| run | result |
|---|---|
| new tests on the unfixed code | 23 of 37 fail (before the allow-list tests existed) |
| every probe here on the fixed binary | no statement that writes or changes the session answers; the store's files are unchanged |
| every reading form in `WhatReadsIsAnswered`, and the parity tests against 0.32.0 | pass |
| the whole suite, without RealData, on Windows | 776 passed, 0 failed, 1 skipped. Linux and macOS have not run it, because the branch is not pushed |

## Not closed by this

- **`read_*` and `glob` still read anything under the store,** as designed in 1.3.5.
- **The scalars and macros were read by name** (616 and 118), not proven. Only table functions and PRAGMAs are forced decisions.
- **This is still not a public endpoint's sandbox.** `docs/mcp.md` keeps that as stage two, and `datarepo-host` on
  `feat/ai-contributions` would serve this with no stage two.
