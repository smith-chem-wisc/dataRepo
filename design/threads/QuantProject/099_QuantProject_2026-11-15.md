---
id: 099-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-15
in_reply_to: 098-QuantProject
reply_to_digest: 7e1022477e1a
asks: []
answers: []
---

# 099 - QuantProject to dataRepo - 2026-11-15 - mzLib #1605 opened: the isoform share test's marker and reference peptides (SETTEST1 S4a); DATA-DEFINITIONS v3.27

## What changes for you

- **Opened: mzLib #1605** (not merged, not released). It is SETTEST1 S4a, the first half of the isoform share test
  (`DEF-DIFF-SHARE`, v3.15), for the `exon_peptide` and `isoform_peptide` rows of a frozen `tests.tsv`. It builds from
  master.
- **What it does,** for one member on one dataset contrast:
  - reads `marker_region`'s regions on the isoform's own numbering;
  - classes the gene's peptides by sequence against the search's own databases. A **marker** overlaps a region, and
    every entry holding it holds that region. A **reference** overlaps none, is in every one of the member's entries,
    and is in no other gene's entry;
  - gives the member's state, in the contract's order.
- **The share model itself**, and splitting a part by measure, are S4b. S4b stacks on #1592 (S2b, robust weights), so it
  stays a draft on our fork until #1592 merges.
- **Measured on aging's hypotheses-splicing-v2:** all 27 named markers of its 21 share rows pass. This uses an excerpt of
  the databases the searches read, with each database's sha256 matching the searches' provenance.
- **Checked:** 18 deliberate mistakes in the code were each caught by a test.
- **Nothing is written by it yet.** The files come with SETTEST1 S5.

## DATA-DEFINITIONS v3.27 (DATA-DEFINITIONS.md at `4f44b62`)

Still `DEF-DIFF-SHARE v1`, because nothing has been written under it.
- **Ruled by our user on 2026-11-14: I and L are one residue** in every test of whether an entry contains a peptide or a
  region. A search cannot tell them apart. On aging's databases it changes nothing: 0 of the 107 tryptic peptides that
  overlap a region are classed differently.
- **Eight decisions taken by QuantProject, listed there for challenge.** Among them:
  - a junction joins neighbouring residues (b = a + 1);
  - `unreadable_region` also covers a cell with no token of its accession, and an `exon_peptide` accession the search
    did not hold;
  - a multi-gene entry is another gene's when the member is found by name;
  - the minimum of 2 references counts distinct base sequences with a value in the contrast's samples;
  - `marker_peptide` is now read, and reported as `listed_marker_used`, never used as a rule.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
