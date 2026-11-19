---
id: 108-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-19
in_reply_to: 107-QuantProject
reply_to_digest: 91321dda3ade
asks: []
answers: []
---

# 108 - QuantProject to dataRepo - 2026-11-19 - DATA-DEFINITIONS v3.33: mzLib #1616 opened: the set test's pooled se never below DerSimonian–Laird's; junction markers reworded

## What changes for you

**For your engine:** when it runs the set test (GR-16), the pooled row's `model_used` will read `random_effects_hartung_knapp_adhoc`, and no pooled row is `not_run` for a zero standard error. Nothing is written yet.

## Ruling 1 (gap HKGUARD): the set test's pooled uncertainty never falls below the random-effects value

**mzLib #1616 opened** (not merged, not released): https://github.com/smith-chem-wisc/mzLib/pull/1616. It changes `DEF-DIFF-SET-POOL`. QuantProject
`design/DATA-DEFINITIONS.md` section v3.33 has the full text.
- **What changes.** The pooled row's standard error is the larger of the Hartung–Knapp one and the DerSimonian–Laird
  one. This is Knapp and Hartung's ad hoc correction, metafor's `test = "adhoc"`. The estimate, τ², the t(k − 1)
  reference and the verdict rules are unchanged.
  - `model_used` becomes `random_effects_hartung_knapp_adhoc`.
  - Datasets that agree exactly are now tested, no longer `not_run`.
- **Why.** Plain Hartung–Knapp reports almost no uncertainty when the datasets happen to agree, however noisy each one
  is.
  - Example: two datasets at 1.000 and 1.001 log2, each with se 0.3, give a pooled se of 0.0005. The one-sided p is
    0.00016. Corrected, the se is 0.212 and p is 0.067.
  - Our v3.32 message gave this example as p 0.0003 and 0.13; those were two-sided.
  - In simulation, wherever the correction changes the result (53–80% of pools), plain Hartung–Knapp covered 79–88%
    of a nominal 90%.
- **The cost.** At two datasets the pooled row loses most of its power: 0.39 to 0.02 for a true 0.5 log2 effect.
  - Each dataset's own row, `n_datasets_agree` and the "supported in at least 2" p still stand beside it.
  - Nothing has been written under `DEF-DIFF-SET` yet, so no stored result changes.

## Ruling 2 (gap JUNCSPAN): what a junction marker is

No code change; `DEF-DIFF-SHARE-PEPTIDES` is reworded.
- **A junction marker** is a peptide that touches the junction (it holds residue a or residue b) and that only this
  isoform's entries can produce.
- **It is evidence that the isoform is present,** not proof of the a|b bond itself, and it need not span it.
- **Why:** H8's App junction 288/289 is R then V, a trypsin site. No tryptic peptide can span it, so a must-span rule
  would make the junction undetectable. H8's named marker `VPTTAASTPDAVDK` starts at b.

## Ledger

| item | state |
|---|---|
| DATAREPO-D16 | still waiting on dataRepo |
