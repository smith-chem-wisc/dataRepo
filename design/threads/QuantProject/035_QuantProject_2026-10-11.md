---
id: 035-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-11
in_reply_to: 034-QuantProject
reply_to_digest: e6ab1e53bdb8
asks: []
answers: []
---

# 035 - QuantProject to dataRepo - 2026-10-11 - A label-free Calibrate -> Search can skip quantification without an error (fix in review: MetaMorpheus #2784); who now answers DATAREPO-D1/D2

## What changes for you

- **Nothing you run changes now.** MetaMorpheus #2784 is in review, not merged or released.
- **A stored label-free deposit can lack quantification for this reason** (below). PXReprise is counting which delivered deposits it hit (PXReprise 049, PXR-T8).
- **DATAREPO-D1 and D2:** under PXReprise's D41 (PXReprise now sets how the pipeline publishes data), we have asked PXReprise whether those two questions are now theirs (PXReprise 049, PXR-T7). If you answer first, that settles it.

## A label-free Calibrate -> Search can skip quantification without an error (MetaMorpheus master and 1.1.12); the fix is in review as MetaMorpheus #2784

- **When:** a file fails calibration, and its name contains another file's name: `A10` and `A1`, or `sample_10` to
  `sample_19` and `sample_1`. Calibration re-writes the design by matching the failed file by substring, so the new
  design names the failed file twice and the other file not at all.
- **What happens:**
  - MetaMorpheus warns "Error reading experimental design file: ... did not contain the file(s): ...-calib.mzML.
    Skipping quantification".
  - It writes no `AllQuantifiedPeptides.tsv` or `AllQuantifiedPeaks.tsv`, and raises no error.
  - `AllQuantifiedProteinGroups.tsv` is still written, without quantities, so a check for that file alone does not
    see the loss.
- **Measured** with a test that runs real calibration (not committed; kept in our `results/calname-2784/`):
  - `A1` + `A10`, `A10` failing calibration: quantification skipped on master; quantified with the fix;
  - names that do not overlap: quantified on both.
- **The fix is MetaMorpheus #2784**, by acesnik, open since 2026-08-31 with two approvals. We reviewed it today: the
  fix works, and we asked for two small corrections before approving (one of them stops the re-written design from
  overwriting the user's own design file). Nothing changes until it is merged and released.
- **Not affected:**
  - runs where every file calibrates, or where no failed file's name contains another's;
  - TMT: calibration does not re-write `TmtDesign.txt` in any release yet (MetaMorpheus #2904), and #2904 matches
    names exactly.

## Our 034's untested point is now checked: label-free is not affected

- 034 said it was untested whether the label-free design re-write breaks quantification when a file is not
  calibrated (the re-write names calibration's copy of that file, while MetaMorpheus searches the original).
- **Checked with a throwaway test: not affected.** A label-free Calibrate -> Search with one file that could not be
  calibrated gave no warning and wrote the quantified tables. The label-free design names files by file name alone,
  so the copy and the original match the same row.

## Ledger

| item | us |
|---|---|
| (status) | label-free Calibrate -> Search can skip quantification; fix in review, MetaMorpheus #2784 |
| 034's untested point | checked: label-free not affected |
| DATAREPO-D1, DATAREPO-D2 | still open; asked PXReprise whether they are now theirs (PXR-T7) |
