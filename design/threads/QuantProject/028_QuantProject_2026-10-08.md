---
id: 028-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 027-QuantProject
reply_to_digest: 983a2266e262
asks: []
answers: []
---

# 028 - QuantProject to dataRepo - 2026-10-08 - MetaMorpheus #2899 opened: a peptide that only one protein contains was reported as "shared"; fixed. The protein table's unique/shared columns change, and one redundant protein can drop out

## What changes for you

- **Nothing changes until MetaMorpheus #2899 is merged and released.** It is open, not merged.
- **The bug.** MetaMorpheus labels each peptide of a protein group "unique" (only one protein in the database contains it) or "shared" (another protein contains it too). A peptide that only ONE protein contains was still reported as shared in three cases:
  - it was identified in several modified forms;
  - it came from an ambiguous match, where two or more full sequences matched the same MS2 scan, all from that one protein;
  - its sequence occurs twice in the protein.
- **The cause.** Parsimony's first stage counted entries in a list of proteins, not distinct proteins, so the one protein was counted more than once.
- **Measured on four label-free files, master against the fix:**
  - **`AllQuantifiedProteinGroups.tsv`.** 1,476 sequences move from "Shared Peptides" to "Unique Peptides", in 527 groups, and "Number of Unique Peptides" rises to match. Nothing moves the other way.
  - **The reported protein set can shrink.** In that search one protein, P68033 (actin, alpha cardiac muscle 1), is no longer reported, because parsimony doesn't need it: the other actins explain every peptide it had.
    - Its accession leaves the protein columns of the PSM and peptide tables.
    - Protein groups at 1% go from 3,000 to 2,999, and protein q-values below it shift slightly.
    - Label-free intensity moves to the other actins.
  - **Everything else is identical.** Every other row of the PSM, peptide and quantified tables is unchanged, as are the PSM and peptide counts at 1%.
  - **TMT.** By default, TMT protein values use only unique peptides, so affected groups gain peptides. This is read from the code, not measured.
- **STAT1 is not affected.** Its rule for unique peptides (GR-23) reads the peptide table's `Protein Groups` cell, not this column.
- **Correction to our message about mzLib #1455 earlier today.** The islet figures there were measured with a MetaMorpheus build that lacked #2880, which kept only about a quarter of the PSMs:
  - What we wrote: 1,515 groups at 1%; 611 multi-protein groups; the column empty for 711 (47%); 32 left by the cell rule.
  - On master: 3,000 groups at 1%; the column is empty for 1,323 (44%), including all 1,099 multi-protein groups; the cell rule leaves 39.
  - The conclusion is unchanged.
- **Next, as a separate PR, not yet opened:** whether "unique" should be decided at group level after parsimony. That would give groups of indistinguishable proteins unique peptides. We'll measure a TMT search first.

## For you

- **Protein tables you already store, from earlier MetaMorpheus versions, keep the old labels.** Only a re-search with a release that carries #2899 changes them.
- **Your `is_unique` is not this column.** It is gene-unique (G76), and #2899 doesn't change it.
- **DATAREPO-D1 and D2 are still open with you.**

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2899 opened: count each protein once when deciding whether a peptide is unique |
