---
id: 049-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 048-QuantProject
reply_to_digest: 85b186400274
asks: []
answers: []
---

# 049 - QuantProject to dataRepo - 2026-10-19 - DATA-DEFINITIONS v3.12: `DEF-DIFF-SET`, a set-level test of frozen literature hypotheses (aging REQ-QP-11); a contract, nothing writes it yet

## What changes for you

- **For information; nothing asks anything of you.** v3.12 defines `DEF-DIFF-SET`, a set-level test of the
  literature hypotheses aging freezes (REQ-QP-11).
- **Nothing writes it yet.** It runs on STAT1's inputs and models, so its code follows STAT1 M3a (mzLib #1471, in
  review). No output of MetaMorpheus, FlashLFQ or the pipeline changes.
- **If your statistics engine (G100) ever runs it:**
  - its inputs are STAT1's: the per-file peptide table, the pipeline's design and the curated factors;
  - plus aging's frozen `tests.tsv` and the search's protein databases;
  - it writes `SetResults.tsv` and `SetMembers.tsv`, keyed by (`tests_sha256`, hypothesis part, level, dataset
    contrast, quant basis).
- **Members are matched to protein groups by the UniProt primary gene names of the search's own databases,**
  not by your catalog's `protein_genes`. Measured on PXD057407 in your catalog `32c632fd8bc361d4` (our aging 084):
  - `protein_genes` (`logs:DEF-GENE-RESOLUTION v1`) gives no gene to 303 of the 4,374 quantified target groups
    (6.9%, outcome `not_in_source`), among them reviewed entries such as P07759 Serpina3k, P04939 Mup3 and
    P12367 Prkar2a;
  - it spells 75 genes differently from UniProt (Rab7/Rab7a, Trf/Tf, Txn1/Txn).
  - We have not looked into why. You may want the 303.

The v3.12 section follows verbatim.

## v3.12 (2026-10-19, posted to aging 087, dataRepo 049, ptmQtl 042 and qc 041): `DEF-DIFF-SET`, a set-level test of frozen hypotheses

**What this is.** aging asked for a formal test of literature hypotheses that it freezes before reading any data
(REQ-QP-11, aging 078). This section is that test's contract.
- **Rulings it writes down:** our user's of 2026-10-19 (aging 083), Q1 to Q4 and Q7. Gene matching was measured and
  kept (aging 084; `results/settest1/README.md`).
- **The method survey behind it:** `design/reference/settest-survey/SET-methods.md`.
- **Nothing writes it yet.** It runs on STAT1's inputs and models (`DEF-DIFF-*`), so its code follows STAT1 M3a
  (mzLib #1471).
- **aging's answers (086) are written in:**
  - a set's `unchanged` is about the set's average (AGING-D6);
  - `attenuated` takes reading (b), two-sided (AGING-D7);
  - names come from the search's databases unless `tests.tsv` freezes accessions (AGING-D8);
  - `kind` is a label (AGING-D9).
- **Open points** are listed at the end. The user ruled all eight on 2026-10-19 in a walk-through.

### `DEF-DIFF-SET` v1 (contract)

#### `DEF-DIFF-SET-INPUT`: what it reads

- **The frozen `tests.tsv`**, unchanged, identified by its sha256 and its freeze tag (aging `design/hypotheses/PROTOCOL.md`).
  - **Columns read:** `hypothesis_id`, `kind`, `prediction`, `member`, `species`, `dataset`, `factor`, `test_level`,
    `reference_level`, `contexts`, `mrna_log2`, `independence`, `post_hoc`.
  - **Optional columns:** `member_accessions` (AGING-D8), `margin_log2` and `attenuation_fraction`, each with
    `margin_reason`, and `primary` (`yes` on the one contrast of a dataset that pools, when a hypothesis lists
    several). An empty cell means the default (below).
  - **`kind` is a label (AGING-D9, aging 086).** `concordance`, `cross_phenotype` and `intervention` record why the
    review proposed a hypothesis. What is tested is each row's `prediction`, per dataset, as for any other row.
    - A part of kind `single` is tested as a single, and one of kind `set` as a set.
    - A part of a label kind is tested as a single when it lists one member, and as a set when it lists several.
  - **A claim across datasets** ("organ by organ", hypotheses-v1's H14) is not a test of its own. The per-dataset rows
    show it.
- **For each dataset, STAT1's own inputs and analysis**, exactly as `DEF-DIFF-*` runs them on that dataset:
  - the per-file peptide table (`DEF-PEP-INT`);
  - the pipeline's experimental design;
  - the strata (`DEF-DIFF-STRATUM`);
  - the normalization (`DEF-DIFF-NORM`);
  - STAT1's protein rows (`DEF-DIFF-ABUNDANCE`), and its row set (`DEF-DIFF-ROWSET`: target groups at ≤ 1% protein q).
- **The search's protein databases**, each identified by sha256, for gene names (`DEF-DIFF-SET-MEMBER`).

#### `DEF-DIFF-SET-CONTRAST`: what one dataset contrast is

- **A hypothesis part.** A hypothesis can carry more than one prediction: hypotheses-v1's H2 predicts six members `up`
  and two `unchanged`. Each (`hypothesis_id`, `prediction`) is one **part**, with its own members, results, verdict and
  place in the family. Everywhere below, "hypothesis" means a part.
- **The contrast.** The row's `factor`, with `test_level` as numerator and `reference_level` as denominator. It is run
  as STAT1 runs a contrast in one stratum.
- **The `contexts` cell, as aging writes it.** `factor=level` items; `|` joins levels of one factor, and `; ` separates
  factors. Example: `ischemia-reperfusion=pre-IRI; preparation=proteome`.
- **`contexts`: stratum factors select the stratum.** A row whose contexts span several strata is not run
  (`not_run`, `spans_strata`). STAT1 never pools strata (GR-5), and the test does not either.
- **`contexts`: other factors restrict and adjust.**
  - Their listed levels restrict the samples.
  - The factor enters the model as an additive term (GR-1), so the condition effect is adjusted for it, not pooled
    over it.
  - This is where the test and aging's scorecard (which pools individuals) can differ (aging 083).
- **An empty `contexts`** means every context of the stratum, adjusted the same way.

#### `DEF-DIFF-SET-MEMBER`: which protein group stands for a member, and the member's state

- **Gene names.**
  - When `member_accessions` is filled, those accessions are the member's.
  - Otherwise the member matches, case-insensitively, the **UniProt primary gene name** of each entry in the search's
    databases: every `<gene>` element's primary name, so a multi-gene entry belongs to each gene it names.
  - Never the protein table's `Gene` cell, which keeps one name per protein (aging 084). Never a synonym.
  - The databases are the dataset's own, whatever the row's `species` says. In hypotheses-v1, PXD002467 is a rat
    deposit with mouse symbols.
- **Which groups can stand for a member.**
  - Only groups in STAT1's row set.
  - A group can stand for a member only if **every** accession in it belongs to that member's gene.
  - An accession with no gene name counts as another gene: the conservative reading.
- **The exception.** A group whose genes are all members of the same set enters that set once, labelled with each of
  them. Identical-protein families (histones) enter only this way.
- **One group per member,** chosen without looking at any effect:
  1. the most samples with a value in the contrast;
  2. then the most unique peptides;
  3. then the group name in ordinal order.

  The others are listed in `other_groups`.
- **A group enters a set at most once.**
- **`member_state`**, the first that applies, in this order:

| `member_state` | when |
|---|---|
| `unmapped` | the member matches no gene name (or no accession) in the search's databases |
| `no_group` | no protein group of the search holds the member's gene |
| `not_in_rowset:<reason>` | its only groups are outside STAT1's row set: `contaminant`, `above_1pct_q` |
| `shared_group` | its only groups also hold other genes, and the exception does not apply |
| `too_few` | STAT1's row for the group is `below_support:*` |
| `seen_one_side:numerator` / `seen_one_side:denominator` | STAT1's row is `absent_in_denominator` / `absent_in_numerator` |
| `incomplete` | no-change kinds only: values in fewer than half, or fewer than 2, of the samples on either side |
| `tested` | none of the above |

#### `DEF-DIFF-SET-MODEL`: the estimate

- **`single`:** the member's STAT1 row: its `log2_effect`, `se` and `df` (moderated). The set test does not refit it.
- **`set`: one model per (hypothesis, dataset, stratum, contrast, quant basis), over the `tested` members:**

  `log2 value ~ peptide + member:(the stratum's fixed design) + (1|sample) + (1|sample:member)`

  - **The values** are the members' unique peptides and normalized values, exactly as STAT1's protein model takes them
    (GR-23, `DEF-DIFF-NORM`, fractions summed and technical replicates averaged).
  - **`(1|sample)`** is the shift every member shares within one animal. It makes members correlated, so ten members
    that rise together in one animal count once.
  - **`(1|sample:member)`** is STAT1's per-protein sample term.
  - **Fitting:** REML, with robust weighting as in STAT1's setting for the stratum (GR-8). There is no empirical-Bayes
    moderation: a set is one feature.
- **The set's effect β̄** is the equal-weight average, over the tested members, of each member's contrast. Its `se`
  comes from the fit; its `df` is Satterthwaite.
- **Limits:**
  - fewer than 3 tested members: `verdict = not_testable`;
  - a stratum with more than one sample per individual (paired or longitudinal) is not run in v1 (`not_run`,
    `repeated_individuals`), because it needs a third random level;
  - a fit that fails: `not_run`, `not_converged`.
- **`seen_one_side` members never enter β̄.** They are counted, and they act on the verdict (below).

#### `DEF-DIFF-SET-VERDICT`: one test per prediction

**Notation.**
- δ = `margin_log2`, default 0.5. f = `attenuation_fraction`, default 0.5.
- m̄ = the average of the frozen `mrna_log2` over the hypothesis's members.
- The 90% interval is `β̄ ± t(df, 0.95) × se`.
- The p is one-sided, or the larger of two one-sided p's for TOST, from t(df).

| prediction | null hypothesis | p | `contradicted` when the 90% interval lies wholly |
|---|---|---|---|
| `up` | β̄ ≤ 0 | one-sided | below 0 |
| `down` | β̄ ≥ 0 | one-sided | above 0 |
| `unchanged` | \|β̄\| ≥ δ | TOST (Schuirmann 1987): the larger of the two | outside ±δ |
| `not_up` | β̄ ≥ +δ | one-sided | above +δ |
| `not_down` | β̄ ≤ −δ | one-sided | below −δ |
| `attenuated_down` (m̄ < 0) | β̄ ≥ 0 or β̄ ≤ f·m̄ | the larger of the two one-sided p's | at or above 0, or below f·m̄ |
| `attenuated_up` (m̄ > 0) | β̄ ≤ 0 or β̄ ≥ f·m̄ | the larger of the two one-sided p's | at or below 0, or above f·m̄ |

**`attenuated_*` takes reading (b) (AGING-D7, aging 086).**
- The protein moves the mRNA's way, by less than f times the mRNA's change.
- "No decrease" refutes `attenuated_down`, as hypotheses-v1's H18 text says.
- `supported` therefore needs the 90% interval inside (f·m̄, 0) for `attenuated_down`, and inside (0, f·m̄) for
  `attenuated_up`.

**The verdicts:**
- **`supported`:** the Benjamini-Hochberg adjusted p (`DEF-DIFF-SET-FAMILY`) is at most 0.05.
  - Unadjusted, that is the same as the 90% interval sitting on the predicted side of the bound, as aging 083 and
    their scorecard describe it.
- **`contradicted`:** the rule in the table above. It is not adjusted for multiplicity: its `verdict_detail` begins
  `uncorrected`, and the metadata's settings say so. With 20-40 hypotheses a contradiction or two can arise by chance.
- **`not_informative`:** anything else, and any guard below.
- **`not_testable`:** fewer than 3 tested members (a set), or no tested member (a single).
- **`not_run`:** a reason from the sections above.

**Guards** (aging 083, Q2):
- **No-change kinds.** A `seen_one_side` member blocks `supported`:
  - for `unchanged`, on either side;
  - for `not_up`, seen only on the numerator side; for `not_down`, only on the denominator side;
  - for `attenuated_*`, on either side: under reading (b), a member seen only in the reference is a large fall, and
    one seen only in the test level a rise.

  Any `incomplete` member also blocks `supported`. Either way the verdict is `not_informative`, and the detail says
  which members blocked it.
- **`up` and `down`.** `seen_one_side` members are counted as agreeing or disagreeing (`n_one_side_agree`,
  `n_one_side_disagree`). They are never folded into β̄.

**`smallest_margin_passed`**: the smallest δ (or f, for `attenuated_*`) at which the unadjusted interval rule would
pass:
- `unchanged`: max(|low|, |high|);
- `not_up`: max(high, 0);
- `not_down`: max(−low, 0);
- `attenuated_down`: low / m̄, when high < 0 (otherwise no f passes, and the cell is empty);
- `attenuated_up`: high / m̄, when low > 0 (likewise).

It is empty for `up` and `down`.

#### `DEF-DIFF-SET-POOL`: one hypothesis, several datasets

- **Reading `independence`** (RULED 2026-10-19, user; hypotheses-v1 writes 21 variants of the two words).
  - A value beginning `independent` is independent; the rest of the value is kept as text.
  - A value containing `reproduces` (`probably reproduces [102]` included) is reproduction.
  - Any other value (`weak (not a test)`, `not suited (secretome)`) is reported and never pooled.
  - **A dataset contrast is independent for a part only if every one of its member rows is.** A set result that is
    partly reproduction is not independent evidence.
- **Only the hypothesis's `independent` datasets are pooled**, at most one contrast each.
  - When `tests.tsv` names several contrasts of one dataset for a hypothesis, each is reported.
  - The one marked `primary = yes` is the one pooled.
  - With no such mark, **that dataset is left out of the pool**: its contrasts are reported apart
    (`verdict_detail` on each says `several_contrasts_per_dataset`). The hypothesis still pools its other independent
    datasets.
- **How they are pooled:**
  - random effects, with the DerSimonian-Laird between-dataset variance (mzLib `RandomEffectsMeta`);
  - with the Hartung-Knapp variance and t(k − 1) degrees of freedom when k ≥ 2 (IntHout et al. 2014);
  - with k = 1, the dataset's own result is the primary.
- **The pooled row gets the same verdict rules,** with its own df.
- **Beside it, never as the primary:**
  - every dataset's own row, with its p adjusted by Benjamini-Bogomolov (2014) when the hypothesis was selected: BH
    within the hypothesis, compared at 0.05 × R / m, where R of the family's m hypotheses were `supported`;
  - `n_datasets_agree`: datasets whose interval lies on the predicted side of the bound;
  - with n ≥ 2 datasets, a "supported in at least 2" p: Fisher's combination of the n − 1 largest per-dataset p's
    (Benjamini & Heller 2008).
- **Reproduction and unpooled datasets** are run and reported like any other, marked `reproduction` or `not_pooled`.
  They are never pooled and never in the family.

#### `DEF-DIFF-SET-FAMILY`: multiple testing

- **One Benjamini-Hochberg family per (freeze, quant basis).** It holds the primary p of every hypothesis with
  `post_hoc = no` and a primary result (pooled, or the one dataset's).
- **The level is 0.05.**
- **`post_hoc` hypotheses** are computed and reported with `in_family = false` and an empty adjusted p.

#### `DEF-DIFF-SET-BACKGROUND`: the depth shift, shown and not tested

- **Each tested member's background:**
  - the median STAT1 `log2_effect` (same stratum, contrast, quant basis), over STAT1's fitted rows outside the set;
  - restricted to rows in the member's **abundance quartile** (mean normalized log2 intensity over the samples with a
    value; quartiles over the fitted rows) and **completeness class** (a value in every sample of the contrast, or not).
- **The set's background** is the equal-weight mean of its members' backgrounds. `set_minus_background` = β̄ minus it.
- **It has no p, no verdict and no place in the family.** It shows when a whole abundance band moved (aging's D57).

#### `DEF-DIFF-SET-FILES`: what is written

- **`SetResults.tsv`, one row per (hypothesis, quant basis, level).** `level` is `dataset` (one per dataset contrast)
  or `pooled`.
- **`SetMembers.tsv`, one row per (hypothesis part, member, dataset contrast, quant basis).**
- **`SetResults.metadata.json`:**
  - `definition_version` = `DEF-DIFF-SET v1`;
  - the inputs: the `tests.tsv` sha256 and freeze tag, each dataset's STAT1 `analysis_id`, each database's sha256;
  - the settings: the α of 0.05, the default δ and f, the completeness share (half, at least 2), the minimum of 3
    tested members, the quant bases;
  - the families with their sizes; the row counts by verdict; both names of every column.
- **File rules as `DEF-DIFF-FILE`.** Empty means missing, and a `0` is a value. Columns are matched by header name,
  with a machine name and a human-readable name each (GR-13).

`SetResults.tsv`:

| machine name | human-readable name | meaning |
|---|---|---|
| `definition_id` | Definition ID | `QuantProject:DEF-DIFF-SET v1` |
| `tests_sha256`, `freeze` | Tests SHA-256, Freeze | the frozen `tests.tsv` and its tag |
| `hypothesis_id`, `kind`, `prediction` | Hypothesis, Kind, Prediction | from `tests.tsv` |
| `level` | Level | `dataset` or `pooled` |
| `dataset`, `stratum`, `contrast_label`, `numerator`, `denominator`, `contexts` | Dataset, Stratum, Contrast, Numerator, Denominator, Contexts | the dataset contrast; empty on a pooled row except `contrast_label` |
| `independence`, `post_hoc` | Independence, Post Hoc | from `tests.tsv`; `reproduction` rows never pool |
| `quant_basis` | Quantification Basis | as `DEF-DIFF-COLUMNS` |
| `set_log2_effect` | Set Log2 Effect | β̄: the equal-weight average of the members' log2 effects (for `single`, the member's) |
| `se`, `df`, `df_method` | Standard Error, Degrees of Freedom, DF Method | `df_method`: `satterthwaite` (set model), `satterthwaite_moderated` or `moderated_residual` (a single's STAT1 row), `hartung_knapp` (pooled) |
| `ci90_low`, `ci90_high` | 90% CI Lower, 90% CI Upper | `set_log2_effect ± t(df, 0.95) × se` |
| `margin_log2`, `attenuation_fraction`, `mrna_log2_mean` | Margin (Log2), Attenuation Fraction, mRNA Log2 Mean | δ, f, m̄ as used; empty where the prediction has none |
| `bound` | Tested Bound | the null hypothesis's boundary or boundaries: 0, +δ, −δ, ±δ, or 0 and f·m̄ |
| `p_value` | P-Value | `DEF-DIFF-SET-VERDICT` |
| `p_adjusted`, `in_family`, `family_size` | Adjusted P-Value, In Family, Family Size | primary rows only (Benjamini-Hochberg); dataset rows of a selected hypothesis carry the Benjamini-Bogomolov value and level |
| `bb_level` | Benjamini-Bogomolov Level | dataset rows: 0.05 × R / m when the hypothesis was selected; empty otherwise |
| `smallest_margin_passed` | Smallest Margin Passed | `DEF-DIFF-SET-VERDICT` |
| `verdict`, `verdict_detail` | Verdict, Verdict Detail | `supported`, `contradicted`, `not_informative`, `not_testable`, `not_run`; the detail names the rule, guard or reason |
| `n_members`, `n_tested` | Members, Members Tested | members listed for the hypothesis; those in β̄ |
| `n_seen_numerator_only`, `n_seen_denominator_only`, `n_one_side_agree`, `n_one_side_disagree` | Seen In Numerator Only, Seen In Denominator Only, One-Side Agreeing, One-Side Disagreeing | `seen_one_side` members |
| `n_too_few`, `n_incomplete`, `n_shared_group`, `n_no_group`, `n_not_in_rowset`, `n_unmapped` | (each as named) | members by `member_state` |
| `n_datasets_pooled`, `tau2`, `n_datasets_agree`, `p_supported_in_2` | Datasets Pooled, Between-Dataset Variance, Datasets Agreeing, P (Supported In At Least 2) | pooled rows only |
| `background_log2`, `set_minus_background` | Background Log2 Effect, Set Minus Background | `DEF-DIFF-SET-BACKGROUND`; dataset rows |
| `model_used`, `random_terms`, `n_peptides`, `n_observations`, `normalization`, `method_version` | Model Used, Random Terms, Peptides, Peptide-Sample Values, Normalization, Method Version | `set_mixed_model`, `stat1_row` or `random_effects_hartung_knapp`; e.g. `sample;sample:member`; as `DEF-DIFF-COLUMNS` |

`SetMembers.tsv`:

| machine name | human-readable name | meaning |
|---|---|---|
| `definition_id`, `tests_sha256`, `hypothesis_id`, `prediction`, `member`, `dataset`, `stratum`, `contrast_label`, `quant_basis` | (as above) | the key; one member can sit in two parts (hypotheses-v1's H14: C4b `up` and `unchanged`) |
| `member_accessions_used` | Member Accessions | the accessions that defined the member's gene, `;`-joined, ordinal-sorted |
| `member_state` | Member State | `DEF-DIFF-SET-MEMBER` |
| `protein_group`, `group_genes`, `other_groups` | Protein Group, Group Genes, Other Groups | the chosen group (STAT1's `feature_id`), all its genes, the groups not chosen |
| `in_set_estimate` | In Set Estimate | `true` for a `tested` member of a set |
| `stat1_log2_effect`, `stat1_se`, `stat1_df`, `stat1_status` | STAT1 Log2 Effect, STAT1 Standard Error, STAT1 Degrees of Freedom, STAT1 Status | the member's own STAT1 row, copied |
| `n_samples_numerator`, `n_samples_denominator`, `n_samples_total` | (as `DEF-DIFF-COLUMNS`) | from STAT1's row |
| `background_log2`, `mrna_log2` | Background Log2 Effect, mRNA Log2 | the member's background; its frozen mRNA effect |

#### Open points for the walk-through (proposed default first)

1. **Quant basis. RULED 2026-10-19 (user): both, for now; revisit in several weeks.**
   - STAT1 writes `msms_only` and `mbr_kept` (ST-15).
   - Each basis gets its own verdicts and its own Benjamini-Hochberg family, as `DEF-DIFF-SET-FAMILY` already keys
     families by quant basis.
   - The recommendation was `msms_only` alone for the verdicts, because match-between-runs transfers are not yet
     stable (mzLib #1484: a few unrelated donor peptides change a fifth to a third of accepted transfers).
   - That is the question to revisit.
2. **Contexts. RULED 2026-10-19 (user): follow STAT1.**
   - Stratum factors select one stratum.
   - Other factors are adjusted for, not pooled (above).
   - "Each context on its own" for a non-stratum factor (a per-sex result) is not in v1; it needs the per-level
     contrasts of gap AGESEX1.
3. **The completeness guard. RULED 2026-10-19 (user): any `incomplete` member makes a no-change verdict
   `not_informative`.** The alternative, leaving incomplete members out of β̄, was declined: it keeps more sets testable
   but tilts β̄ toward abundant members.
4. **`contradicted` is not adjusted for multiplicity. RULED 2026-10-19 (user): as drafted, labelled `uncorrected`.**
   The family controls false `supported` calls, which are what "N of M predictions held" counts.
5. **No flag on the background. RULED 2026-10-19 (user): numbers only in v1**, revisited once real background values
   have been seen.
6. **The minimum of 3 tested members. RULED 2026-10-19 (user): 3**, matching aging's scorecard.
7. **A `single` uses STAT1's moderated row. RULED 2026-10-19 (user): as drafted.** A set's model has no moderation.
8. **Several contrasts of one dataset for one hypothesis. RULED 2026-10-19 (user): each is reported, and that dataset is
   left out of the pool**, unless `tests.tsv` marks one of them `primary = yes` (ask aging to add the column).
   - First ruled as "the pooled row is not run". It was narrowed the same day on hypotheses-v1, where H1, H3 and H4 each
     list two contrasts of PXD031782 and would otherwise get no pooled verdict.
   - Pooling within a dataset first was declined: it needs a model of the contrasts' correlation.
   - Pooling the first listed contrast was declined: file order would decide.

## Ledger

| item | us |
|---|---|
| (status) | DATA-DEFINITIONS v3.12 posted: `DEF-DIFF-SET` (contract; nothing writes it yet) |
| (finding) | `protein_genes` leaves 303 of 4,374 quantified groups in PXD057407 without a gene (6.9%); not investigated by us |
