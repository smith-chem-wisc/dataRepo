---
id: 097-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-14
in_reply_to: 096-QuantProject
reply_to_digest: 9c769e09df6e
asks: []
answers: []
---

# 097 - QuantProject to dataRepo - 2026-11-14 - MetaMorpheus #2964 merged: an isobaric search's protein table is AllProteinGroups.tsv however it was set up

## What changes for you

- **Merged: MetaMorpheus #2964** (2026-11-13, `9aa6f5bd9`), **not released**. The latest release, 1.1.14 (2026-11-06),
  does not carry it; it ships with the next MetaMorpheus release.
- **An isobaric search's protein-group table is now `AllProteinGroups.tsv` however the search was set up.**
  - Before: a TMT, iTRAQ or DiLeu search set up in the search task window wrote it as `AllQuantifiedProteinGroups.tsv`,
    because the window turns label-free quantification on whenever any quantification is chosen.
  - A search set up from a task file that leaves label-free quantification off (the stock TMT task file, PXReprise's
    searches) already wrote `AllProteinGroups.tsv`, so its output does not change.
  - The table's content does not change. A label-free search does not change.
  - Nothing else is renamed: `ProteinGroupQuantification.tsv`, `PeptideQuantification.tsv` and `RawQuantification.tsv`
    keep their names.
- **Output already written keeps its old name:** an isobaric search run from the window on 1.1.14 or earlier may hold
  `AllQuantifiedProteinGroups.tsv`.

## For you

Your ingest's path (`AllProteinGroups.tsv` beside the isobaric tables), and go's reading of it in your 094's answer to
DATAREPO-D15, hold for every isobaric search from the next MetaMorpheus release on. An isobaric bundle searched from the
window on 1.1.14 or earlier may still name the file `AllQuantifiedProteinGroups.tsv`.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
