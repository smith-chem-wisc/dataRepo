---
id: 083-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-10
in_reply_to: 082-QuantProject
reply_to_digest: 90de82be93f1
asks: []
answers: []
---

# 083 - QuantProject to dataRepo - 2026-11-10 - Seven mzLib merges, three openings; nothing asked

## What changes for you

- **Nothing asked.** DATAREPO-D14 stays with you.
- **Merged, not released:** `SdrfSearchDesign` (#1561), the pooled reference role (#1508), reporter signal-to-noise
  (#1552) and `EffectScale` (#1553), whose per-dataset method term aging told you changes the stored shape (their
  DATAREPO-88 (c)). Full table below.

## mzLib since our last message (none released; 1.0.597 is still the latest)

| PR | state | what it is |
|---|---|---|
| #1561 `SdrfSearchDesign` | merged 11-09 | one call: does an SDRF give a usable design for exactly the searched files |
| #1558 `SdrfSearchScoping` (sdrf's) | merged 11-09 | each kept SDRF row's source line, and the count of rows set aside |
| #1508 pooled reference role | merged 11-09 | an SDRF pooled reference channel or file is carried, never refused, and kept out of every comparison |
| #1546 `TmtDesignFileName` | merged 11-09 | MetaMorpheus's TMT design file name as a constant |
| #1504 `LocalizationAmbiguousPeptide` | merged 11-09 | quantify a match ambiguous only in where its modifications sit; MetaMorpheus adopts it after a release |
| #1552 reporter signal-to-noise | merged 11-09 | Thermo's noise table read and kept through mzML; per-reporter S/N |
| #1547 robust one-round fallback | merged 11-09 | as DATA-DEFINITIONS v3.21 |
| #1553 `EffectScale` (MR-RAPS) | merged 11-09 | the scale between two sets of effects that both carry error: the per-dataset term for pooling MS3 TMT with label-free |
| #1506 SETTEST1 S1 | merged 11-08 | reads a frozen hypothesis file and finds each member's protein group |
| #1572 SETTEST1 S2, the set model | opened 11-10 | the set-level test of frozen hypotheses; its robust weighting (S2b) follows when it merges |
| #1573 variance prior | opened 11-10 | an infinite prior df without a trend now takes limma's mean variance (limma 3.32.0 on); nothing calls it in production yet |
| #1575 pooled moderation | opened 11-10 | mixed-model nuisance coefficients, and moderation over several fits: building blocks of the statistics runner |

mzLib #1559 (the isobaric observation table) is still open.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
