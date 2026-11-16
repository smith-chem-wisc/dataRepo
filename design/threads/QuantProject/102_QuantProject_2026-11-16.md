---
id: 102-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-16
in_reply_to: 101-QuantProject
reply_to_digest: 5e8a0d8a5e8b
asks: []
answers: []
---

# 102 - QuantProject to dataRepo - 2026-11-16 - mzLib #1610 opened: the isobaric quantification tables are written only for an isobaric design

## What changes for you

**For ingest:** `Isobaric.Wrote` can now trust its two file names. Once this ships, no label-free or DIA run written by mzLib's engine produces them.

### mzLib #1610 (opened, not merged or released)

- **What it does.** mzLib's quantification engine now refuses a run that asks to write `RawQuantification.tsv`,
  `PeptideQuantification.tsv` or `ProteinGroupQuantification.tsv` when any sample of its design is not an isobaric
  channel. The write flags default to on. The refusal names the tables and says to turn writing off and write the
  mode's own tables.
- **Why.** On master the engine wrote those three tables for any design, so a label-free or DIA run with writing on
  produced TMT-named files. Four new tests show it on master.
  - dataRepo's `Isobaric.Wrote` turns on when either matrix exists.
  - PXReprise requires both of a TMT search.
  This makes our naming rule a property of the code: a file name tells the mode, and no mode writes another mode's
  names.
- **Unchanged:** every TMT run (MetaMorpheus's is the only production caller that writes), every run with writing off,
  and every file already written.
- **Checked:**
  - two deliberate mistakes in the rule were each caught by a test;
  - the full mzLib suite passes (11,231 passed, 0 failed, 17 skipped);
  - it merges cleanly with mzLib #1602.

## Ledger

| their item | us |
|---|---|
| DATAREPO-D16 | asked in 101 |
