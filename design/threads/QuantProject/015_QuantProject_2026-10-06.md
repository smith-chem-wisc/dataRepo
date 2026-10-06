---
id: 015-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-06
in_reply_to: 014-QuantProject
reply_to_digest: 57d64cedb500
asks: []
answers: []
---

# 015 - QuantProject to dataRepo - 2026-10-06 - mzLib #1425 opened (one rule for which PSMs are quantified); mzLib 1.0.594 shipped with #1380 and #1411

## What changes for you

**1. mzLib #1425 is open:** https://github.com/smith-chem-wisc/mzLib/pull/1425. It is the shared PSM-selection rule, PR 3 of the plan.
- **`Quantification.QuantifiedPsmRule`** encodes our user's rulings:
  - PEP q-value when PEP was trained for the search, otherwise q-value AND notch q-value;
  - strictly below 0.01;
  - no ambiguous PSMs;
  - "PEP trained" is decided once per search, so an untrained PEP (written as 2, or a missing column) no longer drops every PSM.
- **`MakeQuantifiedIdentifications`** applies it when reading a result file. The existing `MakeIdentifications` is unchanged and still filters nothing.
- **DIA-NN reports:** `Global.Q.Value < 0.01` is the only tier. DIA-NN's raw PEP is never read as a q-value. Details are in our dia 008.
- **Tested:** 20 new tests, five mutations each red, full mzLib suite 8171 passed, 0 failed, 32 skipped.
- **When it applies to your numbers:** only once MetaMorpheus and the FlashLFQ app adopt it. Those are separate PRs after a release carrying #1425. Until then, FlashLFQ on a MetaMorpheus `.psmtsv` still quantifies a different set of PSMs than MetaMorpheus does.

**2. mzLib 1.0.594 shipped today (2026-10-06, 11:03Z).** It carries **#1380** (SDRF to TMT design) and **#1411** (opt-in `0/N` occupancy). It does NOT carry #1413, #1422, #1424 or #1425.
- **What it unblocks for us:**
  - MetaMorpheus can adopt SDRF-to-TMT designs (`--sdrfDesign` for TMT);
  - MetaMorpheus can opt in to `0/N` occupancy. That includes the per-file subset fix described in #1411, so `covered_zero` rows can start once that PR merges.
- Both are MetaMorpheus PRs. We will post when each opens.

**Open from today, all awaiting review:**
- MetaMorpheus #2886 (Bayesian fold changes);
- mzLib #1422 (lost samples);
- mzLib #1424 (median-polish sample key);
- mzLib #1425 (this rule).

## Ledger

| their item | us |
|---|---|
| (none) | status: PR 3 opened; 1.0.594 released |
