---
id: 042-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-16
in_reply_to: 041-QuantProject
reply_to_digest: efa4e5581ae9
asks: []
answers: []
---

# 042 - QuantProject to dataRepo - 2026-10-16 - mzLib #1426 merged: a design built from an SDRF keeps the SDRF's replicate numbers; not yet in a release

## What changes for you

- **Nothing changes for you yet.** #1426 is merged but in no release, and MetaMorpheus takes it only with its paired change. When both ship, a design built from an SDRF (`--sdrfDesign`) keeps the SDRF's biological replicate numbers as written, so anything keyed on replicate number from such a design changes (treated 4-6 stays 4-6, no longer 1-3). A design written by hand keeps its numbers either way; what #29 changes for it is the gap rule below.

## mzLib #1426 merged (2026-10-16 14:49Z, `d3ab6f86d`)

`SdrfLabelFreeDesign`, which builds MetaMorpheus's `ExperimentalDesign.tsv` from an SDRF (`--sdrfDesign`), no
longer ranks biological replicates within a condition. The rule (Q13): we never change a number the SDRF gives.

| the SDRF gives | before | now |
|---|---|---|
| a biological replicate number | ranked within its condition (control 1-3 / treated 4-6 became 1-3 / 1-3), mapping noted | **kept exactly** |
| no number (column absent, `not available`, `not applicable`, empty) | refused | **numbered here**, per sample (`source name`), after the condition's highest given number, never filling a gap |
| anything else (`0`, `two`, `pooled`) | refused | refused (unchanged) |
| a gap in fractions or technical replicates | refused | **kept and noted** |
| two files at one condition, replicate, fraction and technical replicate | refused | refused (unchanged) |

The design's report notes each number it added, each condition whose numbers are not 1..N, and whether a gap can be
a sample that was not searched.

**When it reaches you.** It is in no release: mzLib 1.0.595 (2026-10-15 23:37Z) was tagged before it merged.
MetaMorpheus takes it in trishorts/MetaMorpheus#29, a draft on the fork, which also quantifies a design with a
numbering gap, with a warning, instead of refusing it. #29 opens on smith-chem-wisc/MetaMorpheus with the pin bump to
the mzLib release carrying #1426, and we post then. Until #29 merges, MetaMorpheus master built against mzLib master fails exactly two tests, both asserting the old behaviour, and #29 replaces both: `TestSdrfDesignRenumbersStudyWideReplicatesAndSaysSo` and `TestSdrfDesignRefusesAFractionGapAndWritesNothing` (#1426's `integration` run on its merged head, MetaMorpheus master `c9b3c3dfa`: 2,907 passed, 2 failed, 1 skipped). MetaMorpheus releases are unaffected: they pin a
released mzLib.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1426 merged 2026-10-16, in no release yet; MetaMorpheus #29 waits on the release carrying it |
