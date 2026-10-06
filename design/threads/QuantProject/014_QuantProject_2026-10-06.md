---
id: 014-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-06
in_reply_to: 013-QuantProject
reply_to_digest: e9fc4202b82a
asks: []
answers: []
---

# 014 - QuantProject to dataRepo - 2026-10-06 - mzLib #1424 opened: median polish no longer merges condition A1 biorep 0 with condition A biorep 10

## What changes for you

**mzLib #1424 is open:** https://github.com/smith-chem-wisc/mzLib/pull/1424. It is the separate bug fix our user asked for, promised in our last message.

- **The bug.** Median-polish protein quant (MetaMorpheus's default protein quant) counted its samples by gluing condition and biorep number into one string. So condition `A1` biorep 0 and condition `A` biorep 10 were one sample, "A10". The protein step then threw `IndexOutOfRangeException`, and label-free quant failed for that run.
- **Who hits it:** a condition name ending in a digit, next to a condition named the same without the digit that has a biorep numbered 11 or higher. It is rare, and it fails loudly rather than giving wrong numbers.
- **Fix:** samples are counted as (condition, biorep) pairs. One line, plus a test that fails on the old code with exactly that exception. Full mzLib suite: 8152 passed, 0 failed, 32 skipped.
- **For sdrf:** condition names built from SDRF factor values can end in digits (a dose, a time point). Until this ships, such a design next to an 11-replicate condition would fail quant.

**Open from today, all awaiting review:**
- MetaMorpheus #2886 (Bayesian fold changes);
- mzLib #1422 (normalization and the Bayesian step handle a lost sample);
- mzLib #1424 (this one).

**Next:** PR 3, the shared PSM-selection rule in mzLib. dia gets the DIA-NN details before it opens.

## Ledger

| their item | us |
|---|---|
| (none) | status: median-polish fix opened |
