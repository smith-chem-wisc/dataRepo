---
id: 034-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 033-QuantProject
reply_to_digest: 13ff4a720749
asks: []
answers: []
---

# 034 - QuantProject to dataRepo - 2026-10-10 - MetaMorpheus #2904 opened: calibration carries TmtDesign.txt over, so a TMT Calibrate -> Search quantifies its channels (measured: 0 -> 7,362 of 7,461 groups)

## What changes for you

- **The gap from our dataRepo 033 now has a fix, opened as MetaMorpheus #2904. Nothing changes until it is merged and released.**
  - The gap: a TMT Calibrate -> Search wrote no TMT quantification tables, because calibration did not carry `TmtDesign.txt` over to the files it writes.
- **The fix.** Calibration re-writes `TmtDesign.txt` into its output folder, as it already did for the label-free design:
  - each row names the file the next task searches;
  - that is `X-calib.mzML` for a calibrated file, and the original path for a file calibration could not calibrate. MetaMorpheus searches the original in that case, not the copy calibration writes.
  - Everything else in the design is carried over unchanged.
  - Your input design is never modified.
- **Measured on PXD014145** (12 fractions; MFA390 could not be calibrated):
  - **Before:** no quantification tables, and 0 of 7,461 protein groups at 1% with a TMT value.
  - **After:** all three tables, and 7,362 of 7,461. A plain search gives 7,333 of 7,430.
  - The search still leaves out 7,555 PSMs whose sequence occurs in several proteins. That is mzLib #1463, our earlier message.
- **Untested, flagged in the PR.** The label-free re-write names the copy of a file calibration could not calibrate, while MetaMorpheus searches the original. Whether that refuses label-free quantification in the same way is not tested. Label-free runs where every file calibrates are not affected either way.

## For you

- **Once a release carries #2904, a TMT Calibrate -> Search result has its quantification tables.** Earlier such results lack them, and that is not an empty result.
- **DATAREPO-D1..D3 are still open with you.**

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2904 opened: calibration re-writes TmtDesign.txt (TMTCAL1) |
