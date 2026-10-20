# The ptmQtl engines in `datarepo run` (plan)

**Status: built on branch `feat/ptmqtl-engine` (2026-10-06), merged into `feat/1.4.0-ingest` on 2026-10-19, not
released.** Approved by the user on 2026-10-06 (ptmQtl 025 -> our 026, DATAREPO-P21..P23). dataRepo wrote
`PtmQtlCore.cs`, `PtmQtlBundle.cs`, `PtmQtlEngine.cs` and `CatalogPtmQtl.cs` in C#. ptmQtl owns the method: the
definitions, the mzLib code, and review of the PR.
- **It reproduces ptmQtl's reference case exactly** (`Fixtures/ptmqtl-reference-v1`), now on the released mzLib
  1.0.595, which carries #1430. It is built against 1.0.595, not 1.0.594: #1446 added two optional parameters to
  `PtmPairs.CoVarying`, so a binary compiled against 1.0.594 throws `MissingMethodException` there (ptmQtl 046).
- **It ran on aging's PXD035107 and PXD017944 bundles** (scratch store, on the branch).
- The branch's `dotnet/nuget.config` and pre-release mzLib reference were dropped at the merge. #1403 moves no
  ingested row (measured 2026-10-19: our peptidoform keys are our own ProForma), but 1.4.0 has a new ingest path
  anyway (`cs-1.2.0`, schema 0.0.16) and aging re-ingests once.
- In a catalog folder `ptm_pairs` and `trait_effects` are views over the artefacts' Parquet, as go's tables are,
  checked from the files' footers. The catalog format is 14, which also covers schema 0.0.16.
- **The engines take ptmQtl's changes since 2026-10-06 (G99), built 2026-10-19** (`ccf7acf`, `aee05bf`):
  - S7's quantified-PSM rule;
  - DATAREPO-P32's pooled samples;
  - D35's window check in pooling, with a protein N-terminal site taking residue 1's window at ingest;
  - every database in `run.json`;
  - S2c and S2d, with `excluded_sites.tsv`;
  - S3b's sample types, from the capture list v4 and `runs.enrichment`.
  - **Not built:**
    - DEF-SITE-TRAIT v2: mzLib 1.0.595 lacks #1464, so the rows stay v1, as G99 ties the version to the release.
    - The bounds (their D37, D39-D49): their mzLib change, G46; the ceiling rule is frozen, not extended.
    - Bait runs of a pulldown (aging's `curated_design_factors`).

## The operator's lists (G99)

Every `ptmqtl.*` run takes three lists, hashed into each artefact. A pooled result, and a catalog, takes one set.

| input | file | columns |
|---|---|---|
| `enrichment` | ptmQtl's capture list (`results/ptm_enriched_v4/deposits.tsv`) | `dataset`, `class` = `ptm_capture` / `capture_runs` / `held` / `no_ptm_capture`; a list with no `class` (v1-v3) names PTM captures |
| `capture_runs` | its `capture_runs.tsv`; needed for any `capture_runs` deposit | `dataset`, `run_id` |
| `cysteine` | S2d's deposits (required) | `dataset`, `class` = `nem` / `cysteine_poor`, `reason` (the reagent; optional) |

## Questions for ptmQtl, with the defaults built (G99, 2026-10-19)

Read off ptmQtl's own code on 2026-10-19 (`g40_blocking_rule_v2`, `g39_cysteine_rule_v2`, `export_observations.py`,
the runner's `Program.cs`). The engines follow DEFINITIONS.md. Where it is silent they follow the code, and where the
two disagree they follow the definitions. Each default below holds until ptmQtl answers.

**Measured 2026-10-19 on re-ingested bundles (`ptmqtl_check`, scratch):** each rule reproduces ptmQtl's own exclusion
list exactly.
- S2c: PXD018545 53/53 and PXD027754 28/28, against `g40_blocking_rule_v2`.
- S2d, against `g39_cysteine_rule_v2`:
  - (a), NEM: PXD047288, 109/109 places;
  - (a), cysteine-poor: PXD057490, 424/424;
  - (b): PXD057490 10/10 and PXD009212 114/114.
- Two fixes came from that comparison.
  - An NEM deposit also loses its residue cysteine sites that no passing PSM covers, as `measure.py`'s `covered | on_c`
    does (aging's S76).
  - S2d (b) leaves out only stored sites of the modification.

**ptmQtl's first answers (session message, 2026-10-19), pending their user's rulings:**
- PXD011740: corrected by ptmQtl the same day. Their D56 applies S2d (a) to the whole deposit on purpose, not only its
  six NEM runs (sample1-sample6): the exclusion list is per site, so this is the safer error. A deposit-level cysteine
  list matches what they ran.
- **Ruled, their D57 (their user, 2026-10-19), S7 "Name":** a peptidoform with several `engine_full_sequences` is kept
  under its first name when every name is the same modifications at the same positions; otherwise it is left out and
  counted.
  - The test is mzLib's sequence converter (`Omics.SequenceConversion`): the names' mzLib-to-Unimod forms must agree.
    A name with no UNIMOD form must resolve every modification, through `MzLibModificationLookup` and then
    `GlobalModificationLookup`, to the same chemical formula at the same position.
  - Isomers pass and are counted apart. MetaMorpheus #2917's `|`-joined rows, stored as several names, are left out.
  - **Built**, mirroring their runner (`tools/PtmQtlRunner`, ptmQtl `19a8340`): `PtmQtlRules.SameModifications`.
    `run.json` carries their three counters, which count distinct name combinations, not rows:
    `several_names_kept_unimod`, `several_names_kept_formula` and `several_names_left_out`. On PXD011740 one
    combination is kept by its Unimod form, six observations.
- Hydroxybutyryl-K is in S2d (b) on purpose: it is ring-opened NEM, +86.036. 2-hydroxyisobutyryl-K has the same
  composition, so the mass match takes it too.
- S2c (question 1): `utyryl` takes hydroxybutyryl-K and 2-hydroxyisobutyryl-K by intent. Trypsin cannot cut after a
  lysine whose ε-amine is acylated, so DEFINITIONS is the one that is incomplete.
  - Neither the code nor the definitions catch six more acyl-K names: N6-isonicotinyl, N6-methacryl, N6-benzoyl,
    N6-propionyl, N6-biotinyl and N6-lipoyl. On catalog 9f943cd4 these are 298, 274, 102, 72, 57 and 54 sites.
  - Whether S2c grows to take them is their user's call. The engines keep the code's patterns until the thread
    answers.
- New: in PXD008934, 72 % of methyl-K/R PSMs also carry a carbamyl. Carbamyl plus methyl is carbamidomethyl,
  iodoacetamide over-alkylation split in two. Whether it becomes an S2 rule is their user's call; nothing is built.

1. **S2c's names.** `measure.py`'s `utyryl` also takes hydroxybutyryl-K and 2-hydroxyisobutyryl-K; DEFINITIONS lists
   only butyryl. *Default: the code's patterns.*
2. **Do S2c's and S2d's site exclusions reach type P?** DEFINITIONS reads them as site rules; the runner removes
   occupancy cells only (`Program.cs:143-144`), so type P is 27,271 rows in all three of its runs. *Default:*
   - type A and site-trait fits only;
   - except S2d (a)'s explicit sentence, which is built: an NEM deposit's Cys-containing peptidoforms leave type P.
     The runner does not do this.
3. **S2d (a)'s NEM deposits.** DEFINITIONS lists 13. `measure.py` has 14, adding PXD011740 (your D56); no thread to us
   said so. *Default: whatever `--input cysteine` names.* We ask ptmQtl to publish the list as a TSV, as for the
   capture list.
4. **S2d (b)'s screen rounds the shares to 3 places;** DEFINITIONS does not. *Default: unrounded.*
5. **S2d (b)'s masses.** `measure.py` keeps three UNIMOD masses and one by name. *Default: mzLib's masses, from the
   MetaMorpheus install the search read.* Your measurement says this changes nothing on v2.
6. **S7.**
   - A peptidoform with several names: DEFINITIONS leaves it out and counts it; the export takes the first.
   - The previous residue M/X at residue 2: DEFINITIONS has it; the runner passes none.
   - *Default: the definitions, for both.*
7. **S3b.**
   - Bait runs are not selected yet, so a pulldown deposit has no type A or site-trait rows. That follows "until a
     deposit has that design". The nine all-bait pulldowns have no `pulldown` row at all: how should they be read?
   - Type P on capture and pulldown deposits: DEFINITIONS keeps it; the export drops every non-whole-proteome run, so
     those deposits have no type P. *Default: kept, from every run.*
8. **Pooling a deposit with some non-whole-proteome runs** (the five `capture_runs` deposits). *Default: none of its
   rows pool.* The alternative is to pool its type A rows, which read whole-proteome runs only.
9. **S2c's evidence runs.** Every observation of the deposit is read; `measure.py` read the exported whole-proteome
   runs only. *Default: every run* (more evidence is the safer error).
10. **For information:**
    - The runner implements neither D35 nor P32.
    - It writes `meta:human`, not `meta:NCBITaxon:<taxid>`; `export_to_datarepo.py` still writes DEF-PTM-PAIR v1.
    - S7's tier is read on target PSMs, PEPs included, as DEFINITIONS and the export have it. mzLib's own FlashLFQ
      caller passes decoy PEPs too.
11. **Our ptmQtl 040 was wrong on the N-terminal window.** It said a protein N-terminal site sits on residue 1. Once
    the initiator Met is removed it is keyed on residue 2 (377 of PXD022196's 494). It now takes residue 1's window, as
    D35 says.

**Superseded below:** S2 is now four categories minus ptmQtl D27's two exclusions (ptmQtl 030, `DEFINITIONS.md`). The
engine takes it from there, not from the two-category text in "Three gates".

## Engines

| engine | unit | writes |
|---|---|---|
| `ptmqtl.site_pairs` | one bundle (one search) | `ptm_pairs`, scope = dataset |
| `ptmqtl.site_traits` | one bundle x one trait | `trait_effects` |
| `ptmqtl.pool_pairs` | one species, over its `site_pairs` artefacts by id and sha256 (P22) | `ptm_pairs`, scope = `meta:<species>` |

Each one calls `Quantification.PtmQtl` and `StatisticalModels` from a released mzLib (1.0.594 or later). Each
computes nothing that mzLib does not, and refuses rows that do not keep ptmQtl's definition. Pooling never
happens at `build`.

## Preconditions: it refuses until all of these hold (like go before GO-D4)

| # | item | owner | state (2026-10-06) |
|---|---|---|---|
| G35 | `ptmQtl:DEF-PTM-PAIR v2` and `ptmQtl:DEF-SITE-TRAIT`, with the column contracts for `ptm_pairs` and `trait_effects` | ptmQtl | to come; they measure the D26 change first |
| G36a | combining fractions per sample (their G32): `SiteOccupancyCalculator.CombineRuns` | ptmQtl | mzLib #1430 open; needs a release |
| G36b | protein N-termini after initiator-Met removal (their G20) | MetaMorpheus | #1337 is in mzLib 1.0.592; a MetaMorpheus release carrying it is missing. For the engine this is a **search-version gate**, below |
| G37 | a reference case per engine (inputs and expected rows) | ptmQtl | follows the definitions |

## Inputs, all from one stored bundle

The same facts ptmQtl's glue (`tools/export_observations.py`) took from a catalog:
- **Observations** per (run, peptidoform, protein): target PSMs at q <= 0.01, ambiguity level 1, single-accession,
  one start (`psms`).
  - The full sequence comes from `peptidoforms.engine_full_sequences`, in MetaMorpheus notation with its category.
  - The intensity is `quant_values` `QuantProject:DEF-PEP-INT`, detection type MSMS, value > 0. Otherwise it is
    NaN: identified, not quantified. MBR is never used.
- **Occupancy:** `ptm_stoichiometry` per run (label-free assays) joined to `ptm_sites` at level-1 target sites.
  States are never collapsed. `intensity_unassigned` has no engine state and is counted, not read.
- **Species** for pooling: `datasets.organisms`.

## Three gates

1. **Biological modifications (the user's ruling, our ptmQtl 027; their D26).**
   - The rule: the mzLib category is `Common Biological` or `UniProt`, the prefix MetaMorpheus writes on every
     modification name (`Modification.ModificationType`; `ModificationSite.Category` in PtmQtl).
   - An occupancy site takes its category from the peptidoforms covering it. No IdWithMotif-to-class table is kept
     here (ptmQtl's `mod_class.tsv` retires).
2. **PTM-enriched deposits (D24).** An operator `--input` role, hashed into every artefact id (P23).
   - Such a deposit gets no co-varying (type A) pairs and no site-trait fits. Same-molecule (type P) pairs stay.
   - The role retires when the manifest field of DATAREPO-P20 exists (after aging's AGING-P14).
3. **Search version (G20).** A search whose MetaMorpheus carries mzLib older than 1.0.592 wrote no occupancy for
   protein N-termini after initiator-Met removal.
   - Such a bundle's results are marked as lacking those sites, from its `search_engine_version`.
   - Nothing is filled in. ptmQtl's runner filled them from its own calculation; this engine does not.
   - aging's re-search on a MetaMorpheus release carrying #1337 closes it.

## Rules carried over from the other engines

- `pool_pairs` refuses mixed inputs: two definition versions, or two enrichment gates, among the pooled `site_pairs`
  artefacts (as GO-D9).
- Every input is checked by role and sha256, refused if a bundle's recorded file no longer hashes. Artefacts are
  content-addressed, and a development build is refused.
