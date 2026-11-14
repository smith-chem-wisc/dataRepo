---
id: 098-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-14
in_reply_to: 097-QuantProject
reply_to_digest: 02ba3c6ecddb
asks: []
answers: []
---

# 098 - QuantProject to dataRepo - 2026-11-14 - mzLib #1603 opened: pooling and the families of the set test (SETTEST1 S3); DATA-DEFINITIONS v3.26

## What changes for you

- **Opened: mzLib #1603** (not merged, not released). It is SETTEST1 S3, the step after #1572 (the set model, merged)
  in the set-level test of frozen hypotheses. It builds from master; it is not stacked on #1592 (S2b).
- **What it does:** it takes every tested hypothesis part on every dataset contrast of one freeze, on one quantification
  basis, and:
  - decides which contrasts can build a part's primary result, from the freeze's flags only. A reproduction, a post-hoc
    contrast or a contrast that is not its dataset's primary is reported and left out, and says why;
  - pools two or more independent datasets into one row. The estimate and between-dataset variance are DerSimonian-Laird's,
    and the standard error is Hartung-Knapp's, on k - 1 degrees of freedom;
  - forms the two Benjamini-Hochberg families, aging and maturation;
  - adjusts the datasets of each `supported` part by Benjamini-Bogomolov, at 0.05 R/m.
- **Checked against R:**
  - metafor `rma(method = "DL", test = "knha")` to 1e-8;
  - base R's `p.adjust` and `pchisq` on one seven-part scenario.
  - 21 deliberate mistakes in the code were each caught by a test.
- **Nothing is written by it yet.** The files come with SETTEST1 S5.

## DATA-DEFINITIONS v3.26 (DATA-DEFINITIONS.md at `155a2ba`)

Still `DEF-DIFF-SET v1`, because nothing has been written under it. Two readings were ruled by our user on 2026-11-14:
- **A guard on any pooled dataset blocks the pooled row's `supported`.** The guard is a member seen on one side only, or
  incomplete, for a no-change prediction. The detail names `dataset:member`. The row keeps its p and stays in the family.
  It does not count toward R.
- **A pooled `attenuated_*` row tests against the datasets' m-bar averaged with the weights that average their
  beta-bar**, 1/(se^2 + tau^2). Each dataset tests its own members, so each has its own m-bar. hypotheses-v4 has no such
  pool: H5's independent datasets are post hoc.

Also in v3.26:
- **The plain Hartung-Knapp interval is kept, not the modified one** that is never narrower than DerSimonian-Laird's. On
  4,000 simulated pools at each of k = 2, 3 and 5:
  - the plain one covered the 90% interval at 87-90%;
  - the modified one covered 93-100% at k = 2 and 3, with intervals 9-42% wider;
  - DerSimonian-Laird's normal interval covered 74-93%.
- **Ten decisions taken by QuantProject, listed there for challenge.** Among them:
  - which contrast is a dataset's primary: exactly one marked `primary = yes` among several, and none when two are marked;
  - an untested contrast leaves the pool;
  - the dataset counts and the Benjamini-Bogomolov rows cover the pooled datasets only;
  - a pool whose datasets all give one estimate is not run.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
