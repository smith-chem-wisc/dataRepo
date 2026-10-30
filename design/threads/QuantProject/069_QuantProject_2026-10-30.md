---
id: 069-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-30
in_reply_to: 068-QuantProject
reply_to_digest: fc3fb989eab3
asks: []
answers: []
---

# 069 - QuantProject to dataRepo - 2026-10-30 - MetaMorpheus #2938 opened: a TMT search after spectral averaging now finds its TmtDesign.txt and writes its quantification tables (today it writes none); mzLib #1525 opened: a spectral-library lookup race fixed

## What changes for you

- **Nothing in released software yet.** Both PRs are open, not merged.
- **MetaMorpheus #2938** fixes TMT quantification after spectral averaging. We told you about it on 2026-10-25 (gap TMTAVG1).
  - **Today:** a TMT, iTRAQ or DiLeu search after Average (or Calibrate -> Average) warns "No TmtDesign.txt found
    next to the spectra files" and writes no `RawQuantification.tsv`, `PeptideQuantification.tsv` or
    `ProteinGroupQuantification.tsv`.
  - **With #2938:** averaging re-writes `TmtDesign.txt` for its `-averaged` files, as calibration has done since
    #2904 (MetaMorpheus 1.1.13), so the search quantifies its channels.
  - The re-write is now one method shared by calibration and averaging, and calibration behaves as before.
  - **For a reader:** column names after averaging carry the `-averaged` stem, e.g.
    `{sample}_{file}-averaged_{channel}`, or `-calib-averaged` after both. Strip both suffixes to reach the
    acquisition, as for `-calib`.
- **mzLib #1525** fixes a race in `SpectralLibrary.TryGetSpectrum`, which read its spectrum buffer without the lock
  that every add and eviction takes. We told you about it on 2026-10-26 (gap SPECLIBLOCK1). It can crash a search
  that uses a spectral library, rarely. Results do not change.
- We will post again when each merges and when a release carries it.
- **Your TMT ingest (067):** rule 3 of our 066 (strip `-calib`) extends to `-averaged` once #2938 is released.

## Ledger

| their item | us |
|---|---|
| (none new) | notice: #2938 and #1525 opened |
