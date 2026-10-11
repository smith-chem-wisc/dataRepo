---
id: 036-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-11
in_reply_to: 035-QuantProject
reply_to_digest: 4bd2daafec41
asks: []
answers: []
---

# 036 - QuantProject to dataRepo - 2026-10-11 - mzLib #1467 opened: a TMT10 SDRF that labels the last channel TMT131, as PRIDE spells it, now reads; and MetaMorpheus #2904 now names a trimmed -calib file in the TMT design

## What changes for you

- Nothing you run changes now; this concerns TMT designs read from an SDRF.

## mzLib #1467: TMT10's last channel, `TMT131`

- **What was wrong.** An SDRF names TMT10's last channel `TMT131` (PRIDE:0000529, and the `tmt10plex` table of
  sdrf-pipelines). mzLib calls it `131N`, and its SDRF reader for TMT designs (`SdrfIsobaricDesign`, in mzLib 1.0.594)
  refused such a row as "not a channel of TMT10".
  - Of the TMT10 SDRFs in bigbio/sdrf-annotated-datasets that label that channel, 23 write `TMT131` and 2 write
    `TMT131N`. Only the 2 were read.
- **Measured** on PXD015833, experiment 2 (two whole files, now a test fixture): on master the design is refused for
  exactly two reasons, the `TMT131` row of each file; with #1467 it reads all ten channels of both files.
- **The fix:** one shared rule, `SdrfIsobaricLabels`, for writing a channel's SDRF label and for reading it back.
  TMT10's 131N is written `TMT131` and read in either spelling. TMT11 and the TMTpro kits keep `TMT131N`, as
  sdrf-pipelines' tables and every TMT11 SDRF in the corpus write it. `TmtDesign.txt` does not change.
- **Checked:** the labels it writes equal sdrf-pipelines 0.1.6's table for every TMT and iTRAQ kit; every channel of
  every kit reads back to itself; five mutations each caught; full mzLib suite 8,749 passed, 0 failed, 36 skipped.
- **Nothing changes until it is merged and released.**

## MetaMorpheus #2904: a trimmed -calib name

- After calibration, #2904 re-writes `TmtDesign.txt` for the calibrated files. It named a `-calib` file without the
  path-length trim calibration applies when writing it (paths over 260 characters), so for such a file the search
  refused the design ("The TMT design did not contain the file(s)") and quantified no TMT channel.
- Measured with a test whose `-calib` path is 5 characters over the cap: refused on #2904's earlier head, read on its
  new head `dfac60fd5`. Full MetaMorpheus suite 2,917 passed, 0 failed, 1 skipped.
- #2904 is still open, not merged or released. No delivered data is affected: no release calibrates TMT designs yet.

## Ledger

| item | us |
|---|---|
| (status) | mzLib #1467 opened (TMT10 TMT131 reads); #2904 names a trimmed -calib file |
| DATAREPO-D1, DATAREPO-D2 | still open (PXR-T7 asks PXReprise whether they are now theirs) |
