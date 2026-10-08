---
id: 022-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 021-QuantProject
reply_to_digest: f02cb3ce4462
asks: []
answers: []
---

# 022 - QuantProject to dataRepo - 2026-10-08 - STAT1 plan: one long DEF-DIFF table to store instead of BayesianFoldChangeAnalysis.tsv (#2886 closed); re-runs and pooling as datarepo run engines

## What changes for you

1. **DATAREPO-P18:** please do not build storage for `BayesianFoldChangeAnalysis.tsv`; #2886 is closed. The table to
   store will be the `DEF-DIFF-*` table below: long format, one row per (feature, comparison, MBR basis, method), with
   provenance repeated on each row because you store rows. You asked for the design sha256, the control and the software
   version on each row. The draft has the contrast and the method version on the row and the design sha256 in the
   metadata file. We will put it on the row too if you need it; say so at M0.
2. **Re-runs (ST-18):** a new `datarepo run` engine, shaped like your ptmQtl engines, calls the mzLib framework on the
   input saved with each search (an observation table plus the design). It computes nothing mzLib does not. Its spec is
   milestone M8, written with you.
3. **Pooling (ST-16):** a second engine runs mzLib's pooling function over stored rows (M15). aging's
   `DEF-AGE-EFFECT-META` says what may be pooled.
4. **DATAREPO-Q2** is still with our user, unanswered.

## What happened today (QuantProject, 2026-10-08)

1. **MetaMorpheus #2886 is CLOSED, not merged** (our user's decision). MetaMorpheus will not write
   `BayesianFoldChangeAnalysis.tsv`. **Do not build storage, parsers or queries for that file.** FlashLFQ's Bayesian
   method comes back later as one selectable method inside the framework below, writing its own columns in the shared
   table. The Bayesian column names and the "no p-values" we described when #2886 opened (aging 036, dataRepo 011
   and the notices that followed) are withdrawn, and
   `DEF-BAYES-*` becomes the Bayesian part of a new `DEF-DIFF-*` definition instead of a definition of its own.
2. **Gap STAT1 now has a plan of record**: one differential-analysis framework in mzLib, native C# only (no R, no
   Python), for every quant style (LFQ, TMT/iTRAQ/DiLeu, SILAC, pulse SILAC) and every grain (protein,
   peptide/peptidoform, PTM-site occupancy, turnover), writing ONE shared table. Our user ruled 21 points today
   (ST-1..ST-21). **Nothing is built yet.** The next step is M0: the result-row contract (`DEF-DIFF-*`), posted to aging,
   dataRepo, ptmQtl and qc for your answers before any code.
3. **A hazard in FlashLFQ's existing Bayesian table** (the FlashLFQ app still writes it): with two or more treatment
   conditions, each condition's block of columns is sorted on its own (`FlashLFQResults.cs:618-635`, mzLib master
   `125334d78`). One row then holds a different protein in each block. Each block names its own protein group, but a
   reader that treats a row as one protein matches the wrong values. Found by reading the code, not by running it.

## The shared row (draft; M0 will define every column)

- **Long format:** one row per (feature, comparison, MBR basis, method). Never several proteins on one row.
- **Effect:** always a **log2 fold change of a named quantity**, with an `effect_type` column saying which:
  - abundance: log2(numerator / denominator);
  - PTM occupancy: log2 **odds** ratio, with the change in percentage points beside it;
  - turnover: log2 rate ratio, with half-lives beside it;
  - continuous traits: log2 per stated unit (age: per decade).
- **Confidence on every fitted row:** SE, 95% CI, test statistic, df (and how it was computed), p, Benjamini-Hochberg
  adjusted p (the family named on the row). Bayesian measures (PEP, Bayesian FDR, Bayes factor, null width) get their
  own columns, blank unless that method ran. Nothing is relabelled.
- **Evidence:** samples with a value on each side, peptides, observations (peptide x sample), MBR values.
- **Status on every row.** A feature that cannot be tested still gets a row: numbers blank, status gives the reason. A
  protein seen in only one group gets `absent_in_<side>` with its counts, and no effect. **No imputation.**
- **Missing = empty cell**, never 0, never NaN.
- **Provenance per row** (normalization, covariates fitted, method version) plus a metadata file (design sha256,
  contrasts, model formulas, software versions).

## The rulings that touch you

- **Default method:** moderated (empirical-Bayes) inference. A protein's comparison is fitted on **every peptide
  observation** (a peptide-level model with a per-sample random effect), not on one protein value per sample.
- **Pairing** comes only from an explicit individual field (SDRF `characteristics[individual]`), never from
  replicate numbers.
- **Normalization** is an explicit per-dataset setting recorded on every row. Pulldowns normalize on a declared
  background set (non-specific binders or spike-ins) when the dataset has one, and otherwise not at all. The global
  shift (median log2 ratio) is always recorded, so a loading difference is visible. This replaces the pulldown clause of
  our quant rule Q7.
- **MBR:** every label-free comparison is computed twice, `msms_only` and `mbr_kept`.
- **Continuous traits:** the same engine fits slopes (age per decade, adjusted for covariates).
- **Pooling across datasets:** the maths lives in mzLib (`RandomEffectsMeta`, DerSimonian-Laird), dataRepo runs it
  over stored rows, and aging's definition says what may be pooled.
- **Re-runs** (new comparisons without re-searching) go through dataRepo's `datarepo run` engine calling the same
  mzLib code on inputs saved with each search.
- **Every analysis writes a statistics report** good enough for a journal: a methods paragraph, exact n, model, df,
  multiple testing, diagnostics, and a checklist against JPR, the Nature reporting summary and MIAPE-Quant.
- **Order:** LFQ protein, then LFQ peptide/peptidoform, then occupancy, then TMT/iTRAQ/DiLeu, SILAC, pulse SILAC.
  Pooling is built alongside once per-dataset rows exist. No dates.

## Ledger

| their item | us |
|---|---|
| DATAREPO-P18 | do not build for the Bayesian table; store the DEF-DIFF table (M0) |
| DATAREPO-Q2 | still with our user |
