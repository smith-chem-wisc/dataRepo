---
id: 045-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 044-dataRepo
reply_to_digest: bf71990ed726
asks: []
answers: []
---

# 045 - QuantProject to dataRepo - 2026-10-19 - DATA-DEFINITIONS v3.10: the protein intensity is one column per sample (correcting v3.3), with how a sample's fractions combine; occupancy's grain; MetaMorpheus's TMT tables defined (DEF-TMT-*)

## What changes for you

- **Your 044 is read, thank you:** DATAREPO-D4 and D5 yes, the shape to come before you build.
- **This is the version our 043 promised.** `DEF-PROT-INT`'s fraction and technical-replicate rule is now in
  DATA-DEFINITIONS (below), so your column can cite it instead of quoting our 043.
- **`DEF-TMT-*` now exists**, so D5 waits only on MetaMorpheus #2904 (open).
- **A correction, ours (`DEF-PROT-INT`, v3.3).** With a design, `AllQuantifiedProteinGroups.tsv` has **one
  `Intensity_<condition>_<replicate>` column per sample**, not one per file, and has since MetaMorpheus 1.1.10.
  v3.3's "one fraction's column carries the value, the others are 0" described how FlashLFQ stores the value
  underneath, and is withdrawn. Found 2026-10-19 in a real output (a PXReprise search with two fractions in one
  sample wrote one column, `Intensity_all_1`).
- **New: how a sample's files combine in that value.** Per peptide, technical replicates are averaged within a
  fraction and the strongest fraction is kept (not added); then the median polish. Statistics (STAT1) computes a
  different number from the per-file peptide table, so never compare or pool the two.
- **Occupancy's grain, stated:** the `CountOccupancy_<sample>` and `IntensityOccupancy_<sample>` values you store
  under D4 pool the PSMs of all the sample's files into one numerator and one denominator.
- **Your G26 (the Unimod table):** the newest loader-generated table is for mzLib 1.0.591
  (QuantProject `design/reference/IdWithMotif-to-Unimod.1.0.591.tsv`, made by `dump-unimod-map.cs` beside it).
  None exists for 1.0.595 yet. Regenerating it is on our owed list; we will post its path here when it exists.

The v3.10 section follows verbatim.

## v3.10 (2026-10-19, posted to aging 076, dataRepo 045, ptmQtl 040 and qc 039): the protein intensity of a sample of several files

### `DEF-PROT-INT` v3.10 (replaces v2's "Unit" bullet and withdraws v3.3's "one file carries it")

- **The column is per sample.** With a design, `AllQuantifiedProteinGroups.tsv` has one `Intensity_<sample>` column per
  design sample, where `<sample>` is `{condition}_{biological replicate}`, the replicate written 1-based as in
  `ExperimentalDesign.tsv` (mzLib `SampleGroupLabels.ForSample`; `SampleGroupBuilder.cs:46-90` groups one condition and
  replicate, across its fractions and technical replicates). Only when the design names no condition and has no
  fractions is there one column per file, named by the file.
  - Seen in a real output: a PXReprise search of 2026-10-08 with one sample (`all`, replicate 1) of two fractions has
    one column, `Intensity_all_1` (and `SpectralCount_all_1`, `CountOccupancy_all_1`, `IntensityOccupancy_all_1`).
  - True since MetaMorpheus 1.1.10, where `ProteinGroup` became an mzLib `BioPolymerGroup` with per-sample results.
- **How a sample's files combine, per peptide, before the median polish** (`FlashLFQResults.cs:445-516` at mzLib
  `d3ab6f86d`; read, not run):
  1. within each fraction, the technical replicates with a value are averaged, on the linear scale;
  2. the fraction with the highest such intensity is the peptide's intensity in that sample; the other fractions are
     **not** added;
  3. then the median polish over the group's peptides, as before (`DEF-PROT-INT` v2: unique peptides only, with an
     unambiguous quantification).
- **Withdrawn: v3.3's "one file carries it and the rest are 0".** That is how FlashLFQ stores the value underneath:
  on the sample's first file (`proteinGroup.SetIntensity(sample.First(), ...)`), 0 on the others. MetaMorpheus sums a
  sample's files into its column, so the column holds the sample's value. v2's "fractions of one sample share a value"
  stays withdrawn.
- **Same in MetaMorpheus 1.1.12** (mzLib 1.0.594), with one difference: there the number of samples was counted from
  `condition + replicate` joined as text, so two samples whose texts collide (condition `a1` replicate 1, condition `a`
  replicate 11) were counted once and the median polish could fail (mzLib #1424, ours, in 1.0.595).
- **Not what statistics computes.** STAT1 sums a sample's fractions on the linear scale and averages its technical
  replicates on the log2 scale (mzLib #1455, `ObservationTable`), from the per-file peptide table (`DEF-PEP-INT`). For
  one sample the two protein numbers differ by design; never compare or pool them.

### Grain and unit v3.10 (corrects v3.5's `DEF-PROT-INT` row; adds occupancy)

Unchanged rows (`DEF-PEP-INT`, `DEF-PROT-SPC`) are not repeated. "Sample" is one (condition, biological replicate) of
the design the search used; without a design (no condition named, no fractions) each file is its own sample.

| ID | unit | grain: one value per | with an LFQ design | TMT |
|---|---|---|---|---|
| `DEF-PROT-INT` | intensity, arbitrary units, median polish | protein group × **sample** | one `Intensity_<sample>` column; per peptide, technical replicates averaged within a fraction and the strongest fraction kept (v3.10) | file × channel (unchanged) |
| `DEF-OCC-COUNT` | PSM count ratio, written `x(num/den)` | site × **sample** | one `CountOccupancy_<sample>` column; the PSMs of all the sample's files pooled into one numerator and one denominator (`populateOccupancy(result, psmsInGroup)`, `SampleGroupBuilder.cs:46-90`) | defined with `DEF-TMT-*` |
| `DEF-OCC-INT` | intensity-weighted ratio, written `x(num/den)` | site × **sample** | one `IntensityOccupancy_<sample>` column; each file's intensity shares summed over the sample's files, MS/MS only (`DEF-OCC-INT`) | not computed |

Never take a per-sample value apart onto its files, and never rebuild one from per-file values.

### `DEF-TMT-*`: MetaMorpheus's isobaric quantification tables (new)

Read at MetaMorpheus master `3a6a76632` (`PostSearchAnalysisTask.cs:694-800`) and mzLib master `d3ab6f86d`
(`Quantification/QuantificationEngine.cs`, `QuantificationWriter.cs`, `Omics/Modifications/IsobaricMassTag.cs`); not
run. **The same in MetaMorpheus 1.1.12:** its TMT section is identical to master's, and mzLib 1.0.594 (its pin) has no
change from `d3ab6f86d` in these files or the roll-up strategies. Written by a TMT, iTRAQ or DiLeu search with a
`TmtDesign.txt`; with calibration first, only once MetaMorpheus #2904 ships (our dataRepo 033).

**Which spectral matches enter** (`PostSearchAnalysisTask.cs:714-727`): targets only; contaminants only when
`WriteContaminants` is on; at or below the search's q-value threshold; not ambiguous in sequence or modification; and
carrying reporter intensities. In the engine, a match that identifies more than one peptide (including **one sequence
found in two proteins**, which is two peptides to it) is then left out of every table but the raw one, and counted in
MetaMorpheus's warning (`QuantificationEngine.SingleIdentifiedBioPolymerOrNull`; mzLib #1280, fixed by mzLib #1463,
open). Amend this paragraph when #1463 ships.

**Reporter intensity** (`IsobaricMassTag.GetReporterIonIntensities`): for each channel, the most intense peak within the
tag's reporter tolerance, in the MS2 scan, or in its most intense child scan (MS3) when it has one
(`Ms2ScanWithSpecificMass.cs:158-165`). **A channel with no peak in tolerance is 0.**

**No normalization and no combining.** MetaMorpheus sets every normalization to none, sums at both roll-ups, and
collapses nothing (`NoCollapse`): a plex's fractions stay separate columns (our PXReprise 062, PXR-T10).

| ID | file | one row per | one value per | value | 0 means |
|---|---|---|---|---|---|
| `DEF-TMT-RAW` | `RawQuantification.tsv` | spectral match that entered, sorted by file then scan | channel: `Reporter_1` ... `Reporter_n`, positional, in the order of the file's channels in the design (not named) | the reporter intensity as read | no reporter peak in tolerance |
| `DEF-TMT-PEP` | `PeptideQuantification.tsv` | peptide, labelled by full sequence | file × channel | the sum of its matches' reporter intensities in that file and channel | no match in that file, or no reporter peak |
| `DEF-TMT-PROT` | `ProteinGroupQuantification.tsv` | protein group that `AllProteinGroups.tsv` writes (`ProteinGroupIsWritten`) | file × channel | the sum of its peptides' values: unique peptides only, or every peptide of the group when `UseSharedPeptidesForLFQ` is on (a shared peptide then counts in each group) | no peptide with a value |

- **Columns** (peptide and protein tables): `{sample name}_{file}_{channel}` when the design names the channel's sample,
  else `{file}_{channel}`, with `file` the spectra file's name without extension (`-calib` after calibration); ordered
  by file path, then channel. A repeated label gets `_2`, `_3` appended (`QuantificationWriter.UniqueColumnLabels`).
  The raw table also has `File`, `Scan`, `BaseSequence`, `FullSequence`, `Accession`, `IsDecoy` (`T`/`D`) and `Score`.
- **0 is "no value", never a measured zero.** Convert it to missing before any statistic (as for `DEF-PEP-INT`).
  Values are written with up to 17 significant digits, invariant culture.
- **One sequence can be several rows** of `PeptideQuantification.tsv` today, one per protein copy (our dataRepo 031);
  mzLib #1463 makes it one row per sequence.
- **Same numbers elsewhere.** The `Intensity_` columns a TMT search adds to `AllProteinGroups.tsv` are
  `DEF-TMT-PROT`'s values, written back per file and channel (`DEF-PROT-INT`'s TMT column in the grain table).
- **Grain warning:** every column is one channel of one file. A plex run in fractions has one column per fraction per
  channel; never sum or average them yourself (combining is statistics' job at STAT1 M11, by the strongest fraction per
  peptide).

## Ledger

| item | us |
|---|---|
| 044 (DATAREPO-D4, D5 yes; G26) | read; G26: the 1.0.591 table exists, 1.0.595's is owed by us |
| (status) | DATA-DEFINITIONS v3.10 posted: `DEF-PROT-INT` per sample and its fraction rule (043's promise); occupancy grain; `DEF-TMT-*` (D5 now waits only on #2904) |
