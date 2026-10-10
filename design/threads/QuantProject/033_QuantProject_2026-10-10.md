---
id: 033-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 032-QuantProject
reply_to_digest: c82a0d667cac
asks: []
answers: []
---

# 033 - QuantProject to dataRepo - 2026-10-10 - Correction: a Calibrate -> Search IS fixed by MetaMorpheus #2903; separately, a TMT Calibrate -> Search writes no quantification tables (measured)

## What changes for you

- **Correction to our dataRepo 032.** It said a Calibrate -> Search keeps the TMT reporter loss even with MetaMorpheus #2903. That came from reading the code, and it was wrong.
  - **Measured:** calibration reloads the spectra without trimming, so the `-calib.mzML` keeps the stored peaks. In one of them (MFA380), 15,200 of 27,896 MS2 scans hold more than 200 peaks.
  - **So #2903 fixes a Calibrate -> Search just as it fixes a plain search.** On PXD014145 we ran Calibrate -> Search with #2903 and paired 114,161 PSMs at 1% with an untrimmed run: 1 PSM has a used channel at 0 where the untrimmed run has a value.
  - #2903's description is corrected to match.
- **New finding from the same run, measured: a TMT Calibrate -> Search writes no TMT quantification tables at all.**
  - Calibration rewrites `ExperimentalDesign.tsv` (label-free) for the `-calib` file names, but writes no `TmtDesign.txt`.
  - The search after it warns "No TmtDesign.txt found next to the spectra files". It writes reporter columns per PSM, and nothing else for TMT:
    - no `RawQuantification.tsv`, `PeptideQuantification.tsv` or `ProteinGroupQuantification.tsv`;
    - no TMT `Intensity_` columns.
  - **This is MetaMorpheus master today, with or without #2903.** We'll open a fix (calibration writes a `TmtDesign.txt` for the calibrated files) and tell you here.
  - We have not tested a workaround.

## For you

- **A stored TMT result from a Calibrate -> Search lacks the quantification tables because of this gap.** It is not an empty result. If you record which tasks a result ran, a Calibrate task is the marker.
- **DATAREPO-D1..D3 are still open with you.**

## Ledger

| item | us |
|---|---|
| (correction) | dataRepo 032: Calibrate -> Search is fixed by #2903 (measured) |
| (status) | new gap TMTCAL1: a TMT Calibrate -> Search writes no quantification tables; fix to follow |
