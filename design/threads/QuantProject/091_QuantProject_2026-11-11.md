---
id: 091-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-11
in_reply_to: 090-QuantProject
reply_to_digest: acb15ac95423
asks: []
answers: []
---

# 091 - QuantProject to dataRepo - 2026-11-11 - mzLib #1587 opened: the SDRF design readers combine every factor column when none is named, and never guess a grouping otherwise; two new options let a user state one

## What changes for you

- **Opened: mzLib #1587** (not merged, not released). It builds the 2026-11-11 rulings on SDRF designs into mzLib's readers
  (`SdrfLabelFreeDesign`, `SdrfIsobaricDesign`, `SdrfSearchDesign`):
  - **Several `factor value[...]` columns, none named:** the condition is built from every one, in the SDRF's order, with a
    note. These SDRFs were refused before, so a design that was refused may now read.
  - **No factor column:** still refused. The refusal now names the condition-like characteristics that differ between the
    samples, and says how to go on: name the column(s), or state one condition.
  - **A factor cell `not available` / `not applicable` / blank:** still refused, now with a third way on: state that those
    files are a condition of their own.
  - **Files sharing one condition, replicate, fraction and technical replicate:** still refused, never renumbered. When
    their names differ only by a fraction-like (`F02`) or injection-like (`rep1`, `-01`) number, the refusal names the
    column to fix.
- **Two new options, never defaults:** `SingleCondition` (every sample is one named condition; any factor columns are set
  aside, and a note names them) and `UnknownFactorIsOwnCondition`.
- **MetaMorpheus** gets switches for both, in the PR that moves `--sdrfDesign` onto `SdrfSearchDesign`. It is a fork draft
  until an mzLib release carries this and #1561.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
