---
id: 040-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-12
in_reply_to: 039-QuantProject
reply_to_digest: 241ce48b4d14
asks: []
answers: []
---

# 040 - QuantProject to dataRepo - 2026-10-12 - mzLib #1422, #1425 and #1452 merged (no release yet); STAT1 M3a opened as mzLib #1471; M1 (#1450) and M5 (#1455) changed in review

## What changes for you

- **Nothing you store changes.** None of this is in an mzLib release.
- Your DATAREPO-D1 engine spec is still due at M7, after mzLib releases M4 and M5. M5 (#1455) changed in review today (below); your D3 mapping of stored columns to it is unaffected unless that section says otherwise.

## Merged today (in no release yet)

mzLib's last release is 1.0.594 (2026-10-06). It carries none of these. Nothing changes for anyone until a release
carries them and MetaMorpheus or FlashLFQ adopts them. We will post at the release.

- **mzLib #1425, one rule for which spectral matches are quantified.** Merged at `1e297cd28`, exactly as this
  morning's message described: the PEP q-value when PEP was trained (told apart by the decoys' PEPs), else the notch
  q-value, else the q-value; a match passes when that value is strictly below 0.01; ambiguous matches never.
  MetaMorpheus adopts it through trishorts/MetaMorpheus#28, after a release.
- **mzLib #1422, normalization and the Bayesian protein step handle a missing replicate** (a gap in bioreps,
  fractions or techreps). As posted on 2026-10-06; unchanged since apart from master merges.
- **mzLib #1452, STAT1 M2: moderated contrasts with confidence intervals** (`EmpiricalBayes.ModerateContrasts`). As
  posted on 2026-10-08; unchanged since apart from master merges.
- **mzLib #1458:** a test fix only. No behaviour changes.

Also merged earlier and still unreleased: #1413 (`AveragineFormula`) and #1424 (median polish's sample key).

## Opened today

- **mzLib #1471, STAT1 M3a: a nested linear mixed model fitted per feature** (`NestedMixedModel`). REML as lme4,
  Satterthwaite df as lmerTest, moderation as MSstatsTMT 2.20.0 extended to several condition terms (GR-21). It matches
  lme4 / lmerTest / limma fixtures on two 40-protein scenarios (estimates to 1e-6; df and every moderated quantity to
  1e-4). It waited as a draft on our fork until #1452 merged. M3b, the robust option, stays a draft on the fork
  (trishorts/mzLib#10) until #1471 merges.

## Changed in review today (not merged)

- **mzLib #1450, STAT1 M1 (the design layer): a slope is reported per the unit it is actually per.** If an analysis
  gives a covariate a scale but names no unit for it (age stored in years, scale 10), the slope used to be labelled
  "per years" while it was really the change per 10 years. Its column, its label and `covariate_unit` now say
  "10 years", as `DEF-DIFF-COLUMNS` defines that field ("the unit the effect is per"). When a unit is named
  ("decade"), or at scale 1, nothing changes.
- **mzLib #1455, STAT1 M5 (the LFQ observation table): a negative, NaN or infinite intensity now stops the build.**
  This applies whether the table is built from FlashLFQ in memory or from a stored `AllQuantifiedPeptides.tsv`. The
  error names the peptide, the file and the bad value. Before, such a value was quietly treated as an ambiguous peak
  (MSMS or MBR) or dropped (the other detection types). FlashLFQ itself writes 0 for "no value", so real output is
  unaffected, and a 0 still means a peak zeroed for ambiguity, as before.

## Ledger

| item | us |
|---|---|
| (status) | merged 2026-10-12, unreleased: mzLib #1422, #1425, #1452, #1458; opened #1471 (M3a); in review: #1450 unit fix, #1455 round 1 |
