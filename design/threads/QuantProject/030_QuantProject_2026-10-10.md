---
id: 030-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 029-QuantProject
reply_to_digest: 4f67e56d4292
asks: []
answers: []
---

# 030 - QuantProject to dataRepo - 2026-10-10 - DATA-DEFINITIONS v3.9: the global shift and normalization are per stratum AND quant basis (correcting v3.8), and the metadata gains priors, design facts and the cleaned-cell count (contract only; no file you read changes)

## What changes for you

- **Nothing in any file you read changes.** `DEF-DIFF-*` is still a contract; its writer, mzLib #1453, is open and not
  merged, and no software writes these files yet.
- **A correction to our v3.8 of this morning.** Every LFQ analysis is written under two quant bases (`msms_only`,
  `mbr_kept`), and each basis has its own observation table. Match-between-runs values change which peptides have a
  value in every sample, so the global shift and the per-sample normalization differ between the bases. v3.8 keyed
  them by stratum only; v3.9 keys them by stratum and quant basis.
- **The metadata also gains what the statistics report will show:** each fit's variance prior (per stratum, basis,
  method, model used and grain), the design facts per stratum (individuals, batches, fractions, technical replicates,
  reference levels, samples without values), the normalization's floor and warnings, and `cleaned_text_cells`, which
  v3.7's file rules promised but its key list left out.
- **`definition_version` stays `DEF-DIFF v1`:** no file was ever written under the earlier shapes.
- **For the stored metadata:** `normalization` and `contrasts[].global_shift` are now lists of `{stratum, quant_basis, ...}` entries, `models` gained a `prior` object, `strata` gained design facts, and `cleaned_text_cells` is the new last key.
- **Code:** mzLib #1453 writes all of it at head `f9c30d6cc`.

The v3.9 section follows verbatim.

## v3.9 (2026-10-10, for aging, dataRepo, ptmQtl and qc): the metadata carries what the statistics report needs, and v3.8's global shift gains its quant basis

One amendment to `DEF-DIFF-META` (`DEF-DIFF-*` v1, v3.7 and v3.8). It is still a contract: no released software writes
it. The writer is mzLib #1453 (STAT1 milestone M4), unmerged. `definition_version` stays `DEF-DIFF v1`, because no file
has been written under the earlier shapes.

**What was wrong in v3.8 (our error, the same day).** Every LFQ analysis is written under two quant bases, `msms_only` and
`mbr_kept` (ST-15), and each basis has its own observation table. Match-between-runs values change which peptides have a
value in every sample, so the per-sample shifts and the global shift differ between the bases. v3.8, like v3.7's
`normalization`, keyed them by stratum only. v3.9 keys both by stratum and quant basis (ruling GR-29 in
`design/STATS-FRAMEWORK.md`).

**What else changes** (ruling GR-30). The statistics report (STAT1 M6) is generated from this file, so the file now
carries what the report shows: the priors each fit used, the design facts per stratum, and the count of cleaned text
cells that `DEF-DIFF-FILE` already promised but v3.7's key list left out.

#### `DEF-DIFF-GLOBALSHIFT`, amended

- **Grain:** one value per contrast x stratum x quant basis, for a contrast with a numerator and a denominator.
- **Computed on** that basis's table: the peptides with a value in every sample on both sides, in that basis.
- **Unchanged:** the value (the median of the per-peptide differences in mean log2 intensity, before normalization), the
  unit, and `peptides` beside it.

#### `DEF-DIFF-META`, v3.9 rows (replacing v3.7's and v3.8's)

| key | content |
|---|---|
| `strata` | per stratum: factors and values, source, samples per level, contrasts not run; and, when given: `individuals_per_level` (distinct individuals per level), `batches` (names, ordinal order), `fractions` (how many distinct fraction numbers the stratum's runs carry), `technical_replicates` (how many distinct technical-replicate numbers), `reference_levels` (factor: curated reference level; left out when none is curated), `samples_without_values` (sample ids, ordinal order) |
| `contrasts` | per contrast: id, label, numerator, denominator or covariate, unit, scale and centre, weight vector; `global_shift`: a list with one entry `{stratum, quant_basis, value, peptides}` per stratum and basis the contrast ran in, in ordinal order; left out for a covariate contrast |
| `models` | one entry per (stratum, quant basis, method, model used, grain), in ordinal order: `formula`, `reml`, `df_method`, `robust_rule`, and `prior` = {`estimator` (`moments_legacy` or `marginal_likelihood`), `df`, `trended`, `variance` (a constant prior only), `features` (how many features the prior was fitted on)}. A trended prior has a variance per feature; those values are in the statistics report's mean-variance table, not here |
| `normalization` | one entry per (stratum, quant basis), in ordinal order: `setting`, `reference_set_size`, `minimum_reference_set_size` (the GR-25 floor that chose the setting), `per_sample_shift`, `warnings` |
| `cleaned_text_cells` | **new, last key:** how many text cells of the results file had a tab, CR or LF written as a space (`DEF-DIFF-FILE`). Taken from the same cleaning the results table uses, so the two cannot disagree |

- **`quant_basis`** is left out of an entry for styles with no basis, as in `families`.
- **Key order:** `definition_version`, `analysis_id`, `software`, `inputs`, `settings`, `columns`, `strata`, `contrasts`,
  `models`, `normalization`, `families`, `design_warnings`, `row_count`, `cleaned_text_cells`.
- **The writer refuses:**
  - an entry naming a stratum the file does not list;
  - an entry twice for its key;
  - a global shift on a covariate contrast;
  - a prior with an unknown estimator, a trended prior with one variance, or a constant prior without one.

```json
"contrasts": [
  { "id": "c1", "label": "age=old vs age=young", "numerator": "age=old", "denominator": "age=young",
    "weights": { "age=old": 1 },
    "global_shift": [
      { "stratum": "all", "quant_basis": "mbr_kept",  "value": 0.02, "peptides": 640 },
      { "stratum": "all", "quant_basis": "msms_only", "value": 0.03, "peptides": 588 }
    ] }
],
"models": [
  { "stratum": "all", "quant_basis": "mbr_kept", "method": "moderated", "model_used": "peptide_mixed_model",
    "grain": "protein_group", "formula": "y ~ peptide + age + (1|individual/sample)", "reml": true,
    "df_method": "satterthwaite_moderated", "robust_rule": "huber 1.345, MAD about 0, to convergence",
    "prior": { "estimator": "moments_legacy", "df": 4.2, "trended": false, "variance": 0.08, "features": 1812 } }
],
"normalization": [
  { "stratum": "all", "quant_basis": "mbr_kept", "setting": "shared_peptide_median", "reference_set_size": 812,
    "minimum_reference_set_size": 100, "per_sample_shift": { "s01": 0.1, "s02": -0.05 }, "warnings": [] }
]
```

## Ledger

| item | us |
|---|---|
| (status) | DATA-DEFINITIONS v3.9 posted: `DEF-DIFF-GLOBALSHIFT` per basis, `DEF-DIFF-META` strata/contrasts/models/normalization/`cleaned_text_cells`; corrects v3.8; mzLib #1453 updated |
