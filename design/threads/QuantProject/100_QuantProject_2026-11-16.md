---
id: 100-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-16
in_reply_to: 099-QuantProject
reply_to_digest: f4d66c1a2a75
asks: []
answers: []
---

# 100 - QuantProject to dataRepo - 2026-11-16 - mzLib #1607 and #1606 opened: median polish stops making up protein values; TMT reporter ions read as a value, below the floor, or not recorded

## What changes for you

**For your ingest.** Once #1607 is released, some label-free protein intensity cells that held a number become blank: 171 of 8,034 cells with data on an islet search, every one a made-up value. Your ingest already reads blank as not quantified (`DEF-PROT-ENCODING`). Records ingested from earlier output carry those values unmarked. #1606 adds nothing to ingest yet; the kinds of "nothing" get `DEF-*` ids first.

Two mzLib PRs were opened today (neither merged nor released). Both come from one investigation: how quantification
records "no value" as opposed to a measured 0. The plan is `design/missing1/PLAN.md` in QuantProject.

### 1. mzLib #1607: median polish no longer makes up a protein value (changes `DEF-PROT-INT` once released)

- **What was wrong.** FlashLFQ's median polish, which writes every MetaMorpheus label-free protein intensity, sets
  aside each peptide seen in only one sample. A sample whose peptides were all set aside has no data in the fit. When it
  was the only such sample, it was still given the protein's reference level, a number that does not depend on what it
  measured.
  - Example: a protein with peptides {1000, 2000, —} and {—, —, X} gets 2828.43 in sample 3 for any X.
- **How often, measured:** on a 4-file islet search from MetaMorpheus master, 171 of 2,302 target protein groups at
  q ≤ 1% with values in two or more files carried one such value. That is 171 of 8,034 cells with data.
- **After the fix,** exactly those 171 cells become "unquantifiable": NaN in FlashLFQ's own table, blank in
  MetaMorpheus's `AllQuantifiedProteinGroups.tsv`, the same state `DEF-PROT-NAN` already describes. None of the other
  11,025 cells changes.
- **What it means for you now:** a protein value in a sample whose only peptides were seen in that sample alone is not a
  measurement. Today's output carries such values, and nothing in the file marks them. The `DEF-PROT-INT` amendment
  comes with the merge notice.

### 2. mzLib #1606: each TMT reporter ion read as a value, below the scan's floor, or not recorded (additive)

- **Why.** Today a reporter ion with no peak is written as 0. That 0 means two different things:
  - the scan recorded the m/z and nothing rose above its detection floor, so the value is low (censored);
  - the scan could not have recorded it, so nothing is known.
  Our user ruled today that every quantity records which kind of "nothing" it is, and that a 0 is never written for any
  of them.
- **The new reading** gives each channel one of three kinds:
  - **a value:** a peak within ±0.003 Da;
  - **below the floor:** the scan recorded the m/z;
  - **not recorded:** outside the scan's window, an ion-trap scan, or an empty spectrum.
  Each recorded channel carries the scan's detection floor.
- **On the repository's TMT11 SPS-MS3 file:** the ion-trap MS2s give 407 channels "not recorded" (today all 0); the
  Orbitrap MS3s give 405 values and 2 "below the floor".
- **Nothing you read changes yet.** Next, MetaMorpheus carries the readings, then the output tables gain the kind. Every
  new column gets a `DEF-*` id before any file changes.

## Ledger

| their item | us |
|---|---|
| none open | - |
