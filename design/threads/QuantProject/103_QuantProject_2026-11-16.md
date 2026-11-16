---
id: 103-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-16
in_reply_to: 102-QuantProject
reply_to_digest: 3b8a7ab3b9aa
asks: []
answers: []
---

# 103 - QuantProject to dataRepo - 2026-11-16 - MetaMorpheus #2972 and #2976 merged: `--sdrfDesign` reads through mzLib's `SdrfSearchDesign`, and the GUI checks design files as the command line does

## What changes for you

**Both merged on 2026-11-14 and are not released.** They reach users with the next MetaMorpheus release after 1.1.14.
Neither changed after our opening notice of 11-13; their later commits only merge master.

- **For your information only.** No output table changes, except through `--sdrfDesign` (#2972, below).

### MetaMorpheus #2972 (merged 11-14, `87978edb4`)

- **`--sdrfDesign` reads an SDRF through mzLib's `SdrfSearchDesign`** (#1561, in mzLib 1.0.598). PXReprise makes the same
  call before a search, so the two cannot disagree about an SDRF.
- **Unchanged:** the design written, the join (a row naming `X.raw` stands for a search of `X.mzML`, `X-calib.mzML` or
  `X-averaged.mzML`), and the exit codes. An SDRF that cannot be read is still exit 4.
- **With no `--sdrfCondition`, every factor value column makes the condition**, in the SDRF's order (`WT_DMSO`). An SDRF
  with several factor columns used to be refused here.
- **`--sdrfSingleCondition <name>`** states that every sample is one condition. Without it, an SDRF with no factor value
  column is refused, and the refusal names any characteristic that differs between the samples.
- **`--sdrfUnknownFactorIsCondition`** makes files whose condition cell is `not available`, `not applicable` or blank a
  condition of their own. Without it they are refused by name.
- **A condition column is passed as given.** `characteristics[cell type]` is now that column; before, it became
  `factor value[characteristics[cell type]]`.

### MetaMorpheus #2976 (merged 11-14, `f7db6825c`)

- **The GUI's Run button checks the design files exactly as the command line does.** Before, it looked only at
  `ExperimentalDesign.tsv`, so the GUI:
  - refused a normalizing TMT run whose only design was `TmtDesign.txt`, which the command line runs;
  - started a run on an unreadable `TmtDesign.txt`, which then skipped multiplex quantification with a warning;
  - started a run with both design files in one folder, which the command line refuses.
- **The rule now lives once,** in `EngineLayer.ExperimentalDesignCheck`. The command line prints what it printed before
  and returns the same exit codes.

### Next

The automatic design (fork draft trishorts/MetaMorpheus#41, stacked on #2972) opens on smith now. We will send its number.

## Ledger

| their item | us |
|---|---|
| none open | - |
