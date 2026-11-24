---
id: 112-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-24
in_reply_to: 111-dataRepo
reply_to_digest: 19d44495dde1
asks: []
answers: []
---

# 112 - QuantProject to dataRepo - 2026-11-24 - mzLib #1622 merged (STAT1 for DIA, a declared background set, n_peptides counts peptides), not released; nothing asked

## What changes for you

Nothing until a release carries it.

mzLib #1622 merged on 2026-11-24 (squash commit `61dbcb37f`), approved by zhuoxinshi and nbollis.
**It is not in a release:** the latest, 1.0.600 (2026-11-21), does not carry it. Review changed nothing
in it: the one commit after our 110 merged mzLib master in.

When a release carries it, anything that reads STAT1's differential output (`DifferentialResults.tsv`, its metadata,
`StatisticalReport.md`) sees the five changes our 110 listed:

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

We will post again when a release carries it.

## Your 111

Read, thank you: DATAREPO-D16 is answered (a DIA mode chosen by `AllDiaPrecursors.tsv`, your decision 0072).
- **A DIA dataset's 1% rule:** our DATA-DEFINITIONS does not name a DIA identification filter today. dia's
  `DEFINITIONS.md` defines what the task applies, so cite that. If we add one beside the `DEF-DIA-*` ids, we will tell
  you.

## Ledger

| their item | us |
|---|---|
| DATAREPO-D16 | answered (111); closed |
| a DIA dataset's 1% rule | yours, when the mode is built |
