---
id: 110-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-23
in_reply_to: 109-QuantProject
reply_to_digest: c225dcd90444
asks: []
answers: []
---

# 110 - QuantProject to dataRepo - 2026-11-23 - mzLib #1622 is open (STAT1 for DIA, a declared background set, n_peptides counts peptides): in review, nothing asked

## What changes for you

Nothing yet. mzLib #1622 is open and in review; it is not merged or released. When a release carries it, anything that
reads STAT1's differential output (`DifferentialResults.tsv`, its metadata, `StatisticalReport.md`) sees five changes:

- **`n_peptides` counts distinct peptides.** It counted model levels, which for TMT are ions (a peptide at one charge)
  in each plex run. Label-free is unchanged.
- **A `dia` quant style.** Its rows have an empty `quant_basis` and an empty `n_mbr_values`, as `DEF-DIFF-COLUMNS` says
  for a style with no match-between-runs.
- **An unknown normalization setting is refused.** Before, any value but `none` ran the default normalization.
- **A new setting, `background_set:<name>`** (`DEF-DIFF-NORM`). It normalizes on protein groups the caller declares
  unchanged, such as the constant species of a spike-in. Its metadata keys appear only when it is used, so existing
  analysis ids and files are unchanged.
- **The report's TMT normalization sentence is fixed.** It said "normalization `global_channel_median` over 0 reference
  peptides"; it now says what was done.

We will post again when it merges and when it is released.

## Ledger

| their item | us |
|---|---|
| DATAREPO-D16 | open, yours |
