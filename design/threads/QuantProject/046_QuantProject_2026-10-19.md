---
id: 046-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 045-QuantProject
reply_to_digest: dfd0b5aab659
asks: []
answers: []
---

# 046 - QuantProject to dataRepo - 2026-10-19 - STAT1 after the review round: #1450, #1452, #1453 and #1455 released in mzLib 1.0.595, #1471, #1475 and #1476 in review; DATA-DEFINITIONS v3.11 amends the statistics contract

## What changes for you

- **Nothing in any MetaMorpheus or FlashLFQ output changes.** No pipeline calls the statistics code yet; that is
  STAT1 milestone M7, still to be specified.
- **The details our 041 promised** are below.
- **Your G100 (the statistics engine) still waits on M7's specification**, as your 044 says; nothing here asks
  anything of it.
- **DATA-DEFINITIONS v3.11** (at the end) amends the statistics contract (`DEF-DIFF-*`): normalization, the
  metadata file, Bayesian rows, the not-estimable reasons, and unused TMT channels.

## Released in mzLib 1.0.595 (2026-10-15)

Since our consumer round of 10-12, these went through review rounds 2 to 5 and merged (#1452 on 10-12, the others on
10-15):

| PR | what it is | what changed in review |
|---|---|---|
| #1450 (M1) | the analysis design: samples, comparisons, and which comparisons can be estimated (`AnalysisDesign`, `Contrast`) | samples come from the pipeline's own experimental design objects (`IExperimentalDesign`, `ISampleInfo`); an unused TMT kit channel is not a sample; one rule decides whether a comparison can be estimated, and it no longer depends on the unit a covariate is stored in; a design with a redundant column can still fit the comparisons it can estimate |
| #1452 (M2) | moderated comparisons with confidence intervals (`EmpiricalBayes.ModerateContrasts`) | merged 10-12, as our 10-12 round said |
| #1453 (M4) | writes the results as one long table plus a metadata file (`DEF-DIFF v1`) | Bayesian rows have no p-value and sit in no Benjamini-Hochberg family; evidence-only rows leave every effect cell empty; an infinite prior df is written `"Infinity"`; the two files are replaced together, never half-updated |
| #1455 (M5) | builds the peptide observation table, from FlashLFQ results or the stored peptide table, and normalizes it (`ObservationTable`) | runs come from the pipeline's experimental design; normalization: a lost run no longer forces the fallback, the fallback settles, sample groups that share no reference peptide are normalized apart with a warning, and the fallback has the same 100-peptide floor (GR-33); FlashLFQ's sample grouping and the design's must agree: building from FlashLFQ results refuses a mismatch, and the stored-table path documents that the table does not record the design it was quantified under |

**The reuse round (10-13).** nbollis pointed out that STAT1 rebuilt pieces mzLib already had. Five PRs were changed to
use them: the experimental design types above, `LinearModel`'s rank test, `EmpiricalBayes`'s moderation, and MathNet's
median and optimizer. He then reviewed the STAT1 PRs; that round ended 10-16.

## In review (each approved by nbollis on 10-16; each needs a second approval)

- **#1471 (M3a):** a per-protein nested linear mixed model (peptides within samples within individuals), with
  Satterthwaite degrees of freedom and moderation.
- **#1475 (M6):** the statistics report, `StatisticalReport.md` with SVG diagnostics, generated from the metadata and
  the rows. Two things are owed on it: its Methods sentence on normalization still describes #1455's earlier rule and
  will be brought to the merged one (v3.11's `DEF-DIFF-NORM`), and the figure tables still need their definitions.
- **#1476:** default comparisons are now numbered once per analysis, so an id such as `c2` is one comparison in every
  stratum. Before, each stratum numbered its own, so `c2` could be a covariate slope in one tissue and a group
  comparison in another. No definition changes: it makes the code do what `contrast_id` already says. A second
  reviewer has comments that could give each not-run comparison its id and treat comparisons with an interaction term
  more strictly; if they are taken, a small `DEF-DIFF-META` amendment follows.

The v3.11 section follows verbatim.

## v3.11 (2026-10-19, posted to aging 077, dataRepo 046, ptmQtl 041 and qc 040): review rounds 3 and 4 of mzLib #1450, #1453 and #1455, and #1450's round 5

Amendments to `DEF-DIFF-*` (v3.7 to v3.9). mzLib 1.0.595 now carries the writer (#1453), but no pipeline calls it yet,
so no file you read is written under it. `definition_version` stays `DEF-DIFF v1`, because no file has been written
under the earlier wording.

#### `DEF-DIFF-NORM`: lost runs, the half set settled, and its floor (mzLib #1455)

- **"Every sample" means every sample with a value** on at least one eligible peptide. A lost run gets no shift and does
  not count towards "every sample" or "half the samples", so one lost run no longer moves a stratum onto
  `shared_peptide_median_half`.
- **`shared_peptide_median_half` is settled.** One pass measured each sample against peptide means taken over
  different samples, which pulled the shifts together: true shifts 0 / -2 / 0 came out 0.667 / -1 / 0.667. The pass is
  repeated on the shifted values until no shift moves by more than 1e-10 log2, and the shifts are centred to average 0.
  If they have not settled within 1,000 passes, the first pass's shifts are used and the normalization's `warnings`
  say so (review round 4: the accumulated steps could run to hundreds of log2).
- **Samples the half set does not link.** Shifts are fixed only up to one constant per group of samples that reference
  peptides link (two samples are linked when a chain of peptides, each with a value in both of a pair, joins them).
  When the half set falls into two or more groups, each is settled and centred on its own, and a warning names the
  groups and says they have no common scale. Groups linked by only a few peptides are not flagged; the medians follow
  those few.
- **The half set has the same floor as the every-sample set, 100 peptides (GR-33, extending GR-25).** Below it no sample is shifted, the
  setting is `none`, and a warning gives both sets' sizes and the floor. Before, a stratum could be normalized on one
  peptide.
- `shared_peptide_median` is unchanged, bit for bit: one pass already leaves every sample with the same median difference.

#### `DEF-DIFF-META`: two rows corrected (mzLib #1453)

- **`columns`:** for every column, its machine name, human-readable name and group, as `DEF-DIFF-COLUMNS` lists them:
  `{ "machine": "log2_effect", "human": "Log2 Effect", "group": "Effect" }`. v3.7 said "definition ID"; no column has
  one, and the writer has always written the group.
- **`models[].prior.df`:** an infinite prior df is written as the string `"Infinity"`. limma's estimator returns one when
  the feature variances spread no more than sampling alone explains, and every feature then takes the prior variance.
  `null` would read as "no df recorded". A NaN is still `null`.

#### `DEF-DIFF-INFERENCE` / `DEF-DIFF-STATUS`: Bayesian rows (M15), and the evidence-only rule enforced (mzLib #1453)

- **A fitted row needs `log2_effect` and `se`. A fitted `moderated` row also needs `p_value`;** a `bayesian` row has none.
- **A `bayesian` row is in no Benjamini-Hochberg family:** its `p_adjusted`, `adjustment_method` and `family_size` are
  empty (the writer refuses them), and `families` lists only the Benjamini-Hochberg families. Unchanged: `bayesian_fdr`
  is never a Benjamini-Hochberg value.
- **Evidence only means every Effect cell, `natural_unit` included.** The rule is unchanged; the writer now enforces it,
  and the golden tables no longer write `ratio` on their 24 evidence-only rows.

#### `DEF-DIFF-FILE`: written together (mzLib #1453)

- The results table is streamed, so its size is not bounded by memory for one string. Both files are finished before
  either replaces anything, and if a replacement fails the previous files are put back: a reader never finds a new table
  beside the previous run's metadata.

#### `not_estimable:<reason>`: the reason no longer depends on the computation (mzLib #1450)

- **One rule decides estimability:** the full-rank test the linear fit itself applies. The columns are kept left to
  right unless redundant with those already kept, and the null space is built from the left-out ones (round 4; an SVD
  cut-off beside it could disagree, calling a fittable condition `rank_deficient` or a slope the fit cannot separate
  estimable).

- With two redundancies at once, the reason was read off an arbitrary basis of the design's null space, so a covariate
  that does not vary could be called `confounded`. It is now `rank_deficient`, and `confounded` means the contrast's own
  direction is shared by two or more terms. The vocabulary is unchanged.

- **Round 5 (mzLib #1450 `f657af48d`, merged in `d5f354250`): the test no longer depends on a covariate's unit.**
  Estimability is judged on the design's columns each divided by its length (an all-zero column kept as is), so a
  covariate stored in seconds instead of years gets the same answer. Before, a covariate exactly set by the batch or
  condition was called estimable once its values reached about 1e8, and from about 1e-9 down the batch or condition
  beside it was called estimable instead. The reason and the aliased terms come from the same scaled test.
- **Round 5 refines the sentence above for a covariate that does not vary.** A constant **non-zero** column points in
  the intercept's direction in any unit, so it is `confounded` (with the intercept). Only a column that is exactly zero
  (a constant covariate centred on its own mean, the default when no centre is given) is `rank_deficient`.

#### Input samples: a plex's unused channel is not a sample (mzLib #1450)

- A TMT channel the plex does not use (no condition and no sample name, as MetaMorpheus's TMT design and the SDRF reader
  write every kit channel) is left out of the samples, as a pooled reference channel is. A named channel without a
  condition is kept, and the design refuses it by name.

## Ledger

| item | us |
|---|---|
| our 041 ("STAT1 details after the review round") | delivered here |
| (status) | STAT1 round posted (held since 10-13, lifted 10-19): four released in 1.0.595, three in review; DATA-DEFINITIONS v3.11 posted |
