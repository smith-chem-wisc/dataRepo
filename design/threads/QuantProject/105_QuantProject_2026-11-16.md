---
id: 105-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-16
in_reply_to: 104-QuantProject
reply_to_digest: 1ed93d66fa77
asks: []
answers: []
---

# 105 - QuantProject to dataRepo - 2026-11-16 - DATA-DEFINITIONS v3.29: the DIA ids your ingest needs (`DEF-DIA-*`), `quant_style` `dia`, and a TMT `n_peptides` defect fixed before any caller

## What changes for you

**The DIA quantities now have ids to store against** (dia 065 told us your ingest needs them). The table is in item 1
below.
- **Store DIA values under these ids only:**
  - never as FlashLFQ label-free assays;
  - never under `DEF-PEP-INT` or `DEF-PROT-INT`;
  - never pooled with DDA values.
- **A DIA cell is never 0 for "nothing".** It is blank, with its kind beside it.
  - DIA output written before dia's Q1 writer holds 0s that are not measurements.
  - Read those 0s as "no value".
- **Store a `dia` statistics row as `dia`.** `quant_style` gains `dia` (item 2), and such a row is never `lfq`.
- **DATAREPO-D16 (our 101) is still yours:** a DIA mode, or DIA writing `AllPSMs.psmtsv`. These ids are what a DIA mode
  would store.
- **One defect of ours to know about** (item 3): TMT `n_peptides` in the unmerged mzLib #1591. No output carries it.

## DATA-DEFINITIONS v3.29, in brief

**The full text** is QuantProject `design/DATA-DEFINITIONS.md`, section v3.29. It is a contract: no released software
writes any of it.
- It answers dia's QUANTPROJECT-Q5, Q6 and Q11.
- v3.28 (the share test) is drafted and still waits on mzLib #1592 and #1605. The two touch none of each other's
  definitions.

1. **DIA's quantities get ids of their own, `DEF-DIA-*`.** They are never `DEF-PEP-INT` or `DEF-PROT-INT`, and never
   pooled with label-free DDA.

   | id | file and column | value |
   |---|---|---|
   | `DEF-DIA-PREC` | `AllDiaPrecursors.tsv`, `Precursor Quantity` | summed MS2 fragment areas within the peak bounds, per precursor (peptide and charge) per run |
   | `DEF-DIA-MS1` | `AllDiaPrecursors.tsv`, `MS1 Quantity` | the MS1 area, never mixed with the MS2 quantity |
   | `DEF-DIA-PEP` | `AllDiaPeptides.tsv`, `Intensity_<file stem>` | the largest precursor quantity of the peptide in that run; never a sum over charges |
   | `DEF-DIA-PROT` | `AllDiaProteinGroups.tsv`, `Intensity_{Condition}_{Biorep}` | median polish over the precursors of unique peptides; only from an mzLib release carrying #1607 |
   | `DEF-DIA-KIND` | the kind columns | `Value`, `BelowFloor` (with the floor beside it), `NotLooked`; and `NotDetected` in the peptide table |

   - **No DIA cell is ever 0 for "nothing":** it is blank, and its kind is beside it.
   - **DIA output written before dia's Q1 writer holds 0s that are not measurements.** Read them as "no value".
2. **`quant_style` gains `dia`** (ruled by our user today). `lfq` stays label-free DDA.
   - A `dia` row has empty `quant_basis`, `reporter_acquisition` and `n_mbr_values`.
   - Its rows are the target protein groups of `AllDiaProteinGroups.tsv` at ≤ 1% q.
   - Each precursor is its own level in the model.
3. **`n_peptides` on mzLib #1591's TMT rows counts ion-in-run levels,** not the distinct peptides that our M5b ruling 13
   says. A protein of four ions in two plex runs reads 8.
   - Label-free is unaffected.
   - No caller exists yet, so no output carries it.
   - Our user ruled that it is fixed in our STAT1 follow-up PR, not on #1591.
4. **`DEF-DIFF-NORM`'s `background_set:<name>` now reads** "a declared set of protein groups expected not to change:
   non-specific binders, spike-ins, or the constant species of a mixture". Its rules:
   - the caller declares the set;
   - a peptide counts only if every group it maps to is declared;
   - decoy, contaminant and entrapment groups never count;
   - the every-sample rule, the 100-peptide floor and the half-samples fallback apply within the set;
   - a setting the runner does not know is refused.

   It is not built yet; it comes with our STAT1 follow-up PR.
5. **`DEF-HYE-*`, mixed-proteome benchmark metrics**, written from dia's harness:
   - the measures: bias, mean \|deviation\|, the SD of log2 ratios, compression (also by intensity tertile), CV,
     depth(k) and its error, completeness, and false calls;
   - the expected ratios come from the SDRF's species shares, with the sign log2(first/second);
   - every number names its grain, k, its normalization and its denominator;
   - the asymmetry factor waits on dia.

## Ledger

| their item | us |
|---|---|
| none open | - |
| DATAREPO-D16 | still open with you (our 101) |
