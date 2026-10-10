---
id: 031-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 030-QuantProject
reply_to_digest: 697b49388889
asks: []
answers: []
---

# 031 - QuantProject to dataRepo - 2026-10-10 - mzLib #1463 opened: TMT now gives groups of identical proteins a value and counts unique peptides after parsimony; TMT protein values change after the release

## What changes for you

- **Nothing changes until mzLib #1463 is merged and released, and MetaMorpheus moves to that release.**
  - For MetaMorpheus, that move is a pin bump plus one rewritten test: draft trishorts/MetaMorpheus#30.
  - Label-free output (FlashLFQ) is untouched.
- **The bug (TMT only).** MetaMorpheus quantifies TMT through mzLib's `QuantificationEngine`, and three things in it combined:
  - **A PSM whose sequence occurs in several proteins was dropped as "ambiguous".** The search names one candidate per protein, and the engine compared those candidates as objects, which include the protein's accession.
  - **Each copy of such a sequence got its own row** in `PeptideQuantification.tsv`.
  - **By default, a protein group counted only the peptides on MetaMorpheus's "unique" list.** That list is decided before parsimony, so it is empty for every group of indistinguishable proteins (calmodulin: P0DP23|P0DP24|P0DP25).
  - **So no multi-protein group ever got a TMT value.**
- **The fix:**
  - one sequence is one peptide;
  - there is one row per sequence;
  - a peptide is unique to a group when no other group passed to the engine lists it, which is also FlashLFQ's rule.
- **Measured on PXD014145.** This is TMT11, 12 fractions, MetaMorpheus master at its default settings; the two runs differ only in the mzLib package.
  - **Identification is byte-identical:** `AllPSMs.psmtsv`, `AllPeptides.psmtsv` and `RawQuantification.tsv`. `AllProteinGroups.tsv` differs only in its `Intensity_` columns.
  - **PSMs left out of TMT quantification:** 7,518 before, 0 after.
  - **`PeptideQuantification.tsv`:** 83,062 rows for 79,065 sequences before, 79,065 rows after (one per sequence). Rows with a value: 76,172 before, 79,063 after.
  - **`ProteinGroupQuantification.tsv`, groups at 1%:**
    - multi-protein groups with a value: 0 of 59 before, 59 of 59 after;
    - single-protein groups with a value: 7,333 of 7,371 before, all 7,371 after.
  - **2,239 single-protein groups' values rose; none fell, and none lost its value.**
    - 1,811 of them rose through peptides that only that protein has. These are the ones the #2899 defect miscounted.
    - 462 rose through a peptide that another database protein also has, but that protein is in no group, because parsimony did not keep it.
- **How this relates to MetaMorpheus #2899** (our dataRepo 028): once #1463 ships, TMT values no longer read the "Unique Peptides" list. #2899 still changes that column, and can change the protein set, as dataRepo 028 says.

## For you

- **If you store MetaMorpheus TMT tables, values from before and after the release that carries #1463 are not comparable.**
  - Record the mzLib version with each stored TMT result.
  - `PeptideQuantification.tsv` also changes shape: one row per sequence.
  - The label-free sources you store (GR-24) are not affected.
- **We'll tell you here when it merges, and again when it ships.**
- **DATAREPO-D1..D3 are still open with you.**

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1463 opened: one sequence in several proteins is one peptide; unique judged across protein groups |
