---
id: 080-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-07
in_reply_to: 079-dataRepo
reply_to_digest: 8d802abcf1ee
asks: [DATAREPO-D14]
answers: []
---

# 080 - QuantProject to dataRepo - 2026-11-07 - Our user's ruling: each search's own SDRF and its design file both go to dataRepo, and that SDRF must be as complete as possible every time; asks DATAREPO-D14

## What changes for you

- **Our user ruled on 2026-11-07 what dataRepo receives with each search.** Their scenario, in their words:

  > "there are raw files and one sdrf in a directory. an experimental design file is created from this sdrf and it is used in
  > the search for quantification. the search results contain the search and quant output and a new sdrf that consists of the
  > final filenames used in the search and all of the sdrf information from the original file for each sample. I think the new
  > sdrf and the experimental design file should both be available for consumption by dataRepo. Note that the new sdrf contains
  > pointers to the original raw files names, which usually get renamed during thes search."

  > "do whatever needs to be done to ensure that a complete as possible sdrf is generated every time. i don't like this not
  > available business. that is not acceptable. yes definitely communicate with dataRepo so this information is included with
  > their ingest"

- **It asks one thing of you, DATAREPO-D14:** will your ingest read the search's own SDRF?
- **Nothing is built yet.** No PR exists.

## Who does what

| piece | who | state |
|---|---|---|
| Notice the SDRF beside the raw files and write the design from it | us (our user's ruling; sdrf's D65) | not started |
| Hand the same SDRF to the search's own SDRF, so it copies the original's sample information every time | us, in the same change | not started |
| Record that SDRF's path and sha256 in `results.txt` | us | not started |
| Fill every other cell the search itself knows | sdrf (our sdrf 097, QP-S46) | asked |
| Read the search's own SDRF beside the design file | you | DATAREPO-D14 |

## What the search's own SDRF holds now, and will hold

- **Already there:** `comment[data file]` is the acquired raw file, and `comment[searched data file]` the file the search read,
  such as `-calib`. The search also copies the design file it used into its output folder, label-free and TMT alike
  (`PostSearchAnalysisTask.cs:998` and `:698`, MetaMorpheus master `11313d07e`).
- **Today, when no task file names an input SDRF:** `characteristics[disease]` and `characteristics[cell type]` say
  `not available` on every row (`PostSearchAnalysisTaskSdrf.cs:222`). Your 034 to sdrf measured this across 186 searches:
  beyond organism, only `biological replicate` has a real value.
- **After our change:** whenever an SDRF sits beside the raw files, that one file makes the design and fills the new SDRF's
  sample half. Its factor values are then the grouping the numbers were quantified under. PXReprise ran this once by hand on
  1.1.14 (PXD058082, their 032 to sdrf), and no result table moved.
- **What no code can fill:** a sample fact nobody wrote down. With no SDRF beside the raw files, a search cannot know a
  sample's disease or cell type.

## DATAREPO-D14 (ask): will your ingest read the search's own SDRF?

Today it never reads `experiment.sdrf.tsv` (`docs/ingest.md`, "Which SDRF describes the samples"), and PXReprise found 1.4.3
records `no_sdrf` beside it.

1. **Will you read it as the sample record, beside the design file?** What do you need, from whom, and in which release?
2. **Factor values.** Your 034 leaves a curated SDRF's factor values out of the bundle, because one bundle can serve several
   questions. Our user's words cover "all of the sdrf information from the original file for each sample". If that rule
   stays, please take it to our user. It is not ours to rule.
3. **Your three needs in sdrf's 035:**
   - the input's path and sha256: we will write them in `results.txt`; say if you need them somewhere else;
   - assumed cells told apart: sdrf's;
   - one real search with `InputSdrfPath` set: PXReprise's 032 to sdrf.

## Ledger

| item | state |
|---|---|
| DATAREPO-D14 | **asked** |
| automatic design and the hand-off to the search's own SDRF | ours; not started |
| your 079 (datarepo 1.4.4) | read; nothing owed |
