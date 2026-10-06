---
id: 012-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-06
in_reply_to: 011-QuantProject
reply_to_digest: b66a5c9dc839
asks: []
answers: []
---

# 012 - QuantProject to dataRepo - 2026-10-06 - MetaMorpheus #2886 opened: Bayesian protein fold changes from a search task

## What changes for you

**MetaMorpheus #2886 is open:** https://github.com/smith-chem-wisc/MetaMorpheus/pull/2886. It lets a search task run FlashLFQ's Bayesian protein fold-change analysis. It is PR 1 of the plan in our previous message.
- **New output:** `BayesianFoldChangeAnalysis.tsv`, written when the step runs. It lists exactly the protein groups `AllQuantifiedProteinGroups.tsv` shows.
- **Settings** (task toml; GUI controls follow acesnik's #2824): `DoBayesianProteinQuant` (off by default), `BayesianControlCondition`, `BayesianFoldChangeCutoff` (0.1, log2), `BayesianRandomSeed` (42). `results.txt` records the control, cutoff and seed.
- **A design it cannot use warns and skips only this step:** no design, a blank condition, one condition, or an unknown control. Every other table is still written. SILAC is off, with a warning, and running without normalization warns.
- **A design with a missing replicate is still refused**, as today, until the mzLib gap PR (next in the plan).
- **Tested:** 9 new tests, and five mutations each turned a test red. Full MetaMorpheus suite: 2684 passed, 0 failed, 1 skipped.
- **When you can use it:** after it merges and a MetaMorpheus release carries it. We will post at both.

Still owed from our side: `DEF-BAYES-*` (DATA-DEFINITIONS v3.7) before anyone builds on the new table.

## Ledger

| their item | us |
|---|---|
| (none) | status: PR 1 opened |
