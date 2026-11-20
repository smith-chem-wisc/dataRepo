# RESUME

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**dataRepo** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-19 &middot; rendered 2026-11-19

| | |
|---|---|
| Commits | 1008 |
| Sync | [`smith-chem-wisc/dataRepo`](https://github.com/smith-chem-wisc/dataRepo) |
| Locked decisions | 75 |
| Open gaps | 141 |
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

> **`CLAUDE.md` is 58 KB, over its 25 KB budget** (it loads into every session). Keep standing rules and traps; move dated status entries word for word to `.project/status-log_<from>_to_<to>.md` (close-the-chat, step 5).

<!-- END GENERATED -->


## Goal

Build an AI-ready, API-accessible repository for the results of the `aging` pipeline's PRIDE
reanalyses. The results cover search, quant, provenance, design and organelle annotation. Humans can
use it, but AI agents are the main users. The question it serves is how organelle proteomes change
with age.

## Where it stands (2026-11-19)

- **dataRepo's code lives in smith-chem-wisc/PXReprise** (since #4, 2026-11-13; G136). This repository is the project's record:
  design, threads, results, `.project`, and the frozen Python. Code work happens in `E:\GitClones\PXReprise-dataRepo`, one
  `datarepo/<topic>` branch from `upstream/master` per change, a PR to smith, on board #16 (`code/PINNED.md`). smith master is
  `65b081f` (#17 to #23 merged 2026-11-18).
- **One release for the engine and datarepo (D73, D74).** The first joint release is **PXReprise 1.0.0**. datarepo has no
  version of its own (1.4.5 was its last; 1.5.0's content ships in 1.0.0). aging adopts when it chooses, at about 7.5 h of
  re-ingest (our 129). Every release opens with an `**Adopting:**` line. Releasing is the user's word.
- **Schema 1.0.0 is planned (PXReprise D78, our 129) as six PRs:**
  - A: R5's schema diff;
  - B: retire the Python parity shims;
  - C: SF4's catalog layer;
  - D: schema 1.0.0 itself (R3, R2, bundle-id algorithm v2, the sharing key, ingest path `cs-2.0.0`);
  - E: R4, a catalog takes every bundle of its major up to its own minor;
  - F: a whole-store scratch re-ingest to measure adoption.

  A to C by about 11-25, D and E by about 12-04, F by about 12-08. **D waits on** #24, #25 and PXR-R70 (PXReprise's: the search
  profile as a recorded field). One shared store (PXReprise D79) supersedes U36.
- **Two public issues decide D's shape:**
  - **smith-chem-wisc/PXReprise#24 (U41):** each Parquet file's schema fingerprint. We recommend the column-contract hash. aging
    agrees (B, for stable citations).
  - **smith-chem-wisc/PXReprise#25 (U42):** which tables the core keeps. Comments are in from:
    - Alex: one layer per engine, a `reference` layer, ptmQtl results on request;
    - aging: B, ptmQtl results stored until every method is available and fast;
    - dia: DIA as additions;
    - us, twice (G143, D75).

  ptmQtl's comment waits on the user in PXReprise's session, and the user rules once partners have commented.
- **How partner comments reach the issues:** PXReprise's session collects them. We reply in our PXReprise thread with a
  `## Comment for #N` section, written for a public reader (no private paths, thread numbers or private decision ids), and
  PXReprise posts it word for word under "Project of origin". Ours: 131 is comment 7001405174, and 132 is comment 7001454691.
- **Committed publicly for 1.0.0 (D75, G143):**
  - a new enum value is minor, and a catalog refuses a newer minor;
  - `peptidoform_ions` is renamed `matched_fragment_ions`;
  - `confidence_rule` is reworded;
  - `ptm_pairs`' stale description is fixed.
- **ptmQtl's tables:** everyone agrees they leave the core. Both users of them (aging 141, ptmQtl 068) want results stored
  with their record. ptmQtl asks that no row be stored from the 1.4.0 engines, which compute the October method, not v5.
- **Owed by us:**
  - G144: aging's DATAREPO-91, a table of each ptmQtl method (released at ptmQtl's current version? time on aging's largest
    deposit and pooled). It was also promised on #25.
  - G145: ptmQtl's DATAREPO-P39, moving the engines to v5 before they store a row, and when.
  - G138: QuantProject DATAREPO-D16 (DIA), with dia's #25 comment now in.
  - G137's five holes, then porting `feat/ai-contributions-v2` (G136).
  - G141: D63's item 10.
  - G139: the seam test, when the user says go.
- **Unread at the close:** QuantProject 106 (eight mzLib quant PRs and MetaMorpheus #2980 merged, none released) and 107
  (DATA-DEFINITIONS v3.32, `DEF-TMT-READING`; a missing floor is null, never 0). Neither asks anything.
- **Held by the user, do not re-raise:** U32 (keeping the databases, no default), U37 and PXR-R55 (with Alex), U38.
- **Pick up at:**
  1. Run `threads.py inbox`, and read QuantProject 106 and 107.
  2. Check #24 and #25 for new comments:
     `gh api repos/smith-chem-wisc/PXReprise/issues/25/comments --jq '.[] | "\(.id) \(.user.login) \(.created_at)"'`.
     Alex comments as `Alexander-Sol`. PXReprise posts partners' comments from `trishorts`, so read the "Project of origin"
     line.
  3. Start G144 (DATAREPO-91): build the table from ptmQtl 068 section 3 and 069, mark what our 1.4.0 engines compute (`code/_wt_ptmqtl`,
     `design/PTMQTL_ENGINE.md`), find aging's largest deposit by MS2 count, and answer aging. Then post the table to #25 through
     PXReprise as a `## Comment for #25`.
  4. PR A (R5's `SchemaGen diff`) needs neither ruling. Start it on a `datarepo/` branch from `upstream/master`, classing each
     change by D75's rule.

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
- Older status sections, word for word: `.project/status-log_2026-09-19_to_2026-11-17.md` and `.project/status-log_2026-11-17_to_2026-11-19.md`.
