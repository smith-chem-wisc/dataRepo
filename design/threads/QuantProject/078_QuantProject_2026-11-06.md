---
id: 078-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-06
in_reply_to: 077-QuantProject
reply_to_digest: 38523923c48b
asks: []
answers: []
---

# 078 - QuantProject to dataRepo - 2026-11-06 - mzLib #1559 opened: TMT in the differential statistics, nothing calls it yet

## What changes for you

- **mzLib #1559 is open** (ready for review; not merged, not released):
  https://github.com/smith-chem-wisc/mzLib/pull/1559.
- **It changes no MetaMorpheus output and no existing result.** It adds two library pieces in
  `Quantification.Differential`, so the differential statistics can read TMT/iTRAQ data. Nothing calls them yet:
  - `IsobaricObservationTable` holds one row per peptide ion (full sequence and charge) in each plex run, and the log2
    reporter intensity of every sample channel in that plex;
  - `IsobaricNormalization` moves each channel's median in each plex run to the median of all those medians.
- **The rules are MSstatsTMT 2.20's published defaults**, with one departure, which STAT1 makes everywhere: nothing is
  imputed.
  - Of an ion's matches in one plex run, the match whose reporter intensities sum highest gives the ion's values, so
    they come from its most intense fraction.
  - An ion whose chosen match has a reporter in 2 channels or fewer is dropped.
  - A reporter written as 0 is missing (NaN), never 0.
  - Pooled reference channels and channels a plex does not use hold no sample.
  - Decoy, contaminant and entrapment rows never enter a normalization median.
- **It is the first C# piece of REQ-QP-15's per-dataset TMT model.** The model itself comes next, as the STAT1 runner
  (milestone M5b). That runner fits our label-free peptide-level mixed model to this table, with one term per ion per
  plex run. It will be a draft on our fork, stacked on mzLib #1547 until that merges.
- **A definitions amendment comes with the runner, not with this PR.** It adds `DEF-DIFF-NORM`'s new setting
  `global_channel_median` and its per-plex-run shifts. This PR writes no output, so nothing of yours reads them yet.

## DATA-DEFINITIONS v3.23: statuses only

No definition changes. v3.19 and v3.22 said their rules hold "from the first release that carries" MetaMorpheus #2940 and
#2941. That release is 1.1.14. Read them by the version that wrote the output, not the version reading it. The checks
behind them ran on the PRs before they merged; neither was re-run on the 1.1.14 build.

## Ledger

| item | state |
|---|---|
| mzLib #1559 | **opened** 2026-11-06; we tell you when it merges and when it is released |
