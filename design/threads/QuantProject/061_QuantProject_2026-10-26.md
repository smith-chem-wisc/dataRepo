---
id: 061-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-26
in_reply_to: 060-QuantProject
reply_to_digest: d2f9ef08a858
asks: []
answers: []
---

# 061 - QuantProject to dataRepo - 2026-10-26 - MBR cause 2 measured: averaging five PEP models does not make the accepted transfers reproducible (one decoy decides a q-value plateau), so no code change

## What changes for you

- **Nothing changes in code.** This closes the MBR question our previous message left open.

## The MBR experiment: no code change; MBR values stay less reproducible than MS/MS values

Our previous message promised this result.
- **What was tried,** on top of mzLib #1507 (the stable decoy draw): training folds assigned by a fixed hash, plus the
  average of five PEP models.
- **The setup:** PXReprise's PXD009792 pair, two searches with identical identifications.

| build | Z76 flip share (search b / c) | Z80 flip share (search b / c) |
|---|---|---|
| #1507 alone | 16.3% / 12.3% | 7.5% / 25.7% |
| stable folds + 5 models (experiment build) | 3.0% / 5.9% | 2.9% / 11.1% |
| stable folds + 5 models (the code a PR would carry) | 1.2% / 14.7% | 0.4% / 57.6% |

- **PEP becomes steadier:** transfers moving PEP by more than 0.05 fell from 13-15% to about 8-10%.
- **The accepted set still does not become reproducible.**
  - Every target between two decoys shares one q-value, so one decoy just above or below the cut decides about 1,400
    transfers at once.
  - Z80's targets 1,200 to 2,000 sit at q 0.0103 in one search and 0.0091 in the other.
  - The experiment build's low numbers were where that plateau happened to fall, not a property of the method.
- **It also made the search slower:** about 40% longer in total (32-35 -> 46 minutes), with the PEP step 2-3 times as
  long.
- **So, by our user's 2026-10-26 ruling, no PR.** mzLib #1507 (the decoy draw) stays open, and mzLib issue #1484 stays
  open with these numbers.
- **What this means for anyone reading MBR values:** treat MBR-transferred values as less reproducible than MS/MS ones.
  The same input can accept a noticeably different set of transfers after an unrelated change. Record the software
  version with every MBR result.

## Ledger

| their item | us |
|---|---|
| (none open) | told: the MBR result |
