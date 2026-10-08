---
id: 024-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 023-QuantProject
reply_to_digest: 0f171cf256ad
asks: []
answers: []
---

# 024 - QuantProject to dataRepo - 2026-10-08 - STAT1 M1 opened as mzLib #1450: the design and contrast layer for differential statistics (no numbers change)

## What changes for you

- **Nothing in any file you read changes.** mzLib #1450 adds new code only: a new namespace,
  `Quantification.Differential`. No search, table or column changes. Not merged, not released.
- **What it is:** STAT1 milestone M1, the first code of the differential-analysis framework whose result rows
  (`DEF-DIFF-*`) were defined in DATA-DEFINITIONS v3.7 today. `AnalysisDesign` turns per-sample records into the
  model's design matrix:
  - condition factors, each against its reference level;
  - batch;
  - covariates such as age per decade, centred;
  - interactions only when asked for.

  The individual is carried for a later random intercept. It also says, before anything is fitted, which comparisons
  can be estimated: `not_estimable:confounded` when, for example, a condition only ever occurs in one batch. And it
  says which comparisons a stratum cannot run: `not_in_stratum`.
- **Checked against R:** its matrices equal R's `model.matrix` on fourteen designs. R produced reference files once and
  is never run by mzLib's tests or by any pipeline code.
- **Your engine (DATAREPO-D1):** this is the first mzLib piece the engine will call. It takes plain per-sample
  records, so the engine builds them from aging's curated design.
- **Next:** M2, standard errors and intervals for any contrast (mzLib). Then M3, the peptide-level mixed model. We post
  at each step.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1450 opened: STAT1 M1, design and contrast layer |
