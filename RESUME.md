# RESUME

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**dataRepo** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-19 &middot; rendered 2026-11-23

| | |
|---|---|
| Commits | 1057 |
| Sync | [`smith-chem-wisc/dataRepo`](https://github.com/smith-chem-wisc/dataRepo) |
| Locked decisions | 78 |
| Open gaps | 153 |
| Gate items skipped | 5 |

**Worktrees** -- details in `code/PINNED.md`

| Worktree | Branch | HEAD | Pin | Status |
|---|---|---|---|---|
| `code/_wt_ptmqtl` | feat/ptmqtl-engine | `ec584c73` | `ec584c73` | at pin |
| `code/_wt_141` | feat/1.4.1 | `e41c4af8` | `e41c4af` | at pin |
| `code/_wt_tmt` | feat/tmt | `9e18c4dc` | `9e18c4d` | at pin |
| `code/_wt_142` | feat/1.4.2 | `3447228b` | `3447228` | at pin |
| `code/_wt_150` | feat/1.5.0 | `91901d0a` | `91901d0` | at pin |
| `code/_wt_ai` | feat/ai-contributions-v2 | `e5918297` | `e591829` | at pin |
| `code/_wt_ai_contrib` | feat/ai-contributions | `1db8a535` | `1db8a535` | at pin |
| `code/_wt_mzlib_sumo` | fix/sumo-remnant-target-lysine | `6974a4d4` | `6974a4d4` | at pin |

> **`CLAUDE.md` is 59 KB, over its 25 KB budget** (it loads into every session). Keep standing rules and traps; move dated status entries word for word to `.project/status-log_<from>_to_<to>.md` (close-the-chat, step 5).

<!-- END GENERATED -->


## Goal

Build an AI-ready, API-accessible repository for the results of the `aging` pipeline's PRIDE
reanalyses. The results cover search, quant, provenance, design and organelle annotation. Humans can
use it, but AI agents are the main users. The question it serves is how organelle proteomes change
with age.

## Where it stands (2026-11-23)

- **dataRepo's code lives in smith-chem-wisc/PXReprise** (since #4, 2026-11-13; G136). This repository is the project's record:
  design, threads, results, `.project`, and the frozen Python.
  - Code work happens in `E:\GitClones\PXReprise-dataRepo`, one `datarepo/<topic>` branch from `upstream/master` per change,
    with a PR to smith on board #16 (`code/PINNED.md`).
  - smith master is `0cbd6c1` (#55's merge, 2026-11-23); CI is green. **No datarepo PR is open.**
- **One release for the engine and datarepo (D73, D74).** The first joint release is **PXReprise 1.0.0**, not yet out.
  - The latest released datarepo is still v1.4.5; 1.5.0 was never released.
  - Schema 0.0.17 and catalog format 17 are unreleased working versions (`schemas/datarepo/releases/README.md`), so an
    addition before the release does not bump them. Master's ingest path is `cs-1.5.0`.
  - aging adopts when it chooses, at about 7.5 h of re-ingest (our 129). Releasing is the user's word.
- **Merged since the 2026-11-20 close, all Shipped on board #16:**
  - #42, PEP-trained decided per search (G148);
  - #47, the seam test (G139 (a));
  - #48, missing search databases or settings are findings (cs-1.4.0; G152, G153);
  - #53, the tutorial names v1.0.0 and can be followed from source until then (G139 (b));
  - #54, R81 (**D78, reversing D55**): a bundle's 1% rule is the search's own identification filter, on the predicate ptmQtl's
    S7 shares (cs-1.5.0). On 215 served bundles, served 1% peptidoforms do not move; S7's target PSMs go 129.3 M -> 105.3 M.
  - ptmQtl's #50 (S7 on that predicate) and #55 (type A is DEF-PTM-PAIR v3; ptmQtl 074).
- **Schema 1.0.0 is planned (PXReprise D78, our 129) as six PRs, A to F; none has a branch.**
  - D waits on the user's rulings on #24 (U41) and #25 (U42). Both are open; #25's last comment is from 2026-11-23.
  - Partner comments reach the issues through PXReprise's session: we write a `## Comment for #N` section in our PXReprise
    thread, and they post it word for word.
- **Owed by us:**
  - **G144:** aging's DATAREPO-91 table, with ptmQtl's v3 engines timed. It is unblocked by #55. `PtmQtlBundle.Read` takes 0.0.17
    bundles only, so time it on scratch bundles ingested by master's datarepo (G145). Send it to aging, and to #25 through PXReprise.
  - **G139:** the release commit's three tutorial edits: remove the pre-release note, rerun the two ids, set the ingest path to
    `cs-1.5.0`. They go as a PR on PXReprise's release branch when PXReprise says it exists (their G127).
  - G149 (the 1% definitions' v2 under option A), G151 (measure both notch clauses on every served search), G143, G147.
  - `datarepo/go-cross-file-tests` (G146's follow-up), G137's five holes then porting `feat/ai-contributions-v2`, and G141.
- **Waiting on others:**
  - **G155, PXReprise's:** `datarepo-binaries` fails on osx-arm64 on every master push since #43. The engine's Microsoft.ML
    supports x64 and x86 only, and `release.yml` uses the same build, so 1.0.0's release would stop there. Told in our 155.
  - G150 (the differential layer) waits on PXR-R79's real output, due about 11-28.
  - ptmQtl: site-trait v2, and whether S7 reads `datasets.confidence_rule` (theirs).
  - go GO-D14, pep DATAREPO-89, pyMzLib DATAREPO-70.
  - U43: bridge's query package (default: published from PXReprise after 1.0.0).
- **Held by the user, do not re-raise:** U32 (keeping the databases, no default), U37 and PXR-R55 (with Alex), U38.
- **For the user, whose call deleting is:** these checkouts are merged and can go.
  - `code/_wt_ptmqtl`: its `nuget.config` names `E:\x\feed`, which PXReprise's cleanup deleted on 2026-11-23.
  - `code/_wt_141`, `_wt_142` and `_wt_tmt` (released). `_wt_150` waits until 1.0.0 is out (PINNED).
  - `E:\GitClones\PXReprise-dataRepo-tut`.

  Command: `git -C E:\CodeReview\dataRepo worktree remove code/<name>`.
- **Pick up at:**
  1. Run `threads.py inbox` (ptmQtl 074 and PXReprise 154 are read; our last is PXReprise 155).
  2. Check G155 with `gh run list --repo smith-chem-wisc/PXReprise --workflow datarepo-binaries.yml --limit 3`, and read
     PXReprise's reply to our 155.
  3. **G144:** ingest aging's largest deposit by MS2 count with master's datarepo into a scratch store (0.0.17). Time ptmQtl's
     v3 engines on it, and on the pooled scope. Then send aging the table, and send PXReprise a `## Comment for #25`.
  4. Then G149 and PR A of the schema 1.0.0 plan. Check #24 and #25 for rulings:
     `gh api repos/smith-chem-wisc/PXReprise/issues/25/comments --jq '.[] | "\(.id) \(.user.login) \(.created_at)"'`.
  5. When PXReprise names 1.0.0's release branch, do G139's three tutorial edits as a PR on it.


## Design documents

- `design/OPEN_QUESTIONS.md`: every question for the user, with its default (D7). U39 and U40 were answered by D74; U41 and U42 are smith #24 and #25.
- `design/CHARTER.md`: who defines, runs, stores and consumes what. Draft v0.8, not in force until every project signs.
- `design/FRAMEWORK.md`: the framework's steps. Ingest and build are locked (D9, D10); the rest are proposals.
- `design/CSHARP_PORT.md`: the C# port (D41), done. The Python stays frozen at 0.32.0 in this repository.
- `design/INPUT_INVENTORY.md`: what dataRepo must ingest from the aging pipeline's outputs (the 2026-09-19 survey).
- `design/SCHEMA_V0.md` and `design/SCHEMA_COVERAGE.md`: schema v0, and aging's benchmark questions mapped against it
  (2026-09-19).
- `design/RUNNER.md`: how an operator runs a released engine on stored data (G64, D28).
- `design/PTMQTL_ENGINE.md`: the ptmQtl engines in `datarepo run`, released in 1.4.0.
- `design/PUBLIC_DATA.md`: dataRepo's part of the public-data contract (D48). Steps 1 and 2 were released as 1.3.5 and 1.3.6.
- `design/RELEASE_1.4.1.md`: 1.4.1's contents (released 2026-11-01).
- `design/RELEASE_1.5.0.md`: 1.5.0's build list and release-day steps. Its content now ships as PXReprise 1.0.0 (D74), so the
  release-day steps are history.
- `design/NOTE_FROM_CodeReview_2026-10-06_dq2-talk-directly.md` and
  `design/NOTE_FROM_USER_2026-10-21_github-actions-minutes.md`: two notes from the user (settle DATAREPO-Q2 directly with sdrf
  and QuantProject; keep private-repository CI cheap).
- Older status sections, word for word: `.project/status-log_2026-09-19_to_2026-11-17.md`, `.project/status-log_2026-11-17_to_2026-11-19.md`, `.project/status-log_2026-11-19_to_2026-11-20.md` and `.project/status-log_2026-11-20_to_2026-11-23.md`.
