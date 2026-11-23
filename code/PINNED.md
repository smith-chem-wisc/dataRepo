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
| dataRepo | `code/_wt_ptmqtl` | `feat/ptmqtl-engine` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` 7d47d64 | `ec584c73be1e962d96537bac74cede50ae712cac`: the ptmQtl engines (G88, D44); no PR yet. **Merged and released in 1.4.0** (the commit is in `origin/master`; G88 closed 2026-11-23). Its local feed `E:\x\feed` and mzLib worktree `E:\x\pr1430` were deleted 2026-11-23 in PXReprise's E:\x cleanup (the user's OK), so its `dotnet/nuget.config` names a feed that is gone: the worktree can be retired |
| dataRepo | `code/_wt_140_ingest` | `feat/1.4.0-ingest` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` | `0c1f8d0aeb281dde98a8668088892874febd4001`: 1.4.0's ingest side (G103), pushed. The scratch re-ingest binary was built from `54453e1`; `0c1f8d0` adds DATAREPO-84, DATAREPO-D7 and ptmQtl's S2c v3 and S2e. Held by datarepo-9b, which also holds the threads since 2026-10-20. No PR yet: it merges at release. **Merged 2026-10-28 as `88f26b0` and released as 1.4.0**: the worktree can be retired |
| dataRepo | `code/_wt_141` | `feat/1.4.1` (pushed) | this repo, off `master` | `e41c4af`: 1.4.1; merged via feat/tmt (`cb73f74`) and **released 2026-11-01**: can be retired |
| dataRepo | `code/_wt_tmt` | `feat/tmt` (pushed) | this repo, off `feat/1.4.1` | `9e18c4d`: the isobaric ingest (G105); merged as `cb73f74` and **released in 1.4.1**: can be retired |
| dataRepo | `code/_wt_142` | `feat/1.4.2` (pushed) | this repo, off `master` 2c59589 | `3447228`: 1.4.2 (DEF-TMT v3.22, #2941 finding and verdict, matched-ion descriptions); merged as `1248c17`, **released 2026-11-03** (tag `v1.4.2`); can be retired |
| dataRepo | `code/_wt_143` | `feat/1.4.3` (local only, on purpose: master holds it) | this repo, off `master` | `33250a8`: 1.4.3 (`TsvReader`, PXR-R48); merged as `1190f85`, **released 2026-11-05** (tag `v1.4.3`); **worktree removed 2026-11-06** (PXD025315 delivered); the branch stays |
| dataRepo | `code/_wt_144` | `feat/1.4.4` (local only, on purpose: master holds it) | this repo, off `master` `b684c02` | `dbdc48d`: 1.4.4 (the MCP sandbox fix, G128); merged as `5eee942`, **released 2026-11-07** (tag `v1.4.4` on `91f5458`); **worktree removed 2026-11-07**; the branch stays |
| dataRepo | `code/_wt_ai_contrib` | `feat/ai-contributions` (pushed to `origin` = smith-chem-wisc/dataRepo) | this repo, off `master` | `1db8a53584a361346930af98bd473f338319ef85`: built by PXReprise for our review (PXReprise 064); reviewed 2026-11-06, not taken as it stands (G129, U29); not merged. **Superseded by `feat/ai-contributions-v2`** |
| dataRepo | `code/_wt_150` | `feat/1.5.0` (pushed) | this repo, off `master` | `91901d0`: 1.5.0 built (D60-D67), measured on a copy of the whole store (`results/reingest_150_2026-11-12/`), release-prepped (CHANGELOG undated, tutorial `88a2166ec0d33563`, CI green at `7f4fca5`, four platforms built). **Not merged or released.** Since PXReprise#4 (2026-11-13) the code lives in smith-chem-wisc/PXReprise. **Checked 2026-11-17: every code commit of this branch is on PXReprise master** (G136); it is never released as 1.5.0, its content ships in PXReprise 1.0.0 (D74). Can be retired once 1.0.0 is out |
| dataRepo | `code/_wt_ai` | `feat/ai-contributions-v2` (pushed) | this repo, off `feat/1.5.0` `91901d0` | `e591829`: AI contributions reworked (D71; `design/AI_CONTRIBUTIONS_V2.md`, V1-V6 done at `c9d17c3`, 951 tests pass, `results/ai_contributions_e2e_2026-11-14/`), then the stranger agent's report (G137). **Not merged**; to be ported to smith-chem-wisc/PXReprise as `datarepo/<topic>` PRs after G137's five fixes (G136) |
| PXReprise | `E:\GitClones\PXReprise-dataRepo` (a clone, not a worktree) | `master` = `upstream/master` | `origin` = trishorts/PXReprise-dev (shared fork), `upstream` = smith-chem-wisc/PXReprise | **dataRepo's code lives here since 2026-11-13.** One `datarepo/<topic>` branch from `upstream/master` per change, PR to smith, merge commits only. Done: `datarepo/hello-world` `a90ee72` = [smith-chem-wisc/PXReprise#14](https://github.com/smith-chem-wisc/PXReprise/pull/14); `datarepo/split-reason-descriptions` `8ec9b8e` = [#16](https://github.com/smith-chem-wisc/PXReprise/pull/16); both merged 2026-11-17 18:41 UTC, Shipped on board #16. Since then, all merged and Shipped: #42 `datarepo/pep-filter-per-search` (2026-11-22); #47 `datarepo/seam-test`, #48 `datarepo/missing-search-inputs`, #53 `datarepo/tutorial-one-release` (head `42bded4`) and #54 `datarepo/r81-search-filter` (head `76f3f2e`), all 2026-11-23. No datarepo PR is open. At the 2026-11-23 close the clone sat on `datarepo/r81-search-filter`, and a second worktree `E:\GitClones\PXReprise-dataRepo-tut` (on #53's branch) can be removed; branch the next change from `upstream/master` |
| mzLib | `code/_wt_mzlib_sumo` | `fix/sumo-remnant-target-lysine` (pushed to `origin` = trishorts/mzLib) | `E:\GitClones\mzLib`, off `smith/master` b1e925ff9 | `6974a4d4cede89b84a1409411593e391ecbd252a`: [smith-chem-wisc/mzLib#1432](https://github.com/smith-chem-wisc/mzLib/pull/1432), closes #1431 |

**`feat/ptmqtl-engine` merges only after an mzLib release carries #1430.** (History: it merged and shipped in 1.4.0.
The feed and the `pr1430` worktree named below were deleted on 2026-11-23.)
- The branch builds against mzLib packed from #1430's branch: version `1.0.595-pr1430.b2d218d`, in the local feed
  `E:\x\feed`, built in the worktree `E:\x\pr1430` (a worktree of `E:\GitClones\mzLib`). That source is named by
  `dotnet/nuget.config`, which exists on this branch only.
- At merge: delete that file, point at the released mzLib, and bump the ingest path (#1403's ProForma change rides
  along).
- Twelve test failures on the branch are mzLib-version effects, not engine defects. The steps are G88.

**`fix/sumo-remnant-target-lysine` is PR #1432**: `ready for review`, `ready-for-agent`, six referees, on board #16 as
In review. When it merges, move the board item to Shipped and remove the worktree. The MetaMorpheus follow-up (two
MetaDraw settings XMLs still name `... on D`) waits on an mzLib release that carries it.

**`feat/1.4.3` (worktree `code/_wt_143`, off `master` `6109d8d`, 2026-11-05): PXR-R48, the streaming TSV reader.** Merged to
master `1190f85`, released as 1.4.3 on the user's word. The worktree can be removed once PXReprise has delivered PXD025315.
