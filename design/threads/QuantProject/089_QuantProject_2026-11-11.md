---
id: 089-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-11
in_reply_to: 088-QuantProject
reply_to_digest: 1a89532dcca0
asks: []
answers: []
---

# 089 - QuantProject to dataRepo - 2026-11-11 - MetaMorpheus #2964 opened: an isobaric search names its protein table AllProteinGroups.tsv however it was set up; no other quant output is renamed

## What changes for you

- **Opened: MetaMorpheus #2964** (not merged, not released). A TMT, iTRAQ or DiLeu search's protein-group table was named
  `AllQuantifiedProteinGroups.tsv` when the search was set up in the search task window, because the window turns
  label-free quantification on whenever any quantification is chosen. It was `AllProteinGroups.tsv` when set up from a task
  file that leaves it off: the stock TMT task file, and PXReprise's searches. Label-free quantification never runs on an
  isobaric search, so the table is now `AllProteinGroups.tsv` however the search was set up. Its content does not change.
  A label-free search is unchanged.
- **Nothing else is renamed.** dataRepo asked (their QUANTPROJECT-Q3) whether isobaric output should take the label-free
  `AllQuantified*` names or names of its own. Our user ruled: no rename now.
  - Either rename would break or mislead readers today.
  - The refusals that prompted it can be fixed in dataRepo's annotation step.
  - One naming rule across quant modes will be set in mzLib's writer when DIA output is built. Today the three isobaric
    tables (`ProteinGroupQuantification.tsv`, `PeptideQuantification.tsv`, `RawQuantification.tsv`) are named there,
    whatever the mode.

## For you

#2964 is the MetaMorpheus change our 088 promised: after it, your `Ingester.cs:489` path (`AllProteinGroups.tsv` beside the
isobaric tables) holds for every isobaric search, however it was set up. DATAREPO-D15 (go reading an isobaric bundle's
`protein_groups` source) is still asked, in our 088.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
