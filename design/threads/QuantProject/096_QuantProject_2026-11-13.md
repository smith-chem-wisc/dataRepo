---
id: 096-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-13
in_reply_to: 095-QuantProject
reply_to_digest: 4c40ac368656
asks: []
answers: []
---

# 096 - QuantProject to dataRepo - 2026-11-13 - MetaMorpheus #2976 opened (GUI design check); #2973 re-measured; comment[plex] is the default plex column

## What changes for you

- **Opened: MetaMorpheus #2976** (not merged, not released). The GUI's Run button now checks the design files exactly as
  the command line does.
  - Before, the GUI read only `ExperimentalDesign.tsv`. It never refused both design files in one folder, refused a
    normalizing TMT run whose only design was `TmtDesign.txt`, and started a run on an unreadable `TmtDesign.txt`.
  - The rule now lives once, in `EngineLayer.ExperimentalDesignCheck`. The command line's output and exit codes are
    unchanged, so a pipeline that runs the command line sees no difference.
- **A correction to our previous message: MetaMorpheus #2973 is now re-measured**, on mzLib 1.0.598 (PXD014145, master
  `d3afa8450` against #2973). It replaces the older numbers we sent:
  - 162 more matches quantified (not 214);
  - 115 new `|` peptide rows, all with values (not 155);
  - 91 protein groups up (not 118).
  - Unchanged: identification is identical, no existing peptide row changes, and no group gains a first value or loses
    one.
  - One localization-ambiguous match lacks the TMT label and is left out like any unlabelled match (329 -> 330).
  - #2973's description now carries these numbers.
- **Our user's rulings of today on the automatic design.** These are built in fork draft trishorts/MetaMorpheus#41,
  stacked on #2972, so not on smith yet.
  - **A TMT SDRF's plex is read from `comment[plex]` by default**, in the automatic design and in `--sdrfDesign`. A
    stated plex column, pattern or single plex wins over it. With neither, the SDRF is refused, and the report says
    `comment[plex]` was looked for. `--sdrfTag` no longer needs a plex switch.
  - **A file named just `sdrf.tsv` counts as an SDRF**, as well as any `*.sdrf.tsv` beside the spectra files. Two or
    more are still refused.
  - **Only a real edit makes a design MetaMorpheus made the user's.** Line endings are ignored.
  - **The GUI half (a later PR):**
    - the design is made from the SDRF when spectra files are added;
    - for TMT, the kit is guessed from the SDRF's channel labels;
    - Run refuses only when the SDRF names a channel the search's kit does not have.

## Ledger

| item | state |
|---|---|
| this notice | nothing asked of you |
