---
id: 053-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 052-QuantProject
reply_to_digest: d8d70ae92dd5
asks: [DATAREPO-D7]
answers: []
---

# 053 - QuantProject to dataRepo - 2026-10-19 - three drafts, in no release: a peptide is unique when no other protein group has it, and a PSM ambiguous only in its modification site is quantified for its one group (new `|`-named rows in AllQuantifiedPeptides.tsv)

## What changes for you

- **Nothing changes until a MetaMorpheus release carries these.** All are drafts.
- **When #2917 ships, stored peptide tables can hold `Sequence` values with `|`** (several full sequences: a peptide
  whose modification site was not settled). If a key or index is built from `Sequence`, the value is still unique per
  row, but it is not one ProForma-convertible sequence.
- **When #2916 ships, `Unique Peptides`, `Shared Peptides` and `Number of Unique Peptides` change meaning**: from
  database-level to protein-group-level. Stored output from before and after differ in those three columns only, so
  record the MetaMorpheus version with them.
- **DATAREPO-D7 (ask):** do you convert `Sequence` to ProForma, or key anything on it? **Our recommendation:** keep the
  string as written and mark `|` rows as localization-ambiguous, rather than splitting them into several rows.

## The drafts

- **smith-chem-wisc/MetaMorpheus#2916 (labels).**
  - A peptide is unique to a protein group when no other group of the search lists it. Calmodulin's group
    (P0DP23|P0DP24|P0DP25) then shows its peptides as unique.
  - Parsimony, the protein list and the groups are unchanged; only `Unique Peptides`, `Shared Peptides` and `Number of
    Unique Peptides` move.
  - On mzLib up to 1.0.595 TMT values move too (PXD014145: 460 groups up, 12 newly valued), because that engine reads the
    set.
- **smith-chem-wisc/MetaMorpheus#2917 (label-free quant).**
  - Which PSMs: one base sequence, one mass, the same modifications at different sites, every candidate in one protein
    group.
  - How: quantified for that group, as one row per peptide and set of modifications. `Sequence` is every site, joined
    by `|`.
  - Left out in a file where an isomer was identified with its site: passing both made FlashLFQ zero both.
  - Threshold: the PSM-level q-value.
- **TMT:** trishorts/mzLib#14 (engine) and trishorts/MetaMorpheus#34 (on #30), after mzLib #1463. Same rule, no per-file
  part.

## Measured

- **Islet, MBR off, #2917 vs master:** identification identical; 858 new rows; 9 existing peptide values move. Of 2,999
  groups at 1%, 292 go up, 76 go down in some file (median polish), 8 gain a value and 1 loses its values. Of the
  user's 190 sequences seen only ambiguously, 135 are now quantified.
- **PXD014145, #34 vs #30:** +214 PSMs quantified, 155 new rows, no existing peptide row moves, 118 groups up.
- **Definitions:** DATA-DEFINITIONS v3.14 is drafted (`DEF-PROT-UNIQUE`, and the `DEF-PEP-ROW` and `DEF-TMT-*`
  amendments). It is NOT in effect and is posted for real when the first of these ships.

## Ledger

| their item | us |
|---|---|
| none open | |
