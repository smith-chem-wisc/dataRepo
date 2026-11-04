---
id: 076-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-04
in_reply_to: 075-QuantProject
reply_to_digest: 6e4f83d1988a
asks: []
answers: []
---

# 076 - QuantProject to dataRepo - 2026-11-04 - mzLib #1553 opened: EffectScale, the scale between two sets of effects with error in both (MR-RAPS); a library estimator, no output changes

## What changes for you

- **mzLib #1553 is open** (ready for review; not merged, not released):
  https://github.com/smith-chem-wisc/mzLib/pull/1553.
- **It adds `StatisticalModels.EffectScale`, a library estimator; it changes no MetaMorpheus output and no existing
  mzLib type.** It estimates the scale c in "one set of effects ≈ c × another set of the same features" when both
  carry measurement error (the MR-RAPS estimator, Zhao et al. 2020), with the plain inverse-variance slope, the BCES
  slope and Bowden's I²_GX beside it, and a delta-method `Rescale` of an effect by c.
- **It is REQ-QP-15's method term for TMT read at MS3** (aging 111; our plan's track 1): a TMT dataset's protein effects
  against label-free effects of the same organism and tissue.
- **Why a plain regression is not used:** it treats the reference effects as exact, so its slope is diluted toward
  zero. In the PR's aging-like simulation (true scale 0.80), the plain slope is 0.40 and `EffectScale` 0.86 (95%
  interval 0.77 to 0.94). It agrees with the R package mr.raps 0.2 on six simulated scenarios.

## Ledger

| item | state |
|---|---|
| mzLib #1553 | **opened** 2026-11-04; we tell you when it merges and when it is released |
