# RESUME

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**dataRepo** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-19 &middot; rendered 2026-11-17

| | |
|---|---|
| Commits | 987 |
| Sync | [`smith-chem-wisc/dataRepo`](https://github.com/smith-chem-wisc/dataRepo) |
| Locked decisions | 74 |
| Open gaps | 138 |
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

> **`CLAUDE.md` is 57 KB, over its 25 KB budget** (it loads into every session). Keep standing rules and traps; move dated status entries word for word to `.project/status-log_<from>_to_<to>.md` (close-the-chat, step 5).

<!-- END GENERATED -->


## Goal

Build an AI-ready, API-accessible repository for the results of the `aging` pipeline's PRIDE
reanalyses. The results cover search, quant, provenance, design and organelle annotation. Humans can
use it, but AI agents are the main users. The question it serves is how organelle proteomes change
with age.

## Where it stands (2026-11-17)

- **dataRepo's code lives in smith-chem-wisc/PXReprise** (since #4, 2026-11-13; G136). This repository is the project's record:
  design, threads, results, `.project`, and the frozen Python. Code work happens in `E:\GitClones\PXReprise-dataRepo`, one
  `datarepo/<topic>` branch from `upstream/master` per change, a PR to smith, on board #16 (`code/PINNED.md`). The first two
  were merged by the user on 2026-11-17: #14 (hello world, PXR-R64) and #16 (the catalog's `split_reason` descriptions read the
  manifest's list, so `tissue` is named; PXR-R66).
- **One release for the engine and datarepo (D73, D74).** The user: no drift, and changes must work in both directions.
  - The first joint release is **PXReprise 1.0.0**. datarepo has no version of its own any more: 1.4.5 was its last, and
    **1.5.0 is never released under that name**. Its content is all on PXReprise master (checked commit by commit, PXR-R65) and
    ships in 1.0.0.
  - Releases are cut when ready and never held for aging. **aging adopts when it chooses** and pays the re-ingest then. That
    replaces the 1.5.0 swap announced in our 116.
  - Every release opens with an `**Adopting:**` line. The engine's last release of its own is 0.4.50 (2026-11-17).
- **The pins agreed with PXReprise (their 122):**
  - (a) a test across the seam on every PR: ours (G139);
  - (b) the engine refuses a datarepo built from another release: theirs;
  - (c) the Adopting line: theirs.

  Nobody builds them until the user says go. Why they are needed: no test crosses the seam today, and the two programs have
  already drifted (engine 0.4.48 writes `split_reason: tissue`, which production datarepo 1.4.5 refuses).
- **Owed by us:**
  - PXR-R68 (2), our figure for what adopting 1.0.0 costs aging. Theirs is 5 to 6 h; ours, from 1.5.0's measurement, is about
    9 h for 273 deposits. Also (3), everything in datarepo that reads its own version (G140).
  - DIA: QuantProject DATAREPO-D16 and dia DATAREPO-Q2..Q5 take one answer, after reading PXReprise's decision record 0072
    (G138).
  - G137's five holes, then porting `feat/ai-contributions-v2` (G136).
- **Answers in, waiting on us:** sdrf 039 (SDRF-D14, D15) and pride 008 (PRIDE-D1) unblock D63's item 10 and the SDRF
  discussion with the user (U30; G141).
- **Held by the user, do not re-raise:** U32 (keeping the databases, no default), U36 and U37 (with Alex), U38.
- **Pick up at:**
  1. Run `threads.py inbox`.
  2. Answer PXReprise's PXR-R68 (2) and (3) (G140):
     - count the deposits in `F:\aging_data\repo\store`;
     - correct the 1.0.0 cost from `results/reingest_150_2026-11-12/` (on branch `feat/1.5.0`);
     - list each reader of `BundleWriter.PackageVersion` under `E:\GitClones\PXReprise-dataRepo\src`, with what it reads from
       now on.

## Design documents

- `design/OPEN_QUESTIONS.md`: every question for the user, with its default (D7). U39 and U40 were answered by D74.
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
- Older status sections, word for word: `.project/status-log_2026-09-19_to_2026-11-17.md`.
