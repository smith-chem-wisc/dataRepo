# From the user, 2026-10-21: personal GitHub Actions minutes are nearly used up, so keep private-repo CI cheap

**What happened.** GitHub warned that the personal account `trishorts` had used 90% of its Actions minutes for
October. The account is on the **Free plan: 2,000 minutes a month, shared by every private repo it owns.** From
Oct 1 to 21 its private repos used **1,941 minutes (97%)**:
- `trishorts/PXReprise`: 1,932 minutes. `ci.yml` builds twice on every push to `master`.
- `trishorts/circular-peptide-combinatorial-synthesis`: 9 minutes, from Copilot pull-request review.

When the minutes run out, Actions stops on **every** trishorts private repo until the Nov 1 reset, unless the
user adds a payment method and a budget. **These don't count against the quota:** smith-chem-wisc repos, and
trishorts's public repos and forks (mzLib, MetaMorpheus, FlashLFQ, ProteaseGuru, aging-pipeline). Standard runners
are free there.

**Your repo:** `smith-chem-wisc/dataRepo` is public (workflows: binaries.yml,ci.yml,dotnet-binaries.yml). Standard runners are free there, so there is nothing to do.

## Rules for every project from now on

1. **Ask the user before you add a workflow or Copilot review to a private trishorts repo.** Almost every project
   repo has no CI today. Keep it that way unless there is a reason.
2. **If a private repo does run CI, keep it cheap:**
   - Use `ubuntu-latest` only. Windows minutes count 2x and macOS minutes 10x.
   - Don't build on every push to `master`. Prefer `pull_request` plus `workflow_dispatch`. Otherwise add
     `paths-ignore: ['design/**', '**/*.md', 'docs/**', 'results/**']`, so thread and notes commits never start a
     build.
   - Add `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`.
   - Build once. Don't rebuild the solution in a second job.
   - Run live or network canaries on a daily `schedule:`, not on every push.
   - Set `timeout-minutes` on every job.
3. **For a commit that only touches docs, design or threads, put `[skip ci]` in the message.** GitHub skips
   `push` and `pull_request` workflows when the head commit has it.
4. **Heavy CI belongs in a public repo or the smith-chem-wisc org,** where standard runners cost nothing.
5. **Billing is the user's call.** Don't change plans, budgets, repo visibility or runners. Raise it with the user
   instead. The options already on the table are a budget (Linux is about $0.006/minute), GitHub Pro (3,000
   minutes), making a repo public, or a self-hosted runner on the lab workstation.

**Checking usage:** `gh api "/users/trishorts/settings/billing/usage?year=YYYY&month=MM"`. This needs the gh
`user` scope, which was granted 2026-10-21. Only Actions rows for **private** repos count toward the 2,000 minutes.

**No reply needed** unless your repo line above says there is something to do.
