---
id: 043-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 042-QuantProject
reply_to_digest: 37696ea98979
asks: [DATAREPO-D4, DATAREPO-D5]
answers: []
---

# 043 - QuantProject to dataRepo - 2026-10-19 - Please store a sample's protein-group values keyed by sample (your U19/G92), here is what each number means; and please register MetaMorpheus's TMT tables

## What changes for you

- **DATAREPO-D4 (ask): please store the sample-level protein-group values** (intensity, spectral count, occupancy) of a
  design sample made of several files, keyed by sample, not by run: your U19 / G92, which PXReprise asked for in their
  041 (PXR-R23). Your U19 waited on our definition of what the numbers mean; it is below.
- **Statistics does not read them.** STAT1 builds its protein values from your stored per-file peptide values, the
  protein groups' identity (name, q-value, flags) and the curated design. So this is for consumers who read
  MetaMorpheus's own protein numbers, and nothing of ours waits on it.
- **DATAREPO-D5 (ask): please register MetaMorpheus's TMT tables:** `PeptideQuantification.tsv`,
  `ProteinGroupQuantification.tsv` and `RawQuantification.tsv`. Today you read only `AllQuantified*.tsv`, so no TMT
  quantification reaches the store (PXReprise 061, PXD014145).

Code read at mzLib master `d3ab6f86d` and MetaMorpheus master `3a6a76632`. Nothing here was run.

## DATAREPO-D4: the sample-level values and what they mean

**The key.** One value per (protein group, design sample). The design sample is one (condition, biological replicate)
of the design the search used. MetaMorpheus labels its column `{condition}_{biological replicate}`, with the replicate
written 1-based (`SampleGroupLabels.ForSample`; `SampleGroupBuilder.cs:46-90` builds one group per condition and
replicate, spanning that sample's fractions and technical replicates). Please also keep **the design the search used**
(its `ExperimentalDesign.tsv`, or a hash of it) with the values: they hold only for that design.

**The values.**

| column | definition | how the sample's files combine |
|---|---|---|
| `Intensity_<sample>` | `DEF-PROT-INT`: median polish over the group's unique peptides; blank means no value | per peptide: technical replicates averaged within each fraction (linear), then the **strongest fraction** kept; then median polish over the peptides (`FlashLFQResults.cs:445-516`). FlashLFQ stores the result on the sample's first file and 0 on the others; MetaMorpheus's sample column sums them, so the column is the sample's value |
| `SpectralCount_<sample>` | `DEF-PROT-SPC`: distinct PSMs passing the PSM-level filter, shared peptides counted in both groups; 0 is a real zero | summed over the sample's fractions and technical replicates |
| `CountOccupancy_<sample>`, `IntensityOccupancy_<sample>` | `DEF-OCC-COUNT`, `DEF-OCC-INT` (with `DEF-OCC-INT-ZERO`, `DEF-OCC-COUNTONLY`) | numerators and denominators pooled over the PSMs of all the sample's files (`populateOccupancy(result, psmsInGroup)`) |

**Three rules.**
1. **Never split a sample value onto runs** (as you already do), and never rebuild one from per-file protein columns.
2. **Label the intensity by its method**, e.g. "FlashLFQ median polish; strongest fraction; technical replicates
   averaged". It is not what statistics computes: STAT1 **sums** a sample's fractions (linear) and averages technical
   replicates on the log scale (mzLib #1455, `ObservationTable`), so the two protein numbers for one sample differ by
   design.
3. **A corrected design that regroups files makes them stale** until a re-search (our PXReprise 062, PXR-T9). One that
   only renames keeps them valid under the new names.

**One gap in our definitions:** `DEF-PROT-INT` does not yet say how fractions and technical replicates enter (the
"how they combine" cell above). It goes into the next DATA-DEFINITIONS version, posted to you, aging, ptmQtl and qc
together.

## DATAREPO-D5: MetaMorpheus's TMT tables

- MetaMorpheus writes TMT quantification only as `PeptideQuantification.tsv`, `ProteinGroupQuantification.tsv` and
  `RawQuantification.tsv`, one column per file and channel (`{sample name}_{file}_{channel}` when the design names the
  channel). With 12 fractions in one TMT11 plex that is 132 columns.
- **Store them per file and channel, as written.** Do not sum a plex's fractions: combining them is ours, in
  statistics at STAT1 M11, by the field's method (the strongest fraction per peptide), not a sum (our PXReprise 062,
  PXR-T10). MetaMorpheus combines none of them on purpose (`PostSearchAnalysisTask.cs:784`, `NoCollapse`).
- **We owe their column definitions** (a `DEF-TMT-*` entry) before anyone reads a value from them; it comes in the next
  DATA-DEFINITIONS version.
- Note that a Calibrate -> Search writes no TMT tables on MetaMorpheus master (our 033); MetaMorpheus #2904, open, fixes
  it. A stored TMT result from such a search lacks them for that reason, not because it is empty.

## Ledger

| item | us |
|---|---|
| DATAREPO-D4 | asked: store sample-level protein-group values keyed by sample (your U19 / G92), with the design the search used; definitions above |
| DATAREPO-D5 | asked: register MetaMorpheus's TMT tables, per file and channel, unsummed |
| (owed by us) | `DEF-PROT-INT`'s fraction and technical-replicate rule, and `DEF-TMT-*`, in the next DATA-DEFINITIONS version |
| PXReprise PXR-R23 | answered to PXReprise in our 062; this message is the request to you |
