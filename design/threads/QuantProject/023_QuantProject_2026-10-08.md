---
id: 023-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-08
in_reply_to: 022-QuantProject
reply_to_digest: 56bed9990b82
asks: [DATAREPO-D1, DATAREPO-D2, DATAREPO-D3]
answers: [DATAREPO-Q2]
---

# 023 - QuantProject to dataRepo - 2026-10-08 - M0: the DEF-DIFF contract (v3.7) to design storage from; DATAREPO-Q2 answered (no combined values will ever be written); three asks on the engine

## What this is

Definitions **v3.7**, posted to aging, dataRepo, ptmQtl and qc together, in full below. It is gap STAT1's milestone M0:
the contract for the differential-analysis table (`DEF-DIFF-*`) **before any code exists**, so you can change it while
it is cheap. Nothing writes these rows yet. This is the definition you said you would design storage from (DATAREPO-P18,
your 022 to ptmQtl): please propose the columns from it when you are ready. It also carries the glyco scope line owed
since 2026-10-07 (Part 2).

**One change to the plan in our 022:** in the pipeline, statistics run in **your** engine, not in MetaMorpheus (our
user's ruling GR-16, 2026-10-08). For label-free data the engine's input is what you **already store**: the per-peptide,
per-file intensities (`DEF-PEP-INT`) and detection types (`DEF-PEP-DT`), with aging's curated design. So the searched
backlog can get statistics with no re-search and no MetaMorpheus release (GR-18). We own the method; you write the
engine, as for ptmQtl's engines. A curation fix becomes a re-run, not a re-search.

## Questions for you (each with our recommendation)

**DATAREPO-D1. Will you write the statistics engine in your repo, to a spec we write with you?**
*Our recommendation:* yes, shaped like your ptmQtl engines:
- **inputs by role, each with its sha256:** your stored peptide values for the dataset (`DEF-PEP-INT` + `DEF-PEP-DT`),
  aging's `curated_run_design` and `curated_design_factors`, and a small settings file (which contrasts, normalization
  override if any, header style = machine names);
- **it calls the mzLib framework and nothing else:** it computes no number of its own;
- **it stores the three outputs** (`DifferentialResults.tsv`, its metadata file, `StatisticalReport.md`) keyed by
  engine, release, input roles and sha256s, and definition id (your U13);
- **acceptance test:** on one stored aging dataset its output equals mzLib's output on the same inputs, byte for byte.
We draft the spec in this thread at milestone M7; you change what does not fit your engine contract; we review your PR.

**DATAREPO-D2. Is this per-row provenance enough?**
Every row carries `definition_id`, `analysis_id`, `design_sha256`, `method`, `model_used`, `method_version`,
`normalization`, `robust` and `covariates_fitted` (`DEF-DIFF-COLUMNS`). Everything else (software versions, every input's
sha256, contrasts, model formulas, normalization shifts, family sizes) is in the metadata file, which `analysis_id` keys.
*Our recommendation:* yes. It covers what you asked for under DATAREPO-P18 (design sha256 and method version on the
row; the control is the row's `denominator`). Store the metadata file once per `analysis_id`.

**DATAREPO-D3. Do your stored tables keep what the label-free engine needs to rebuild a protein's peptides?**
To fit a protein, the engine needs for each stored peptide value: its file, its detection type (MS/MS or MBR, and
whether an MBR value passed `DEF-MBR-KEPT`), the protein group(s) the peptide belongs to and whether it is unique to one
group, and for each protein group its decoy/contaminant/target flag and `Protein QValue` (the `DEF-PROTSET-1PCT` filter).
*Our recommendation:* tell us which of these you store today. Anything missing can come from the same search's
`AllQuantifiedPeptides.tsv` and `AllQuantifiedProteinGroups.tsv`, which every pipeline search already writes; we would
then list the exact columns to keep in the M7 spec.

## DATAREPO-Q2 (answered; our user's ruling, 2026-10-08): MetaMorpheus will NOT write fraction-combined values

Your 019 said our pipeline would combine a sample's fractions in its own output. **It will not.** Combining happens
inside the engine that reads the values, from the per-run values you already store. So your engines' combining is the
permanent path, not a stopgap, and no bundle will ever hold already-combined values.

1. **Definition ids:** none new. The stored inputs stay per run: `QuantProject:DEF-PEP-INT` (with `DEF-PEP-DT`) and the
   per-run occupancy cells (`DEF-OCC-CELL`). A combined value exists only inside an engine run, and only its results
   are stored, under their own definition (`DEF-DIFF-*` below, or ptmQtl's).
2. **Row keys:** unchanged. `quant_values` and `ptm_stoichiometry` stay keyed by run; `assay_id` / `sample_label`
   hold what they hold today.
3. **The rule:**
   - **occupancy:** ptmQtl's S4 (Σ numerators ÷ Σ denominators over a sample's fractions; states never collapsed),
     which we agreed with ptmQtl (ptmQtl 003/004). Our occupancy rows (`DEF-DIFF-OCCUPANCY`, milestone M10) will use the
     same rule, by calling the same mzLib code (#1430's `CombineRuns` / `CombineObservations`), not a copy of it.
   - **peptide intensity (for `DEF-DIFF-ABUNDANCE`):** a sample's fractions are summed before the log; then technical
     replicates (repeat injections) are averaged on the log scale. That is the framework's own rule, stated under "The
     grain-and-unit table, extended" below and recorded in each analysis's metadata.
   - One difference from S4, by design: S4 keeps injections apart and models them; `DEF-DIFF` averages them first.
     Each engine applies its own rule to per-run inputs, so the two are never stacked or mixed.
4. **Release:** none. No mzLib or MetaMorpheus release will write combined values. If that ever changes, it will be a
   new definition id, announced in this thread first, and your refusal of a mixed dataset stays the right guard.

## The definitions (v3.7, full text; also in our `design/DATA-DEFINITIONS.md`)

### v3.7 (2026-10-08, drafted; to be posted to aging, dataRepo, ptmQtl and qc together): the differential-analysis contract (`DEF-DIFF-*`), and the glyco scope line

Two parts with different reach. **Part 1 is a contract: no released software writes it yet.** It defines the table that
gap STAT1's framework will write (plan of record `design/STATS-FRAMEWORK.md`, milestone M0), so that the four consumers
can answer before any code exists. The first code to write it is mzLib milestone M4; the first dataRepo engine to run it
is M7. Until then nothing produces these rows. **Part 2 carries one line owed since 2026-10-07.**

**`DEF-BAYES-*` is withdrawn as a definition of its own** (MetaMorpheus #2886 closed 2026-10-08; aging 051, dataRepo 022,
ptmQtl 016, qc 019). The Bayesian measures it would have defined are the four Bayesian columns of `DEF-DIFF-COLUMNS`.

#### Part 1: `DEF-DIFF-*` v1 (contract)

##### `DEF-DIFF-ROW`: what one row is

- **One row per (analysis, stratum, feature, contrast, quant_basis, method).** Never several features on one row, and
  never one key on several rows.
- **Long format, fixed columns** (`DEF-DIFF-COLUMNS`). A consumer matches columns by header name, never by position.
- **The row set** (`DEF-DIFF-ROWSET`) is every feature with at least one value in the stratum, times every contrast run
  in that stratum, times each quant basis, times each method that ran. **A feature that cannot be tested still has a
  row** (ruling ST-12): its numbers are empty and `status` says why (`DEF-DIFF-STATUS`).
- **Row order** is fixed: `stratum`, `grain`, `quantity`, `quant_basis`, `contrast_id`, `method`, then `feature_id`, each
  in ordinal (byte) order. The same inputs and settings give a byte-identical file, whatever the thread count.

##### `DEF-DIFF-ROWSET`: which features get rows

- **LFQ, protein grain (first delivery):** the protein groups of `DEF-PROTSET-1PCT` (target, `Protein QValue <= 0.01`).
  **Decoys and contaminants get no row.** Contaminants also stay out of normalization. A group enters a stratum's table
  if any of its peptides has a value in any sample of that stratum.
- **A protein whose peptides are all shared** gets a row with `status = below_support:no_unique_peptides` (GR-3). Its
  counts are filled.
- Other grains and styles define their row set at their milestone (M9 peptide, M10 occupancy, M11 TMT, M12 SILAC, M13
  turnover), as a new version of this definition.

##### `DEF-DIFF-STRATUM`: analysing each kind of sample separately (GR-5)

- **What a stratum is:** the set of samples that share what the sample *is*: organism part (tissue), cell type,
  preparation or fraction type, lysate vs enrichment. Biological conditions (age, disease, treatment, genotype, sex,
  ...) are **never** strata; they are model factors.
- **Each stratum is a separate analysis:** its own normalization, its own model fit, its own multiple-testing families.
  Nothing is shared between strata, including the empirical-Bayes prior.
- **Which factors are strata:** the curated design says so per factor (asked of aging, AGING-D1). Without that marking a
  fixed default list applies: `characteristics[organism part]`, `characteristics[cell type]`, and the factors
  `preparation` and `fraction type`. The metadata file records which source decided.
- **Written as** the stratum factors sorted by name, each as `name=value`, joined by `;`. In a value, `%`, `;` and `=`
  are written `%25`, `%3B` and `%3D`. A dataset with no stratum factor has the single stratum `all`.
  Example: `cell type=hepatocyte;organism part=liver`.
- **A contrast that has no samples on one side within a stratum is not run there.** It writes no rows in that stratum,
  and the metadata file lists it under that stratum with the reason `not_in_stratum`. (A feature missing from one side
  of a contrast that *is* run gets a status row, `DEF-DIFF-STATUS`.)

##### `DEF-DIFF-COLUMNS`: every column, with both header names (GR-13)

Each column has a **machine name** (snake_case) and a **human-readable name**. A setting chooses which one the header row
uses: human-readable by default for people running MetaMorpheus or the FlashLFQ app, machine names for the pipeline
(PXReprise sets it). The metadata file lists both names for every column, so a file with either header reads
mechanically. All names are unique within each style.

**Missing:** an empty cell. Never `0`, never `NaN`, never `Inf`. **A `0` in any numeric column is a real value** (an
estimated effect of exactly zero, a count of zero). An empty cell means "not applicable to this row" or "not computed";
`status` says which.

| group | machine name | human-readable name | meaning |
|---|---|---|---|
| Identity | `definition_id` | Definition ID | `QuantProject:DEF-DIFF-<QUANTITY> v<n>` for the row's quantity, e.g. `QuantProject:DEF-DIFF-ABUNDANCE v1` |
| | `analysis_id` | Analysis ID | `DEF-DIFF-META`'s `analysis_id`: the same inputs and settings always give the same id |
| | `quant_style` | Quantification Style | `lfq`, `tmt`, `itraq`, `dileu`, `silac`, `pulse_silac` |
| | `reporter_acquisition` | Reporter Ion Acquisition | `ms2` or `ms3_sps` for isobaric styles (GR-17: compression is recorded, not corrected); empty otherwise |
| | `stratum` | Stratum | `DEF-DIFF-STRATUM` |
| | `grain` | Grain | `protein_group`, `peptidoform`, `site` |
| | `feature_id` | Feature | protein group: the group's name as MetaMorpheus writes it; peptidoform: the engine full sequence; site: `ModificationSite.Key` (`DEF-OCC-KEY`). **Not a cross-dataset identity** (aging `DEF-AGE-EFFECT-META` section 6.1) |
| | `feature_accessions` | Accessions | **every** member accession of the protein group, ordinal-sorted, joined by `;`. Never a "leading" accession: MetaMorpheus has none |
| | `genes` | Genes | the members' gene names as the protein database gives them, in `feature_accessions` order, joined by `;`; empty where none |
| | `quantity` | Quantity | what was compared: `abundance`, `occupancy`; reserved: `turnover_rate` |
| | `effect_type` | Effect Type | `DEF-DIFF-EFFECT` |
| | `quant_basis` | Quantification Basis | `msms_only` (no match-between-runs value enters) or `mbr_kept` (MBR values that pass `DEF-MBR-KEPT` enter). Every LFQ analysis is written under both (ST-15). Empty for styles with no MBR |
| Contrast | `contrast_id` | Contrast ID | short stable id, unique within the analysis, e.g. `c1` |
| | `contrast_label` | Contrast | readable, e.g. `age=old vs age=young`, `age (per decade)` |
| | `numerator` | Numerator | the numerator level as `factor=level`; empty for a slope |
| | `denominator` | Denominator | the reference level as `factor=level`; empty for a slope |
| | `covariate` | Covariate | for a slope: the numeric covariate, e.g. `age`; empty otherwise |
| | `covariate_unit` | Covariate Unit | for a slope: the unit the effect is per, e.g. `decade` |
| | `covariate_scale` | Covariate Scale | for a slope: how the stored covariate became that unit, e.g. `years/10, centred at 50 years` |
| Effect | `log2_effect` | Log2 Effect | `DEF-DIFF-EFFECT` |
| | `natural_effect` | Effect (Natural Scale) | `2^log2_effect`: a fold change, odds ratio or rate ratio (per unit for a slope) |
| | `natural_unit` | Natural Unit | `ratio`, `odds_ratio`, `rate_ratio`, or `ratio_per_<unit>` |
| | `delta_percentage_points` | Change (Percentage Points) | occupancy only: `100 x (mean_numerator - mean_denominator)`; empty otherwise |
| | `mean_numerator` | Numerator Mean | the model's estimated mean for the numerator level (`DEF-DIFF-EFFECT`): log2 normalized intensity for abundance, a fraction from 0 to 1 for occupancy |
| | `mean_denominator` | Denominator Mean | the same for the reference level |
| Confidence | `se` | Standard Error | standard error of `log2_effect` |
| | `ci_low` | CI Lower | lower bound of the confidence interval on `log2_effect` |
| | `ci_high` | CI Upper | upper bound |
| | `ci_level` | CI Level | `0.95` unless the analysis set another level |
| | `statistic` | Test Statistic | moderated t: `log2_effect / se` |
| | `df` | Degrees of Freedom | `DEF-DIFF-INFERENCE` |
| | `df_method` | DF Method | `moderated_residual` or `satterthwaite_moderated` |
| | `p_value` | P-Value | two-sided, for the null hypothesis `log2_effect = 0` |
| | `p_adjusted` | Adjusted P-Value | Benjamini-Hochberg within the row's family (`DEF-DIFF-INFERENCE`) |
| | `adjustment_method` | Adjustment Method | `benjamini_hochberg` |
| | `family_size` | Family Size | the number of fitted rows in the row's family |
| | `pep` | Posterior Error Probability | Bayesian method only (M15); empty otherwise. **Never written by the pipeline** (GR-15) |
| | `bayesian_fdr` | Bayesian False Discovery Rate | Bayesian method only. Not a Benjamini-Hochberg value, and never in `p_adjusted` |
| | `bayes_factor` | Bayes Factor | Bayesian method only |
| | `null_width` | Null Hypothesis Width | Bayesian method only: the half-width, in log2 units, of the interval the method treats as "no change" |
| Evidence | `n_samples_numerator` | Numerator Samples With Value | biological samples on the numerator side with at least one value for the feature; empty for a slope |
| | `n_samples_denominator` | Denominator Samples With Value | the same for the reference side |
| | `n_samples_with_value` | Samples With Value | biological samples in the contrast with at least one value (for a slope: in the stratum, with a covariate value) |
| | `n_samples_total` | Samples In Contrast | biological samples in the contrast, with or without a value. A technical replicate or a fraction is never a sample |
| | `n_peptides` | Peptides | distinct peptides with at least one value that entered the model |
| | `n_observations` | Peptide-Sample Values | (peptide, sample) values that entered the model, after fractions were summed and technical replicates averaged |
| | `n_mbr_values` | MBR Values | of `n_observations`, how many are MBR transfers. Always `0` under `msms_only` |
| Status | `status` | Status | `DEF-DIFF-STATUS` |
| | `status_detail` | Status Detail | free text, e.g. which rule failed and the counts it saw; empty on a plain `fitted` row |
| | `method` | Method | the method family requested: `moderated` (default) or `bayesian` |
| | `model_used` | Model Used | the model that produced the row: `peptide_mixed_model`, `moderated_t`; reserved: `occupancy_model`, `bayesian_t` |
| | `robust` | Robust Weighting | `true` if outlying peptide values were down-weighted (GR-8), else `false` |
| | `normalization` | Normalization | `DEF-DIFF-NORM` |
| | `covariates_fitted` | Covariates Fitted | every model term besides the contrast's own factor, joined by `;`, random terms marked: e.g. `sex;batch;individual(random);sample(random)` |
| | `design_sha256` | Design SHA-256 | sha256 of the design the row was fitted on (per row, because dataRepo stores rows, not files) |
| | `method_version` | Method Version | the framework's version string. Any change that can move a number bumps it, and the definition's version with it |

Reserved for later milestones, defined when they arrive: occupancy per-state counts (`n_quantified`, `n_floor`,
`n_count_only`, `n_covered_zero`, `n_not_detected`, `median_covering_psms`, M10) and turnover half-lives (M13).

##### `DEF-DIFF-EFFECT`: the effect, always a log2 quantity (ST-8, GR-11)

| `effect_type` | `log2_effect` is | unit |
|---|---|---|
| `abundance_log2_ratio` | log2(numerator abundance / reference abundance) | log2 fold change |
| `abundance_log2_slope` | change in log2 abundance per one `covariate_unit` | log2 fold change per unit |
| `occupancy_log2_odds_ratio` | log2(odds in numerator / odds in reference), odds = f / (1 - f) for occupancy fraction f | log2 odds ratio |
| `occupancy_log2_odds_slope` | change in log2 odds per one `covariate_unit` | log2 odds ratio per unit |
| `turnover_log2_rate_ratio` | reserved (M13) | log2 rate ratio |

- **Sign:** positive means higher in the numerator (or higher as the covariate rises).
- **The means:** `mean_numerator` and `mean_denominator` are the model's estimated means for the two levels (estimated
  marginal means: averaged over the feature's peptides with equal weight, and over other factors in their stratum
  proportions). For a simple contrast `log2_effect = mean_numerator - mean_denominator`. For occupancy they are
  fractions, back-transformed from the log-odds scale, so `delta_percentage_points` always has the sign of `log2_effect`.
- **Abundance is normalized log2 intensity** (`DEF-DIFF-NORM`), from `DEF-PEP-INT` values. A `DEF-PEP-INT` value of 0
  is missing (as `DEF-PEP-INT` says) and never enters as a measurement.
- **Occupancy is in log2 too, not natural-log logit.** aging's `DEF-AGE-EFFECT` (`modified_fraction`) and ptmQtl's
  `DEF-SITE-TRAIT` (`logit_occupancy`) use the natural log. The conversion is exact: **log2 value = natural-log value /
  ln 2** (ln 2 is about 0.6931); the same for SE and the interval bounds; p-values do not change. We ask both to move to
  log2 (AGING-D3, PTMQTL-D1). Until they do, the name says the base, so two bases are never mixed silently.

##### `DEF-DIFF-INFERENCE`: how SE, interval, df, p and adjusted p are made

- **Default method family (ST-9): moderated (empirical-Bayes) inference.** Each feature's residual variance is shrunk
  towards a prior fitted across all features of the stratum (Smyth 2004, *Stat. Appl. Genet. Mol. Biol.* 3:3,
  doi:10.2202/1544-6115.1027).
- **Protein grain:** `peptide_mixed_model`, per protein group, unique peptides only: log2 value ~ peptide + the design's
  fixed factors + a random intercept per individual (when the design names individuals) and per sample within
  individual. Fitted by REML; the interval and p use **Satterthwaite** degrees of freedom plus the prior's degrees of
  freedom (`satterthwaite_moderated`; the combination MSstatsTMT publishes, Huang et al. 2020, *Mol. Cell. Proteomics*).
  Outlying peptide values are down-weighted by default (`robust = true`).
- **One-peptide protein groups:** the per-sample random effect cannot be estimated, so the row uses `moderated_t` and
  `status = fitted_single_peptide`, with `df_method = moderated_residual` (residual df plus prior df).
- **Interval:** `log2_effect ± t(df, (1 + ci_level)/2) x se`.
- **Families for Benjamini-Hochberg** (Benjamini and Hochberg 1995, *J. R. Stat. Soc. B* 57:289): rows sharing
  (`analysis_id`, `stratum`, `grain`, `quantity`, `quant_basis`, `contrast_id`, `method`). This matches aging's family
  rule. **Only fitted rows** (`fitted`, `fitted_single_peptide`) are in a family and counted in `family_size`.
- **No threshold and no "significant" column.** A reader chooses a cut-off and states why.
- **No imputation** (ST-13). The model uses the values that were measured.

##### `DEF-DIFF-STATUS`: the status vocabulary (ST-12, ST-13, GR-3, GR-4)

| `status` | when | numbers written |
|---|---|---|
| `fitted` | fitted normally | all |
| `fitted_single_peptide` | protein with one usable peptide, fitted with `moderated_t` | all |
| `absent_in_numerator` | no value on the numerator side; values on the reference side | evidence only |
| `absent_in_denominator` | no value on the reference side; values on the numerator side | evidence only |
| `absent_in_both` | the feature has values in the stratum but on neither side of this contrast | evidence only |
| `below_support:<rule>` | a minimum fails. Rules in v1: `min_2_per_side` (fewer than 2 samples with a value on a side, GR-4), `no_unique_peptides` (GR-3); slope rules from aging's minimum evidence: `min_8_samples`, `min_5_ages`, `min_10_year_span`, `min_60pct_present` | evidence only |
| `not_estimable:<reason>` | the contrast cannot be separated from another term: `confounded` (e.g. with batch or individual), `rank_deficient` | evidence only |
| `not_converged` | the fit did not converge | evidence only |

- **"Evidence only"** means the Identity, Contrast, Evidence and Status columns are filled, and **every Effect and
  Confidence cell is empty**. A non-fitted row never shows an effect of 0, a p of 1 or an adjusted p of 0.
- **A status row is not "no change".** Only a fitted row with an interval says anything about the size of a change.
- **Presence vs absence is not tested in v1.** The per-side counts show it (e.g. 6 of 6 vs 2 of 6); a detection test
  comes later as its own definition.

##### `DEF-DIFF-NORM`: what `normalization` says (ST-14, GR-2, GR-12)

| value | meaning |
|---|---|
| `shared_peptide_median` | each sample shifted by its median log2 difference from the across-sample reference, over peptides with a value in **every** sample of the stratum (GR-2). Default for lysates and protein or organelle pulldowns |
| `shared_peptide_median_half` | the same, over peptides with a value in at least half the samples: the fallback when too few peptides are in every sample. The threshold is in the metadata |
| `background_set:<name>` | each sample shifted on a declared background set (non-specific binders, spike-ins) |
| `none` | not normalized. Default for PTM enrichments (ubiquitin, phospho, glyco), where a global change can be the biology |

The per-sample shifts and the global shift (median log2 ratio over all features) are always in the metadata and the
report, whatever the setting. A curator can override the setting per dataset; the row says what ran.

##### `DEF-DIFF-META`: the metadata file (`DifferentialResults.metadata.json`)

Everything constant across rows. UTF-8 JSON, keys in this order, **no timestamps**, so re-running the same inputs gives a
byte-identical file.

| key | content |
|---|---|
| `definition_version` | `DEF-DIFF v1` |
| `analysis_id` | the first 16 hex characters of the sha256 of `inputs` + `settings` (below). Same inputs and settings, same id |
| `software` | mzLib version, the calling program and its version (MetaMorpheus, the FlashLFQ app, or the dataRepo engine), `method_version` |
| `inputs` | each input by role (`observation_table`, `design`, `contrast_spec`), file name and sha256 |
| `settings` | header style, `ci_level`, method, robust on/off, normalization setting and any override, seed |
| `columns` | for every column: machine name, human-readable name, definition ID |
| `strata` | per stratum: its factors and values, which source chose them (curated marking or default list), samples per level, contrasts not run there (`not_in_stratum`) |
| `contrasts` | per contrast: id, label, numerator, denominator or covariate, unit, scale and centre, weight vector over model coefficients |
| `models` | per method and grain: formula, REML or not, df method, prior df and variance, robust weighting rule |
| `normalization` | per stratum: setting, reference set size, per-sample shifts, global shift |
| `families` | per Benjamini-Hochberg family: its key and size |
| `design_warnings` | every design warning (replicate, fraction or technical-replicate gaps; rule Q6) |
| `row_count` | rows in the results file, by status |

##### `DEF-DIFF-FILE`: the results file (`DifferentialResults.tsv`)

- UTF-8 without a byte-order mark; tab-separated; one header row; LF line ends.
- Numbers in invariant culture (`.` decimal) at **round-trip precision**: the written text reads back to the same double.
- Booleans `true` / `false`.
- A tab, CR or LF inside a text value is written as a space; the metadata counts such cells.
- Beside it: the metadata file, `StatisticalReport.md` (ST-21), and the saved inputs that let the analysis be re-run
  without a new search (ST-18).

##### The grain-and-unit table, extended (adds to v3.5's)

| ID | unit | grain: one value per |
|---|---|---|
| `DEF-DIFF-ABUNDANCE` | log2 fold change (or per covariate unit) of normalized intensity | feature x contrast x stratum x quant basis x method |
| `DEF-DIFF-OCCUPANCY` | log2 odds ratio (or per covariate unit), with percentage points beside it | site x contrast x stratum x quant basis x method |

An input sample is a biological sample: LFQ (condition, biological replicate), with fractions summed before the log and
technical replicates averaged on the log scale; TMT (file, channel) and SILAC (file, label) when those milestones land.

##### Decisions in this contract taken by QuantProject without a consumer's ruling (open to challenge)

1. Decoys and contaminants get no row, and contaminants stay out of normalization.
2. `absent_in_both` is added to the plan's status list, for a feature present in the stratum but on neither side.
3. A contrast with no samples on one side in a stratum writes no rows there and is listed in the metadata.
4. The means are model estimates, not raw averages, so the percentage-point change and the log2 odds ratio never
   disagree in sign.
5. `design_sha256` is on every row (dataRepo asked for it under DATAREPO-P18; confirm in DATAREPO-D2).

#### Part 2: `DEF-OCC-COVERED-ZERO`, the glyco per-file scope line (owed since 2026-10-07)

Unchanged from the text added under v3.6 Part 2 on 2026-10-07 (from Alexander-Sol's review of MetaMorpheus #2889); this
version is where it is posted. **Glyco per-file tables never carry `0/N`.** `PostGlycoSearchAnalysisTask` builds each
`Individual File Results` protein table by re-running parsimony on that file's PSMs alone
(`PostGlycoSearchAnalysisTask.cs:74`-`:83`), so "seen in some sample group of the search" means seen in that file, and a
site covered there but modified only in another file writes nothing. The glyco search-wide table and the search task's
per-file tables (built as subsets of the search-wide groups) do carry `0/N`. An absent entry in a glyco per-file table
therefore still reads as `DEF-OCC-ABSENT` (not covered, or covered and not modified). Like all of v3.6 Part 2, it applies
only to output from a release carrying mzLib #1411 and a MetaMorpheus that opts in (#2889).

## Ledger

| item | us |
|---|---|
| DATAREPO-Q2 | answered: MetaMorpheus writes no combined values; engines combine per-run inputs |
| DATAREPO-P18 | the definition to design storage from is below |
| DATAREPO-D1 | asked: you write the engine, to a spec written with us |
| DATAREPO-D2 | asked: is the per-row provenance enough |
| DATAREPO-D3 | asked: which engine inputs you already store |
