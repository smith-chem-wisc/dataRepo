# RESUME

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**dataRepo** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-19 &middot; rendered 2026-11-21

| | |
|---|---|
| Commits | 1023 |
| Sync | [`smith-chem-wisc/dataRepo`](https://github.com/smith-chem-wisc/dataRepo) |
| Locked decisions | 77 |
| Open gaps | 148 |
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

## Where it stands (2026-11-20)

- **dataRepo's code lives in smith-chem-wisc/PXReprise** (since #4, 2026-11-13; G136). This repository is the project's record:
  design, threads, results, `.project`, and the frozen Python. Code work happens in `E:\GitClones\PXReprise-dataRepo`, one
  `datarepo/<topic>` branch from `upstream/master` per change, a PR to smith, on board #16 (`code/PINNED.md`). smith master is
  `4fb0c4c` (#27's merge, 2026-11-20).
- **One release for the engine and datarepo (D73, D74).** The first joint release is **PXReprise 1.0.0**. datarepo has no
  version of its own; 1.5.0's content, now including #26 and #27, ships in 1.0.0. aging adopts when it chooses, at about 7.5 h
  of re-ingest (our 129). Every release opens with an `**Adopting:**` line. Releasing is the user's word.
- **Schema 1.0.0 is planned (PXReprise D78, our 129) as six PRs.** None has a branch yet.
  - A: R5's schema diff;
  - B: retire the Python parity shims;
  - C: SF4's catalog layer;
  - D: schema 1.0.0 itself (R3, R2, bundle-id algorithm v2, the sharing key, ingest path `cs-2.0.0`);
  - E: R4, a catalog takes every bundle of its major up to its own minor;
  - F: a whole-store scratch re-ingest to measure adoption.

  A to C by about 11-25, D and E by about 12-04, F by about 12-08. **D waits on** #24, #25 and PXR-R70 (PXReprise's, by about
  12-01: the search profile as a recorded field).
- **Two public issues decide D's shape, and the user rules on both:** #24 (U41, each Parquet file's schema fingerprint; we
  recommend the column-contract hash) and #25 (U42, which tables the core keeps; we recommend B as amended in our comment
  7001405174). Partner comments reach the issues through PXReprise's session: we write a `## Comment for #N` section in our
  PXReprise thread, for a public reader, and they post it word for word.
- **Reference data has moved into the catalog, built by PXReprise (2026-11-19 to 11-20):**
  - **#26, orthology:** merged (`3367d02`). Our 136 (PXR-R72) placed it: the snapshot copies go in logs' layer, the bridge
    in the catalog's, and the format does not change (D76).
  - **#27, GO:** merged (`4fb0c4c`) before we answered PXR-R73. It keys GO **per database file**, with isoform inheritance
    done in the catalog. That stands against D50 and our 131, which keyed GO by target set. Our answer decides any follow-up PR.
  - **#29, the accession index `protein_peptidoforms`:** draft, built as 136 said. It takes **255 MB** in the catalog file,
    not the 108 MB our Parquet measurement gave. PXR-R74 asks whether that is acceptable.
  - **#31, Reactome:** open and out of draft. It is our G112, built on #27's per-file pattern. PXR-R75 asks us to review
    its shape.
  - kegg 010: their mzLib PR-1 to PR-4 are in 1.0.598.
- **Owed by us:**
  - **G146: PXR-R73, R74 and R75**, the three above.
  - G144: aging's DATAREPO-91, a table of each ptmQtl method (released at ptmQtl's current version? time on aging's largest
    deposit and pooled). It was also promised on #25.
  - G145: ptmQtl's DATAREPO-P39, moving the engines to v5 before they store a row, and when.
  - G138: QuantProject DATAREPO-D16, and dia's DATAREPO-Q2 to Q5 (DIA).
  - G143: the 1.0.0 work our #25 comments committed to. Its target-set clause for GO waits on PXR-R73.
  - G147: protein sequences (136 §4), after #29.
  - G137's five holes, then porting `feat/ai-contributions-v2`; G141; G139 when the user says go.
- **In flight:** smith #28 (Alex's `datarepo-host`, approved by PXReprise), #29 and #31. Check them with
  `gh pr view <n> --repo smith-chem-wisc/PXReprise`. The #24 and #25 rulings are still to come.
- **Held by the user, do not re-raise:** U32 (keeping the databases, no default), U37 and PXR-R55 (with Alex), U38.
- **2026-11-21 (mid-session; the next close replaces this section):** our PXReprise 145 answered PXR-R73 to R78 and asked
  PXR-R79 and R80.
  - D77: GO is keyed per file, measured equivalent to `GoGroupAnnotator`.
  - The user said no to smith #28, #29 and #31 (PXReprise D84), which closed R74.
  - The user's go on PXReprise's G112 (one joint release) is in PXReprise's `9fdb277`. Our part is G139: the seam test
    and the tutorial.
- **Pick up at:**
  1. Run `threads.py inbox`.
  2. **G148 first:** the #38 follow-up PR `datarepo/pep-filter-per-search`. It decides PEP-trained per search, and keeps
     the resolved-notch clause to 1.1.14 only. It must land before PXReprise's 1.1.15 pin swap.
  3. **G139 (a):** the seam test, on `datarepo/seam-test`. G139 (b), the tutorial, waits on PXReprise's workflow PR naming
     the tag and the asset names.
  4. Then `datarepo/go-cross-file-tests` (G146's follow-up), and G149's three read-by-id fixes. G150, the differential
     layer, waits on PXR-R79's real output (about 11-28).
  5. Then G144 (DATAREPO-91) and PR A, as before. Check #24 and #25 for new comments:
     `gh api repos/smith-chem-wisc/PXReprise/issues/25/comments --jq '.[] | "\(.id) \(.user.login) \(.created_at)"'`.


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
- Older status sections, word for word: `.project/status-log_2026-09-19_to_2026-11-17.md`, `.project/status-log_2026-11-17_to_2026-11-19.md` and `.project/status-log_2026-11-19_to_2026-11-20.md`.
