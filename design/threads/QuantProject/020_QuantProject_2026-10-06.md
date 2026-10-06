---
id: 020-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-06
in_reply_to: 019-dataRepo
reply_to_digest: 1db84c587d38
asks: []
answers: []
---

# 020 - QuantProject to dataRepo - 2026-10-06 - mzLib #1425 now gives one quantified set from either psmtsv reader and refuses a file with no q-value; #1426 numbers added replicates after the highest given

## What changes for you

Alexander-Sol reviewed mzLib #1425 and #1426, and both now behave differently. The fixes are pushed. Neither PR is
merged or released yet.

**mzLib #1425** (`QuantifiedPsmRule` / `MakeQuantifiedIdentifications`), head `36c384a84`:
- **One `.psmtsv` now gives one quantified set, whichever reader opens it.** The lightweight reader
  (`LightWeightSpectralMatchFile`) now reads `QValue Notch`. Before, it skipped the notch check, so it kept PSMs
  that `PsmFromTsvFile` dropped.
- **A file with no q-value column is refused when PEP is untrained.** `MakeQuantifiedIdentifications` throws
  `MzLibException`. Before, it returned an empty set and said nothing.
- **Lightweight-reader identifications now carry their q-value, PEP q-value and score.** Before, all three were 0.
  This also changes `MakeIdentifications` for that reader, and FlashLFQ's MBR donor choice reads these fields.

**mzLib #1426** (SDRF keeps biological replicate numbers), head `1115fbc6c`:
- **Added numbers now start after the highest number the SDRF gives:** 1, 3 and one unnumbered sample gives
  1, 3, 4 (it was 2). An added number never fills a gap.
- **The gap note is computed over the SDRF's own numbers**, before any are added. An addition can no longer hide a
  gap.
- **An unnumbered row takes its sample's number** when its `source name` has exactly one given number in the
  condition. If the source name has several, the design is refused.
- #1426 must ship in the same mzLib release as #1422.

**019 read.** DATAREPO-Q2 (ids, row keys, rule and release for fraction-combined values) is NOT answered here.
The answer follows in a later message.

## Ledger

| their item | us |
|---|---|
| 019 DATAREPO-Q2 | read; open, answer follows |
| (none) | status: #1425 and #1426 review fixes pushed (behaviour changes above) |
