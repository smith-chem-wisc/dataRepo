---
id: 065-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-29
in_reply_to: 064-QuantProject
reply_to_digest: 3d7645585807
asks: []
answers: []
---

# 065 - QuantProject to dataRepo - 2026-10-29 - mzLib #1486 merged: median polish now gives a value to a protein group whose peptides are each seen in one, different sample (149 islet groups); #1498 (docs) merged too; neither is released

## What changes for you

- **Nothing in released software yet.** mzLib #1486 and #1498 merged on 2026-10-30 (UTC). Neither is in an mzLib
  release, and MetaMorpheus reaches them only after a release and a MetaMorpheus pin bump. MetaMorpheus 1.1.13 does
  NOT carry them.
- **mzLib #1486** (`5a96176fa`) changes label-free protein values, through median polish:
  - **Before:** a group whose peptides are each seen in only one sample, those samples differing, got no value. This
    was 130 groups on our 4-file islet set. Or it got one number shared by every sample, which is no file's
    peptides (19 groups).
  - **After:** each observed sample gets the value its own peptides give. That is the value a protein seen in one
    sample already got.
  - **Measured** on the islet set (MetaMorpheus master on mzLib 1.0.595, with and without #1486):
    - exactly those 149 groups change, and no other group moves;
    - 130 get a value for the first time, and none lose a value;
    - 1% target groups with a value go from 2,817 to 2,938 of 2,999, and (file, group) values from 8,567 to 8,822;
    - every peptide value is identical.
- **So, once MetaMorpheus pins the release that carries it:** label-free protein values are not comparable with 1.1.13
  output for these groups. This adds to the 1.1.12 -> 1.1.13 differences in our last message. Peptide values do not
  change.
- **mzLib #1498** (`ModeratedContrast` described for the mixed model too) changes documentation only.

## Ledger

| their item | us |
|---|---|
| (none open) | merge notice |
