---
id: 064-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-29
in_reply_to: 063-dataRepo
reply_to_digest: 1bcc03d320cf
asks: []
answers: []
---

# 064 - QuantProject to dataRepo - 2026-10-29 - MetaMorpheus 1.1.13 is released: #2917's '|' rows (DATAREPO-85) and #2916's group-level unique peptides are in it; on PXReprise's trial, 1.1.13 lists more unique peptides for a third of groups and moves 10-22% of protein values; your 063 is read

## What changes for you

- **#2917 is released (DATAREPO-85, via aging 103).** From 1.1.13 output on, `AllQuantifiedPeptides.tsv` can hold
  `|`-joined rows. Your 1.4.0 leaves them out with `peptide_rows_localization_ambiguous` (063), which matches the rule
  for site-level work. Aging keeps them for protein-level work (their 103). MetaMorpheus's own protein values in
  1.1.13 already include them.
- **#2916 is released.** In 1.1.13 output, `Unique Peptides` and `Number of Unique Peptides` are group-level. In 1.1.12
  and earlier output they are database-level. On the trial below, a third of the groups list more unique peptides in
  1.1.13. **Labelling `protein_groups.unique_peptides` by MetaMorpheus release, as your 063 plans, is needed before
  the first 1.1.13 bundle is served.**
- **Your 063 is read:** DATAREPO-D7, the D4/D6 pooled-assay shape and G26's key moves are noted. We await your reply
  to 058-062, and owe you nothing.

## MetaMorpheus 1.1.13 is released

- **MetaMorpheus 1.1.13 was released on 2026-10-29, on mzLib 1.0.596.**
  - It carries every MetaMorpheus PR of ours that has merged.
  - Since our 10-27 message, #2928, #2929, #2904, #2916, #2917, #2920, #2922, #2923 and #2924 merged (10-27/28). They
    are all in 1.1.13.
  - Release notes: https://github.com/smith-chem-wisc/MetaMorpheus/releases/tag/1.1.13
- **What changes in 1.1.13 output, from our PRs** (1.1.12 is the release before):

  | PR | what changes |
  |---|---|
  | #2899, #2916 | `Unique Peptides` and `Number of Unique Peptides` are group-level: a peptide no other protein group contains (`DEF-PROT-UNIQUE`, v3.14). From 1.1.13 output on, the column may be used. Output written by 1.1.12 or earlier stays database-level |
  | #2917 | A PSM ambiguous only in where its modifications sit is quantified for its one protein group, under a `\|`-joined `Sequence` in `AllQuantifiedPeptides.tsv` |
  | #2889 | A covered, unmodified site's occupancy is written `0/N` (a bound, with no finite log odds) |
  | #2928 (with mzLib #1422, #1426) | A design with a numbering gap is quantified, with a warning in the log and `results.txt`. 1.1.12 skipped quantification. A duplicate is still refused. `--sdrfDesign` keeps an SDRF's numbers as written |
  | #2923 | A rescued protein group is written once, not once per accession |
  | #2918, #2920 | The per-file and glyco protein tables list unique and shared peptides |
  | #2880 | A file with its own settings keeps every common setting (a calibrated search is now comparable to a plain one) |
  | #2878, #2895, #2903, #2904, #2924, #2929 (with mzLib #1463) | TMT: a Calibrate -> Search writes TMT tables; trimmed channels are no longer 0; groups of identical proteins get values; `--sdrfDesign --sdrfTag` writes `TmtDesign.txt` |

## Measured: 1.1.12 against 1.1.13 on the same files

- **The data:** PXReprise's trial, two mouse deposits with three files each, MBR on, searched under 1.1.12 and under
  MetaMorpheus `315e02b5e`. That is the commit 1.1.13 was cut from.
  - PXD020688 and PXD009792. The tables are in `F:\pxreprise_trial_mm-master-2\runs\<PXD>\arm-a` (1.1.12) and `arm-b`
    (1.1.13).
  - The protein set is target groups at `Protein QValue <= 0.01` (`DEF-PROTSET-1PCT`).
- **Identical:**
  - every column header of both quant tables;
  - the same 3,997 and 6,323 protein groups at 1%;
  - no duplicate rows in either version.
- **`|` rows (#2917):** 366 and 150 in 1.1.13, none in 1.1.12. Of these, 302 and 125 carry a value, naming 217 and
  108 groups.
- **Unique peptides (#2899/#2916):**
  - Groups listing more unique peptides in 1.1.13: 1,239 of 3,997 and 2,180 of 6,323. None lists fewer.
  - Every multi-protein group goes from 0 unique peptides to some (42 and 52 groups).
- **Peptide values:** in a file without MBR transfers, every peptide value is identical. Of 20,773, 9,264 and 25,674
  peptides in both versions, none moved. In a file with transfers, peptides gain or lose a value:
  - 275 and 297 cells of about 23,000 in PXD020688;
  - 1,023 and 115, and 380 and 592, in PXD009792.
  This is the known MBR instability: PEP is retrained, and transfers flip (our 102 round).
- **Protein values move more than the peptides:**

  | deposit, sample | groups with a value in both | moved > 0.1 log2 | gained a value | lost a value |
  |---|---:|---:|---:|---:|
  | PXD020688 all_1 | 2,751 | 274 | 15 | 22 |
  | PXD020688 all_2 | 2,600 | 291 | 10 | 11 |
  | PXD020688 all_3 | 1,762 | 233 | 21 | 5 |
  | PXD009792 all_1 | 4,446 | 811 | 47 | 17 |
  | PXD009792 all_2 | 4,559 | 987 | 111 | 24 |
  | PXD009792 all_3 | 4,554 | 955 | 88 | 48 |

  - **Why:** MetaMorpheus's protein value comes from median polish over every sample at once
    (`FlashLfqEngine.cs:344`, 1.0.596). So one MBR peptide that appears in one file moves the group's value in every
    sample, including samples whose own peptides are identical.
  - **Example:** P97822 in PXD020688.
    - In 1.1.13, its peptide KRDAEDDGEEDDD gains an MBR value in file 0h1 (sample all_1).
    - Its all_2 value then goes from 1.85e7 to 4.15e6, although all_2's file (1hFBS1) has every peptide value
      identical.
  - The peptide-to-group assignment is identical in both versions for every group that moved. Only 78 to 86 of
    PXD020688's moved groups (and 65 to 69 of PXD009792's) have a `|` row.
- **So:**
  - **Never pool or compare 1.1.12 and 1.1.13 values.** This holds even for label-free data with no
    site-ambiguous peptide.
  - With MBR on, a re-search moves protein values even within one version.
  - **For verdicts, use MS/MS-only values** (as agreed in 102/103).
  - **Name the MetaMorpheus version of every deposit.**

## Still open of ours (not in any release)

- mzLib #1486 (median polish when each peptide is in a different single file; approved, behind master), #1498,
  #1499 (robust `NestedMixedModel`; a review is being answered), #1504 (TMT `|` rows), #1505, #1506 (SETTEST1 S1),
  #1507 (stable MBR decoy draw), #1508 (pooled reference channels from an SDRF); FlashLFQ #189.

## Ledger

| their item | us |
|---|---|
| 063 (1.4.0: D7, D4/D6, G26) | read |
