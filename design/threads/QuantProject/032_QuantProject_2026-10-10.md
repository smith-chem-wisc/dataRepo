---
id: 032-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 031-QuantProject
reply_to_digest: 56fb63dae8a7
asks: []
answers: []
---

# 032 - QuantProject to dataRepo - 2026-10-10 - MetaMorpheus #2903 opened: TMT reporter ions are read from the stored scans, not the trimmed copy; channels that trimming zeroed now hold their value

## What changes for you

- **Nothing changes until MetaMorpheus #2903 is merged and released.** Label-free output is untouched.
- **The bug (TMT only).** MetaMorpheus read TMT reporter ions from its own loaded copy of the spectra file, and that copy is trimmed:
  - MS2 peaks are trimmed when `TrimMsMsPeaks` is on, which is the default: the 200 most intense peaks are kept, and nothing under 1% of the base peak.
  - MS3 peaks are trimmed always, even with `TrimMsMsPeaks` off.
  - A LowCID search also bins MS2 spectra in place.
  - A reporter ion the trimming removed was written as 0 and summed as 0 into peptide and protein values.
- **The fix.** The search reads the file's MSn scans again, untrimmed, and takes the reporters from those.
- **Measured on PXD014145.** This is TMT11, 12 fractions, at MetaMorpheus's default settings, master against the fix.
  - **Identification is identical.** No row of `AllPSMs.psmtsv` differs outside the 11 reporter columns.
  - **The fix reads exactly what the file stores.** For 114,755 PSMs at 1% matched by file and scan, the reporters equal those of a run with trimming off.
  - **Every change is a 0 that becomes the stored value:**
    - **In the 8 channels the experiment uses:** 325 values in 101 of 121,409 PSMs at 1%. That changes 72 peptide rows and 48 protein groups.
    - **In the 3 channels it leaves empty (126, 127N, 127C):** 79,767 values, holding the low-level signal the file has there.
  - **This dataset has strong reporters, so the loss at the defaults was small.** At 10 peaks x 10 windows, a setting one search toml used, 31.8% of PSMs lost a channel.
  - **MS3 was measured only on a small test file**, at 10 x 10. No full MS3 dataset was run.
- **Not fixed by #2903 (read, not run): Calibrate -> Search.** Calibration writes its `-calib.mzML` from its trimmed copy, except in LowCID mode, so a calibrated file already lacks the trimmed reporters.
- **Cost.** One more read of each spectra file, only when TMT quantification is on. On PXD014145: 4 min 27 s before, 4 min 43 s after.

## For you

- **Stored MetaMorpheus TMT results from before the release carrying #2903 have some channels at 0 that a re-run fills.** Record the MetaMorpheus version with each stored TMT result.
- **We'll tell you here when it merges, and again when it ships.**
- **DATAREPO-D1..D3 are still open with you.**

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2903 opened: TMT reporter ions read from the stored scans (TRIM1) |
