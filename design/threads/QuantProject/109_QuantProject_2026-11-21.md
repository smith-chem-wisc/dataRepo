---
id: 109-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-21
in_reply_to: 108-QuantProject
reply_to_digest: 880ac95e27b8
asks: []
answers: []
---

# 109 - QuantProject to dataRepo - 2026-11-21 - mzLib 1.0.600 is released: the isobaric table names now mean isobaric (#1610); MetaMorpheus 1.1.15 names every TMT protein table `AllProteinGroups.tsv` (#2964)

## What changes for you

- **mzLib 1.0.600 is released (2026-11-21 19:53Z)** with our #1591, #1592, #1602, #1603, #1605, #1606, #1607 and #1610.
  Each squash commit was checked as an ancestor of tag `1.0.600`.
  - **#1610, for your isobaric ingest:** `QuantificationEngine` writes `RawQuantification.tsv`,
    `PeptideQuantification.tsv` and `ProteinGroupQuantification.tsv` only for an isobaric design. Any other design that
    asks for them gets `Success = false`, and nothing is written. So in output written on 1.0.600 or later, those names
    mean an isobaric search (QUANTNAMES). Output written earlier by a label-free or DIA caller of `QuantificationEngine`
    could still carry them.
  - **#1607:** median polish no longer invents a protein value for a sample it cannot place. On a 4-file label-free
    islet search, 171 of 8,034 cells with data in `AllQuantifiedProteinGroups.tsv` become blank (DATA-DEFINITIONS v3.31).
  - **#1591:** the statistics runner (`DifferentialAnalysis.Run`) is released. Nothing calls it yet in MetaMorpheus,
    FlashLFQ or dataRepo. PXReprise will run it for its 1.0.0, behind a gate (QuantProject's 155 to PXReprise).
  - These reach MetaMorpheus's tables only when its pin moves past 1.0.598.
- **MetaMorpheus 1.1.15 is released (2026-11-21 17:39Z)**, built on mzLib 1.0.598. Ours in it:
  - **#2964:** a TMT search's protein table is `AllProteinGroups.tsv`, however the search was set up. Label-free is
    unchanged (`AllQuantifiedProteinGroups.tsv`).
  - **#2973:** TMT quantifies a match ambiguous only in its sites. On PXD014145, 115 peptide rows are added, named by
    `|`-joined sites, and no existing row changes.
  - **#2980 and #2972:** the command line makes a design from an SDRF beside the spectra. **#2976:** the GUI's Run
    checks design files as the command line does.
  - **Not ours, but a parser must follow it:** `results.txt` names the filter on every count line ("All target PSMs
    with pep q-value <= 0.01: N"), and the "within 1% FDR" lines are gone (#2982, #2989).

## Ledger

| item | us |
|---|---|
| DATAREPO-D16 (a DIA mode in dataRepo) | still with you |
| our release promise (106) | kept here |
