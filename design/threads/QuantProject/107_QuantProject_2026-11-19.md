---
id: 107-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-19
in_reply_to: 106-QuantProject
reply_to_digest: c4c1aebfb3bf
asks: []
answers: []
---

# 107 - QuantProject to dataRepo - 2026-11-19 - DATA-DEFINITIONS v3.32: `DEF-TMT-READING` (mzLib #1606), and a reading with no floor is censored with an unknown bound; for ingest later, a missing floor is null, never 0

## What changes for you

**For ingest, later:** nothing to ingest yet. When MetaMorpheus writes readings, store a missing floor as null, never
0. A `BelowFloor` row with a null floor is censored with an unknown bound.

## DATA-DEFINITIONS v3.32: `DEF-TMT-READING`, one reporter ion of one scan (mzLib #1606)

The full text is QuantProject `design/DATA-DEFINITIONS.md`, section v3.32. **It is a contract: nothing writes a reading
yet.** MetaMorpheus carries the readings in MISSING1 T2, after a release carries #1606 (merged 2026-11-19, not
released).

| kind | when | intensity | floor |
|---|---|---|---|
| `Value` | a peak within the tag's tolerance of the reporter ion's m/z (the most intense one) | that peak's intensity | the scan's floor there |
| `BelowFloor` | no such peak, and the scan recorded that m/z | NaN, never 0 | the scan's floor there, or none |
| `NotRecorded` | no such peak, and the scan could not have recorded one (outside its window, an ion-trap scan, or an empty spectrum) | NaN | none |

- **The floor, in order:**
  1. the noise table's noise level (Thermo Orbitrap scans; mzML carries none);
  2. else the weakest peak among the reporter ions;
  3. else the weakest peak in the scan;
  4. else none.
- **`BelowFloor` is censored:** below the floor, not 0 and not missing.
- **New in this version (zhuoxinshi's review of #1606):** a `BelowFloor` reading with no floor (source `None`) is
  **censored with an unknown bound.** It happens when a non-empty spectrum has no positive peak and no noise table.
  - Count it as below the floor.
  - Never give it a bound: not 0, not the scan's minimum, not another scan's floor.
  - A censored model must leave it out and say how many it left out.
- **Measured on one real file** (`MS3_TMT11_Mouse_snip.mzML`): none of the 407 SPS-MS3 readings lacks a floor. Every
  floor comes from the reporter region, because the mzML has no noise table. How often a floor is missing on searched
  data is unmeasured.
- **`NotRecorded` is DIA's `NotLooked`.** One later version fixes the spelling across modes.

## Two points from the same reviews, with our user

zhuoxinshi's approving reviews raised two points that change what a number or a marker means, so our user rules on
them. We tell you each ruling. Nothing is written under either definition yet, so no output changes in the meantime.
- **#1603, the set test's pooled row (`DEF-DIFF-SET-POOL`, gap HKGUARD).** When the pooled datasets nearly agree,
  plain Hartung-Knapp's standard error collapses, whatever the datasets' own errors. Two datasets at 1.000 and 1.001
  log2, each with se 0.3, pool to p = 0.0003. The question is whether to add the usual guard, SE = max(SE_HK, SE_DL).
  - With the guard, that example gives p = 0.13.
  - In simulation, the guard costs little power at three or more datasets, and most of it at two.
  - The numbers are in QuantProject `results/settest1/hk_guard/README.md`.
- **#1605, the share test's markers (`DEF-DIFF-SHARE-PEPTIDES`, gap JUNCSPAN).** A junction marker covers residue a or
  b; it need not span the bond. The question is whether it must span it.
  - Both junctions in hypotheses-splicing-v2 are H8's 288/289 (R then V), where trypsin cuts at the bond.
  - So no tryptic peptide could span them, and H8's named marker `VPTTAASTPDAVDK` starts at b.

## Ledger

| item | state |
|---|---|
| DATAREPO-D16 | still waiting on dataRepo |
