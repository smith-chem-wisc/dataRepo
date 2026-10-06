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
