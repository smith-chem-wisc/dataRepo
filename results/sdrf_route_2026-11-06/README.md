# Which SDRF reaches the catalog, and what it holds, 2026-11-06 (PXR-R52, PXR-F9; G127)

**Question:** what route do treatment conditions take into the catalog today, and is the search's own SDRF a usable record?
Told to sdrf in 034, PXReprise in 094, aging in 131.

**How:** every bundle in catalog `53f5ff162ba37e84` (196), read-only. `sdrf_route.py` reads each `bundle.json`, the SDRF that bundle read, and the search's
`experiment.sdrf.tsv`; `sdrf_five.py` looks at the five curated SDRFs below. Per deposit: `sdrf_route_by_deposit.tsv`. A value counts as real unless it is blank or a reserved word
(`not available`, `not applicable`, ...). A factor is "informative" with two or more real values.

## Which SDRF was read

| SDRF | deposits | factor values |
|---:|---:|---|
| none | 151 | none |
| the deposit's own (`metadata`) | 31 | kept |
| the deposit SDRF the design came from | 1 | kept |
| a question's SDRF the design came from | 6 | left out |
| `operator_sdrf` | 7 | left out |

## Treatments

- **In bundles:** `characteristics[treatment]` on one deposit, PXD056433 (`naive`, `trained`, 20 samples), from a curated SDRF whose factor values were left out. So the route works with no
  study layer. It is not on sdrf's hold list (`results/treatment-2026-11-06/blocking.txt` in their repo).
- **In aging's study layer:** the `treatment` factor on 6 deposits; design factors on 65 (2,144 rows); curated characteristics on 104.
- **`samples.condition`** is filled only from `characteristics[disease]` (`Sdrf.cs:277`), and has a value on 5 of 196 deposits, each a disease. Its description says "e.g. HGPS, caloric restriction", which is wrong.

## Curated factor columns

Of the 13 left out, 11 have an informative factor. On 6 a same-named characteristic exists (`age group`). On 5 none does:

| deposit | factor | values | elsewhere |
|---|---|---|---|
| PXD011740 | `compartment` | `cell layer`, `secretome` | only inside sample names |
| PXD022196 | `group` | `K0`, `WT`, `5-K0`, `5-WT` | only inside sample names |
| PXD002467 | `group` | 16, `CYT_BO` to `ER_LY` and more | only inside sample names |
| PXD006815 | `group` | `A`, `B` | study layer has `age group` |
| PXD056433 | `group` | `aged_trained`, ... | `characteristics[age group]` × `characteristics[treatment]`, nothing lost |

## The search's own SDRF

- `experiment.sdrf.tsv` is present on 186 of 196.
- Beyond organism, the only characteristic with a real value on any of them is `biological replicate`.
- Its factor column has one value on 174 and two or more on 12, and all 12 are among the 14 that read a curated or design SDRF (6 question, 5 `operator_sdrf`, 1 deposit).
- None of these searches set `InputSdrfPath`, so this says nothing about what one would hold when it does.
