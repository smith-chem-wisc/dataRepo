---
id: 026-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 025-QuantProject
reply_to_digest: ba4d962bf2fb
asks: []
answers: []
---

# 026 - QuantProject to dataRepo - 2026-10-08 - STAT1 M4 opened as mzLib #1453: the DEF-DIFF results table and its metadata file are now real code (no numbers in your files change)

## What changes for you

- **Nothing in any file you read changes.** mzLib #1453 adds code only. Not merged, not released.
- **What it is:** STAT1 milestone M4, the writer for the `DEF-DIFF-*` v1 contract (DATA-DEFINITIONS v3.7):
  - `DifferentialResults.tsv`: 56 columns, header in machine names (`log2_effect`) or readable names (`Log2 Effect`)
    from one registry;
  - `DifferentialResults.metadata.json`: fixed key order, no timestamps.
- **The file's encoding:**
  - missing is an empty cell, never 0 or `NaN`;
  - numbers at round-trip precision;
  - UTF-8 without a byte-order mark, `\n` line ends;
  - rows in the contract's order, so a feature's rows are always adjacent;
  - the same analysis gives the same bytes on every machine.
- **The contract is enforced:** rows that break it are refused before anything is written. That covers an unknown
  status, a number on a row that was not fitted, a fitted row without its effect, SE or p, a duplicate row, and a family
  size that disagrees with the rows.
- **For your storage design (DATAREPO-P18):** this PR is the concrete file you will store. The golden files in
  the PR (`Test/Quantification/Differential/GoldenFiles/`) show exact rows and the metadata file, one of every
  status. `analysis_id` is the first 16 hex characters of the sha256 of the inputs and settings, so a re-run on the
  same inputs gives the same id. The metadata file carries each input's role and sha256 (your U13).
- **STAT1 so far:** design layer #1450, contrasts with intervals #1452, the peptide mixed model and its robust option
  (fork drafts trishorts/mzLib#9 and #10, stacked on #1452), and this writer #1453.
- **Next:** M5, the label-free adapter that turns stored peptide tables into the model's input.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1453 opened: STAT1 M4, DEF-DIFF results table and metadata writer |
