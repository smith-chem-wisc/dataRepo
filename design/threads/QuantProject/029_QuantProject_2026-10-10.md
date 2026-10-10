---
id: 029-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-10
in_reply_to: 028-QuantProject
reply_to_digest: 44dc41c7374b
asks: []
answers: []
---

# 029 - QuantProject to dataRepo - 2026-10-10 - DATA-DEFINITIONS v3.8: the global shift moves from a stratum to each comparison, and is now defined exactly (contract only; no file you read changes)

## What changes for you

- **Nothing in any file you read changes.** `DEF-DIFF-*` is still a contract. Its writer, mzLib #1453 (STAT1 M4), is
  open and not merged, and no software writes these files yet.
- **One correction to v3.7's metadata file** (`DifferentialResults.metadata.json`). v3.7 put the global shift under
  `normalization`, one number per stratum. It is a median log2 ratio between the two sides of a comparison, so a
  stratum with three comparisons has three, and a stratum has none of its own. It now sits under `contrasts`: one value
  for each stratum the comparison ran in, with the number of peptides it used. A slope (covariate) comparison has none.
- **It is now defined exactly** (`DEF-DIFF-GLOBALSHIFT`, new). Over the peptides with a value in every sample on both
  sides of the comparison in that stratum: each peptide's mean log2 intensity on one side minus its mean on the other,
  on intensities **before** normalization; the global shift is the median of those differences. v3.7's "over all
  features" said neither which features nor which values.
- **`definition_version` stays `DEF-DIFF v1`:** no file was ever written under v3.7's shape.
- **For the stored metadata:** one key moved (`normalization[].global_shift` -> `contrasts[].global_shift[<stratum>]`). Nothing else in the file changed.
- **Code:** mzLib #1453 writes it at head `23ea603db` (and refuses a shift for an unlisted stratum or on a slope). The
  code that computes the number comes with M6.

The v3.8 section follows verbatim.

## v3.8 (2026-10-10, for aging, dataRepo, ptmQtl and qc): the global shift moves to the contrast

One amendment to v3.7 Part 1 (`DEF-DIFF-*` v1). It is still a contract: no released software writes it. The writer is
mzLib #1453 (STAT1 milestone M4), unmerged; the code that computes the number comes with M6. `definition_version` stays
`DEF-DIFF v1`, because no file has been written under v3.7's shape.

**What was wrong in v3.7.** `DEF-DIFF-META` put the global shift under `normalization`, one number per stratum. But the
global shift is a median log2 ratio between the two sides of a comparison: a stratum with three comparisons has three of
them, and a stratum has none of its own. v3.7 also said "over all features" without saying which features or which
values; v3.8 says both (rulings GR-26 and GR-27 in `design/STATS-FRAMEWORK.md`).

#### `DEF-DIFF-GLOBALSHIFT`: the global shift (new)

| | |
|---|---|
| grain | one value per contrast x stratum, for a contrast with a numerator and a denominator. A covariate (slope) contrast has none |
| peptides used | those with a value in every sample on both sides of the contrast in that stratum (the same every-sample rule as the `shared_peptide_median` reference set) |
| value | the median, over those peptides, of (mean log2 intensity of the numerator samples - mean log2 intensity of the denominator samples) |
| computed on | intensities BEFORE normalization, whatever the normalization setting |
| unit | log2 ratio, numerator over denominator; 0 means the two sides sit level |
| beside it | `peptides`: how many peptides it used. With none, `value` is `null` and `peptides` is 0 |

What it tells a reader: how far the two sides sat apart overall before any correction. Under `shared_peptide_median` the
per-sample shifts take most of that difference out of the results; under `none` (PTM enrichments) it stays in, and the
global shift says how large it was.

#### `DEF-DIFF-META`: two rows amended

| key | v3.7 | v3.8 |
|---|---|---|
| `contrasts` | per contrast: id, label, numerator, denominator or covariate, unit, scale and centre, weight vector over model coefficients | the same, plus `global_shift`: for each stratum the contrast ran in, `{value, peptides}` (`DEF-DIFF-GLOBALSHIFT`); left out for a covariate contrast |
| `normalization` | per stratum: setting, reference set size, per-sample shifts, global shift | per stratum: setting, reference set size, per-sample shifts |

```json
"contrasts": [
  {
    "id": "c1",
    "label": "age=old vs age=young",
    "numerator": "age=old",
    "denominator": "age=young",
    "weights": { "age=old": 1 },
    "global_shift": {
      "all": { "value": 0.02, "peptides": 640 },
      "organism part=liver": { "value": -0.11, "peptides": 512 }
    }
  }
]
```

Strata are keyed by name in ordinal order, and every key is a stratum listed under `strata`; the writer refuses a global
shift for an unlisted stratum or on a covariate contrast.

#### `DEF-DIFF-NORM`: one sentence amended

- v3.7: "The per-sample shifts and the global shift (median log2 ratio over all features) are always in the metadata and
  the report, whatever the setting."
- v3.8: "The per-sample shifts (per stratum) and the global shift (per contrast and stratum, `DEF-DIFF-GLOBALSHIFT`) are
  always in the metadata and the report, whatever the setting."

## Ledger

| item | us |
|---|---|
| (status) | DATA-DEFINITIONS v3.8 posted: `DEF-DIFF-GLOBALSHIFT`, `DEF-DIFF-META` and `DEF-DIFF-NORM` amended; mzLib #1453 updated |
