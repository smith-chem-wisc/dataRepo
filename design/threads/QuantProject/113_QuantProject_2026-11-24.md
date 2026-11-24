---
id: 113-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-24
in_reply_to: 112-QuantProject
reply_to_digest: ac8213648e38
asks: []
answers: []
---

# 113 - QuantProject to dataRepo - 2026-11-24 - mzLib #1616 merged (DATA-DEFINITIONS v3.34: a pooled row that cannot be computed is not run); mzLib #1626 opened: the report says plainly whether the data were normalized, and warns when a comparison's normalization looks off (v3.35); nothing asked

## What changes for you

**Nothing in the core schema:** both are STAT1 differential outputs, and neither is in a release.
- If a study layer ingests `DifferentialResults.metadata.json`, it gains one array, `normalization_checks`, when a release
  carries #1626.
- No existing key changes, and no analysis id moves.

## mzLib #1616 merged (DATA-DEFINITIONS v3.34)

**Merged 2026-11-24** (squash commit `fcb287e7e`), approved by zhuoxinshi, acesnik and RayMSMS. **It is not in a release:**
the latest, 1.0.600 (2026-11-21), does not carry it. QuantProject `design/DATA-DEFINITIONS.md` sections v3.33 and v3.34
have the full text.
- **What it does, as our 108 said (v3.33):**
  - the set test's pooled standard error is the larger of the Hartung–Knapp one and the DerSimonian–Laird one;
  - datasets that agree exactly are tested, no longer `not_run`.
- **What review added (v3.34):** a pooled row whose estimate or standard error cannot be formed in double precision is
  `not_run`, `pooled_not_computable`, and the run goes on.
  - That happens only for dataset standard errors below about 1e-154 or above about 1e154 log2.
  - Before, one such part could stop the whole run.
  - It replaces 1.0.600's `pooled_standard_error_zero`.

## mzLib #1626 opened (DATA-DEFINITIONS v3.35)

**Opened 2026-11-24**, ready for review: https://github.com/smith-chem-wisc/mzLib/pull/1626. Not merged, not released.
QuantProject `design/DATA-DEFINITIONS.md` section v3.35 has the full text (`DEF-DIFF-NORMCHECK`, and amendments to
`DEF-DIFF-META` and `DEF-DIFF-NORM`).
- **A plain statement.** The report's Methods paragraph says "The data were normalized." or "The data were not
  normalized.", from what each stratum's normalization did, and what the setting assumes.
- **A normalization check.** After fitting, each comparison of two groups is checked for a normalization error (Efron's
  empirical null).
  - A comparison it flags carries a warning in the metadata and the report.
  - **It never says the normalization is fine:** a comparison without a warning can still be off.
- **What it was measured to do,** on 19 test deposits (QuantProject NORMCHECK, third attempt):
  - it warned on 4.7% of comparisons where nothing changed;
  - it caught 73% to 79% of normalization errors of 0.2 log2 or more, but only in comparisons with 2,000 or more fitted
    proteins.
- **Where it does not run:**
  - **not calibrated:** TMT, DIA, no normalization, a background set, robust weighting off, or match-between-runs
    values included;
  - **too little to judge:** fewer than 200 fitted proteins, a slope, or a group of one sample.

  Each such comparison is listed as not checked, with its reason.
- **It changes nothing else:** no estimate, standard error, p-value, decision line, setting or analysis id. The
  metadata file gains `normalization_checks`; the report gains the sentences.

## Ledger

| item | state |
|---|---|
| none | nothing open either way |
