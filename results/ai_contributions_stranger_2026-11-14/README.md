# A stranger agent tests the AI contributions server (2026-11-14)

A subagent given only `docs/mcp.md`, `docs/contributions.md` and a stdio driver (`session.py`), and no source, used and then
attacked the server: the scratch build `1.6.0-scratch.7054ba1` over the catalog folder of a copy of aging's store
(`F:\datarepo_scratch_150\ai_e2e\catalogs`), saves going to `F:\datarepo_scratch_150\stranger\inbox`. 21 runs; its call files
and answers are in `F:\datarepo_scratch_150\stranger\runs\` (scratch, not kept here). What follows is the agent's report,
condensed; **only finding 2 (the NUL byte) was re-checked by us**, against its `r18_nul_observed.json.out.json`.

## Its honest result

`79feabaf54a0bd4d`: of 136 datasets with aging-organelle-map v1 annotation and at least 500 target protein groups at 1%, the
median share of groups whose every member carries a mitochondrion-category GO-CC term is 0.188 (0.079 to 0.644); the top is
PXD018545 (0.644), and 10 of the top 12 are heart or skeletal-muscle deposits. 3 observed queries.

## What it broke (to fix before release)

1. **A person reaches the public record (promise a).** A refused save is recorded with only `contribution.submitted_by`
   withheld; `submitted_by_orcid`, `accepted_by`, `client.name` and a top-level `submitted_by` stay verbatim. The client's
   `clientInfo.name` is recorded as sent (`--client "Jane Q. Doe"` became `sessions.client_name`). Free-text names in title,
   summary, items and `model.provider`/`model.id` are accepted (no server can police free text; say so).
2. **A NUL byte makes an observed query lie (promise b).** DuckDB runs the text before a NUL; the record and the observed copy
   keep the whole text. `SELECT 42 AS n\x00 FROM no_such_table` returned `[[42]]` (re-checked). A query recorded as a join over
   `protein_localizations` ran `SELECT 0.0`; a false result citing it was taken with `observed_queries: 1` (`14cd02ad29f7e5e4`).
   The only sign was `tables_touched: []`, which `contribution_queries` does not keep. Fix: refuse a query holding NUL (or any C0
   control but tab and line ends) before it runs, in `datarepo_sql` and `datarepo_search`.
3. **A call that fails at the JSON-RPC level is not recorded** (a lone surrogate, -32603; 500-deep nesting, -32700): no line,
   no seq, no `session_call`. A client counting its own calls then cites the wrong one (`a4f29478a5d0d98e`). Clients should cite
   the `session_call.seq` each answer returns, not a count; the docs and the driver must say so, and the record's "every call"
   must say "every call that reaches a tool".
4. **A bare `NaN` token closed the connection** and lost the session (the call is not in the record). The server should answer
   a malformed request with a JSON-RPC error and keep serving.
5. **No length limit on `summary`** (a 1,000,000-character one was accepted; its record line is 1 MB) or on other free text
   but `title`. Finding 7 asked for limits on saves.

## Smaller

- Refusals come back with `isError: false` (by design since the Python server: an error is a result an agent can act on), but
  the docs never say so.
- An error about a stated query names it by its place after the observed ones are prepended ("`method.queries[1]`" for the first).
- `rank` of 10^30 is refused as "not a whole number" (it is one, but not a long).
- The contribution tables have no column descriptions in `describe` (`one_row_is` null).
- `contributions.path` shows the operator's local path in a public table.
- The save's argument shape is in neither doc; the agent learned it from errors.
- Row counts of the live `sessions`/`session_calls` lag in `describe` and `tables_touched` (cached at first read).
- `protein_groups.protein_group_id` (`PXD:acc;acc`) and `protein_localizations.protein_group` (`acc|acc`) join only by
  `array_to_string(protein_accessions, '|')`; nothing says so.

## What held

Forged `observed: true` (from another session or with a wrong hash), seq 0, 99, the save's own and a non-SQL or refused call
were all refused; nothing reached the store without the operator (a retraction and a supersession of another's result went to
the inbox only); SQL that writes, attaches or reads files was refused; a fake or unheld basis was refused; `stated_by` other than
`client` and a `client` object were refused; no server wording claims a result is proven or reproduced. One bad save did not
stop later sessions.

## The inbox it left

Accept only `79feabaf54a0bd4d`, if anything; every other request's title starts "[adversarial test]": `60862e01342f43b0`
`86c40b9f5929a65f` `97e28e253b85ca30` (a fictitious person) `92fe8b7801ece39b` `50ad5fb460e50514` `c05a7c397bf5e49a`
`d2833b21d7376ae7` `7bd639c855ef62e2` `ce6cc44ee6213237` `4f07302e40a476a7` `f1135ec06845457a` `96f0c89657fbdf5c`
`274059cf59c36fc2` `4dab3ee910cdb84e` (1 MB summary) `a4f29478a5d0d98e` `993473bfafc36967` `14cd02ad29f7e5e4` (false claim)
`fa3089b5ab1542c1` (retraction of `7e65324a72c36f5d`). All scratch.
