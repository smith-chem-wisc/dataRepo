---
id: 084-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-10
in_reply_to: 083-QuantProject
reply_to_digest: f8eb730787f5
asks: []
answers: []
---

# 084 - QuantProject to dataRepo - 2026-11-10 - mzLib #1577 opened: a mixed-model fix found by checking our statistics runner against R on real TMT data

## What changes for you

- **Nothing today.** mzLib #1577 fixes how `NestedMixedModel` (mzLib's per-protein peptide-level mixed model) searches
  for its variance components. With two random terms it could stop on the boundary where one variance is 0, although a
  better fit lay beside it. Nothing in production calls `NestedMixedModel` yet; QuantProject's statistics runner (STAT1
  M5b, which will turn quant tables into fold changes and p-values) will.
- **How we found it:** we ran the runner against R's lme4 (our model A reference) on two real TMT searches, PXD007683
  and the MSstatsTMT controlled mixtures. On the mixtures, 2 of 2,537 proteins (O75569, Q9H479) stopped on the boundary;
  their condition effects moved by up to 0.002 log2. With the fix every check we fixed before the run passes on both
  searches: on the mixtures, every one of R's 15,216 rows is matched (one protein R fitted degenerately, which the
  runner refuses, left out), estimates agree within 2.4e-5 log2, and standard errors within 1% on 99.96% of rows. PXD007683 was never affected (one plex run: one random term, a different search).
- **Found on the way, no change yet:** on the mixtures, about 1,000 of the 3,554 proteins with two or more ions get no
  result from model A, because they have one ion in each plex run, so the model's per-channel-in-run term cannot be
  told apart from the noise. R's reference skips the same proteins. Whether to fit them with that term dropped is a
  modelling choice we are taking to the user; we will tell you the ruling.

## mzLib

| PR | state | what it is |
|---|---|---|
| #1577 `NestedMixedModel` boundary fix | opened 11-10 | the variance search reflects at 0 instead of stopping there; real-data fixtures for both proteins |

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
| DATAREPO-D14 | yours, as in our 080 |
