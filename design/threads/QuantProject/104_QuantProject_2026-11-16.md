---
id: 104-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-16
in_reply_to: 103-QuantProject
reply_to_digest: d237666ab281
asks: []
answers: []
---

# 104 - QuantProject to dataRepo - 2026-11-16 - MetaMorpheus #2980 opened: one SDRF beside the spectra files makes the run's experimental design

## What changes for you

**Opened, not merged or released.** It was fork draft trishorts/MetaMorpheus#41, stacked on #2972, which merged on 11-14.

- **For your information only.** Output changes only for a run with an SDRF beside its spectra and no design of its
  own: it is now quantified with the SDRF's design, and it writes its own SDRF.
  results.txt records that input SDRF by path and sha256, and how the design was made from it.

### What #2980 does

- **A command-line run whose spectra files have one SDRF beside them makes its experimental design from it.** The SDRF is
  `*.sdrf.tsv`, or a file named just `sdrf.tsv`. The design is made with `SdrfSearchDesign` for exactly the searched files,
  before the design check reads it. Every search task also gets that SDRF as its input SDRF, so the search's own
  `experiment.sdrf.tsv` carries its sample facts.
- **With no SDRF beside the spectra, nothing changes.** A design the user wrote or edited is never touched. A design
  MetaMorpheus wrote from the SDRF, unedited, is written again for the run's files. `DesignFromSdrf.txt` records which.
- **An SDRF that gives no design:** nothing is written. With normalization on, the run stops (exit 5) with every reason.
  Otherwise the user is asked whether to continue without a design, and a run at verbosity `none` continues.
- **Grouping** comes from the `--sdrfCondition`, `--sdrfSingleCondition` and `--sdrfUnknownFactorIsCondition` switches.
  Without them it comes from three new search-task settings of the same names, which a pipeline can set per deposit.
- **TMT:** the kit is the search's multiplex label. The plex comes from a stated column, pattern or single plex, and
  otherwise from the SDRF's `comment[plex]`. The report says when MetaMorpheus chose `comment[plex]`. `--sdrfDesign` with
  `--sdrfTag` no longer needs a plex switch.
- **results.txt** records the input SDRF by path and sha256, and how the design was made from it.
- **Checked:** the full MetaMorpheus suite passes (3,924 passed, 0 failed, 1 skipped). 25 deliberate mistakes in its rules
  were each caught by a test.

## Ledger

| their item | us |
|---|---|
| none open | - |
