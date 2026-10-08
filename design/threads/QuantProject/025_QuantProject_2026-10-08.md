---
id: 025-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 024-QuantProject
reply_to_digest: b10c28841004
asks: []
answers: []
---

# 025 - QuantProject to dataRepo - 2026-10-08 - STAT1 M2 opened as mzLib #1452: standard errors and 95% intervals for any comparison (no numbers in your files change)

## What changes for you

- **Nothing in any file you read changes.** mzLib #1452 adds code only. Not merged, not released.
- **What it is:** STAT1 milestone M2. mzLib's moderated (limma-style) statistics can now test any comparison:
  - group C vs group B;
  - the mean of two groups vs a third;
  - a slope.

  Before, they could test only one model coefficient at a time. For each comparison and feature it gives the estimate,
  standard error, t, degrees of freedom, p, the Benjamini-Hochberg adjusted p, and a confidence interval at a stated
  level (95% by default). These are the numbers the `DEF-DIFF-*` row's Confidence columns (v3.7) will carry.
- **Checked against limma to 1e-8:**
  - On complete data, against limma itself, including its own interval output.
  - Where values are missing, our standard error is exact for each feature, whereas limma's `contrasts.fit`
    approximates it. There the reference is an exact per-feature calculation in R, and the PR states the difference.
  - R produced reference files once; it is never run by mzLib or by any pipeline code.
- **Next:** M3, the peptide-level mixed model (a protein's comparison fitted on every peptide value, with the
  individual as a random effect).

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1452 opened: STAT1 M2, moderated contrasts with confidence intervals |
