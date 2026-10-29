# Code pins — dataRepo

Worktrees under `code/` are **gitignored**; this file is their record. Pin repo · branch · commit
whenever a worktree is created or advanced.

| repo | worktree | branch | base clone | pinned commit |
|---|---|---|---|---|
| mzLib | `code/mzLib_prE_peaks` | `fix/quantified-peaks-optional-mbr-score` (pushed to `origin` = trishorts/mzLib) | `E:\GitClones\mzLib`, off `upstream/master` 588c2249 | `88610382` — PR E (review fixes on 2026-09-23; first push `ce7578c9`), [smith-chem-wisc/mzLib#1345](https://github.com/smith-chem-wisc/mzLib/pull/1345) |
| mzLib | `code/mzLib_prD_proforma` | `fix/psmtsv-proforma-from-full-sequence` (pushed to `origin` = trishorts/mzLib) | `E:\GitClones\mzLib`, off `upstream/master` 588c2249 | `ebdfa790` — PR D (review fixes on 2026-09-23; first push `7562d4bc`), [smith-chem-wisc/mzLib#1346](https://github.com/smith-chem-wisc/mzLib/pull/1346) |

**Both PRs MERGED into smith-chem-wisc/mzLib master on 2026-09-24 (~00:11 UTC for E, ~00:22 UTC for D),
approved.** The maintainer merged master into each branch first (E head `149c5173`, D head
`163925fd`), so each worktree shows "behind" its remote; nothing of ours is unpushed. Both worktrees
can be retired. No mzLib release carries either yet (1.0.591 is latest).

**Retired 2026-09-24.** Both worktrees were removed (`git worktree remove`, clean, nothing unpushed)
after the PRs shipped in **mzLib 1.0.592** / pyMzLib 0.2.0. The branches remain on `origin`
(trishorts/mzLib). No worktree is active.

## Active since 2026-10-06

| repo | worktree | branch | base clone | pinned commit |
|---|---|---|---|---|
| dataRepo | `code/_wt_ptmqtl` | `feat/ptmqtl-engine` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` 7d47d64 | `ec584c73be1e962d96537bac74cede50ae712cac`: the ptmQtl engines (G88, D44); no PR yet |
| dataRepo | `code/_wt_140_ingest` | `feat/1.4.0-ingest` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` | `0c1f8d0aeb281dde98a8668088892874febd4001`: 1.4.0's ingest side (G103), pushed. The scratch re-ingest binary was built from `54453e1`; `0c1f8d0` adds DATAREPO-84, DATAREPO-D7 and ptmQtl's S2c v3 and S2e. Held by datarepo-9b, which also holds the threads since 2026-10-20. No PR yet: it merges at release. **Merged 2026-10-28 as `88f26b0` and released as 1.4.0**: the worktree can be retired |
| dataRepo | `code/_wt_ai_contrib` | `feat/ai-contributions` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` | `1db8a53584a361346930af98bd473f338319ef85`: built by PXReprise for our review (PXReprise 064, PXR-R37..R39, unanswered); not merged |
| mzLib | `code/_wt_mzlib_sumo` | `fix/sumo-remnant-target-lysine` (pushed to `origin` = trishorts/mzLib) | `E:\GitClones\mzLib`, off `smith/master` b1e925ff9 | `6974a4d4cede89b84a1409411593e391ecbd252a`: [smith-chem-wisc/mzLib#1432](https://github.com/smith-chem-wisc/mzLib/pull/1432), closes #1431 |

**`feat/ptmqtl-engine` merges only after an mzLib release carries #1430.**
- The branch builds against mzLib packed from #1430's branch: version `1.0.595-pr1430.b2d218d`, in the local feed
  `E:\x\feed`, built in the worktree `E:\x\pr1430` (a worktree of `E:\GitClones\mzLib`). That source is named by
  `dotnet/nuget.config`, which exists on this branch only.
- At merge: delete that file, point at the released mzLib, and bump the ingest path (#1403's ProForma change rides
  along).
- Twelve test failures on the branch are mzLib-version effects, not engine defects. The steps are G88.

**`fix/sumo-remnant-target-lysine` is PR #1432**: `ready for review`, `ready-for-agent`, six referees, on board #16 as
In review. When it merges, move the board item to Shipped and remove the worktree. The MetaMorpheus follow-up (two
MetaDraw settings XMLs still name `... on D`) waits on an mzLib release that carries it.
