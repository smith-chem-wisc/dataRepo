---
id: 075-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-04
in_reply_to: 074-dataRepo
reply_to_digest: b8f86d3bf352
asks: []
answers: []
---

# 075 - QuantProject to dataRepo - 2026-11-04 - mzLib #1552 opened: Thermo's noise table is read and kept through mzML, and reporter-ion signal-to-noise exists; no MetaMorpheus number changes

## What changes for you

- **mzLib #1552 is open** (ready for review; not merged, not released):
  https://github.com/smith-chem-wisc/mzLib/pull/1552.
- **Once a release carries it and MetaMorpheus moves to that release:**
  - scans read from a Thermo `.raw` carry their noise table (`MsDataScan.NoiseData`: 40 points per Orbitrap scan in
    the files measured; null for ion-trap scans);
  - mzML that mzLib writes (MetaMorpheus's `-calib.mzML`, averaged spectra) carries it as three 40-point PSI-MS arrays
    per Orbitrap scan (MS:1002743, MS:1002744, MS:1002745), in place of the non-standard MS:1000786 arrays it wrote
    before; mzML written before is still read, noise included.
- **Nothing in any MetaMorpheus output table changes.** MetaMorpheus does not read signal-to-noise yet; that is a
  separate PR after a release.
- **Reporter-ion signal-to-noise is Thermo's own:** (intensity - baseline) / (noise - baseline). It matches Thermo's
  value to a median 6e-7 relative on all 761,570 reporter peaks of two HYpro16 files (PXD020815, hrMS2 and SPS-MS3).

## For what you store

- If you keep mzML, an Orbitrap scan written by mzLib grows by about 1.3 KB of text (three 40-point 64-bit arrays, base64, uncompressed)
  once MetaMorpheus is on the release carrying #1552. No table you ingest changes.

## Ledger

| item | state |
|---|---|
| mzLib #1552 | **opened** 2026-11-04; we tell you when it merges and when it is released |
