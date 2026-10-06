# The ptmQtl engines in `datarepo run` (plan)

**Status: planned, not built.** Approved by the user on 2026-10-06 (ptmQtl 025 -> our 026, DATAREPO-P21..P23).
dataRepo writes `PtmQtlEngine.cs` in C#. ptmQtl owns the method: the definitions, the mzLib code, and review of the PR.

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
