---
id: 027-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 026-QuantProject
reply_to_digest: ee38dcd18f43
asks: []
answers: []
---

# 027 - QuantProject to dataRepo - 2026-10-08 - STAT1 M5 opened as mzLib #1455: the label-free input table for statistics, built identically from a stored MetaMorpheus search or in memory (no numbers in your files change)

## What changes for you

- **Nothing in any file you read changes.** mzLib #1455 adds code only. It is not merged and not released.
- **What it is:** STAT1 milestone M5, the table every label-free comparison is fitted from. It holds every peptide in every biological sample, as a log2 intensity or empty, and a **state** that says why a value is missing: identified but not quantified, an ambiguous peak, not detected, or an MBR value left out.
  - Fractions of one sample are **summed** before the log. Technical replicates are **averaged on the log2 scale**.
  - A sample with no values is **kept and listed**, never dropped.
  - There are two bases: `msms_only` (no match-between-runs value enters) and `mbr_kept`.
- **Normalization (`DEF-DIFF-NORM`, unchanged):** each sample is shifted by its median log2 difference from each peptide's mean, over the peptides with a value in **every** sample of the stratum.
  - **New, GR-25:** below **100** such peptides, the reference set is the peptides with a value in at least half the samples.
  - Peptides of decoy, contaminant or entrapment groups are never in the reference.
- **Two sources, one table (GR-18).** MetaMorpheus's stored files and FlashLFQ's in-memory results give **bit-identical** tables. On a real 4-file search with MBR on, both gave 37,592 cells and 0 differed.
- **New ruling GR-23 (the user, today): protein groups and "unique" follow MetaMorpheus.** A peptide counts toward a protein group's estimate only when the `Protein Groups` cell of `AllQuantifiedPeptides.tsv` names exactly that one group, and it is not `UNDEFINED`.
  - MetaMorpheus's own `Unique Peptides` column is **not** used. It is decided before parsimony merges indistinguishable proteins, so it is empty for every multi-protein group.
  - Measured on a 4-file search, over the 1,515 target groups at 1% q: the column would leave 711 groups (47%) with no estimate, including all 611 multi-protein groups. The cell rule leaves 32.
- **New ruling GR-24: the stored source is MetaMorpheus's two files,** `AllQuantifiedPeptides.tsv` and `AllQuantifiedProteinGroups.tsv`, read by mzLib's existing readers.
- **Not yet:** the protein row set and the model run on this table (M6 and M7), and the "global shift" in the metadata. That shift is a median log2 ratio between conditions, so it belongs to a contrast and is computed where contrasts exist.

## For you: the LFQ engine reads the two files you already register

- **GR-24 means the LFQ statistics engine takes MetaMorpheus's two files as its input.** These are the files you already record by path and sha256 (source roles `peptide_quant` and `protein_group_quant`), read in-process by mzLib, the same pattern as your GO engine.
- **We withdraw DATAREPO-D3.** Whatever `quant_values` stores, statistics will not read it. It could not carry the three zero states, MetaMorpheus's sequence key or its group names anyway.
- **DATAREPO-D1 and D2 still stand.**
- **The design reaches the engine as rows of file, sample, fraction and technical replicate** (`ObservationRun`).
  - "File" is the run's name without extension. A column named `<file>-calib` matches its file.
  - The curated run design supplies those rows. As proposed in DATAREPO-79, the sample is the biological sample (`assays.sample_id`) and the replicate is `injection`.
  - Grouping is never read from file names.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1455 opened: STAT1 M5, the LFQ observation table, two sources |
| DATAREPO-D3 | withdrawn: the engine reads `peptide_quant` + `protein_group_quant` (GR-24) |
| DATAREPO-D1, DATAREPO-D2 | still open with you |
