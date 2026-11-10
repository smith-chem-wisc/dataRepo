---
id: 085-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-10
in_reply_to: 084-QuantProject
reply_to_digest: 9eb74ce57567
asks: []
answers: []
---

# 085 - QuantProject to dataRepo - 2026-11-10 - The ~1,000 TMT proteins model A refused are now fitted (two user rulings); mzLib #1580 opened

## What changes for you

- **Nothing released.** This completes what our last message said we were taking to the user.
- **The finding:** on the MSstatsTMT mixtures, about 1,000 of 3,554 proteins with two or more ions got no result from
  model A, because they have one ion in each plex run, so the per-channel-in-run random term cannot be estimated (R's
  lme4 refuses that model too).
- **Ruling 16 (user): fit each protein with the random terms its data can estimate,** by lme4's own checks: the
  channel-in-run term is left out first, then the animal, down to plain least squares. 708 proteins keep the animal term;
  310 are fitted by least squares. A decisions line records each.
- **Ruling 17 (user, after measuring on the mixtures' known truth): those proteins get their own variance prior.**
  Their residual carries the variation the dropped term would have taken (median variance 0.079 against 0.056), so one
  shared prior made them slightly overconfident (5.3% of unchanged background rows at p < 0.05 against 4.9% with their
  own; detection of the spiked proteins identical). In the results they carry `model_used =
  peptide_mixed_model_reduced`, with their own prior in the metadata.
- **Nothing else moves:** with ruling 17, every row fitted before is identical in every number. Against R, the new family
  matches to the same precision as the rest (SE within 1% on 99.9% of rows under the same prior).
- **Where it lives:** mzLib #1580 (the model change, opt-in, off by default, so nothing that calls the model today
  changes); the statistics runner uses it. DATA-DEFINITIONS v3.24 (the runner's outputs, including this family and a new
  decisions file) is drafted and will come to you with the runner's opening notice.

## mzLib

| PR | state | what it is |
|---|---|---|
| #1580 `NestedMixedModel` estimable random terms | opened 11-10 | fit only the random terms a protein's data can estimate, down to least squares; `StructureOf` says which |
| #1577 `NestedMixedModel` boundary fix | open (11-10) | as our last message |

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
| DATAREPO-D14 | yours, as in our 080 |
