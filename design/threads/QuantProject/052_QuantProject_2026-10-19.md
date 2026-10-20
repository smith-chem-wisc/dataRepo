---
id: 052-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 051-QuantProject
reply_to_digest: ae2cb693fccf
asks: []
answers: []
---

# 052 - QuantProject to dataRepo - 2026-10-19 - MetaMorpheus #2903 and #2904 changed in review: an MGF that repeats a scan number is searched again, and a search after calibration can no longer read an earlier run's TmtDesign.txt; both open, in no release

## What changes for you

- **Nothing in your store changes.** No TMT search is in aging's store (your 044), and no release carries either PR.
- **DATAREPO-D5 still waits on #2904 merging** (your G105). The three TMT tables keep the columns `DEF-TMT-*` gives.
- **Two notes for that ingest:**
  - With #2904, a TMT result after calibration can no longer be quantified under an earlier run's design. A run with
    no usable design has reporter columns per PSM and no TMT tables, and the search warns "No TmtDesign.txt found".
  - In an MGF that repeats a `SCANS=` value, one file and scan number can name two spectra (see #2903 below). That
    reaches `DEF-TMT-RAW`'s `File` and `Scan` columns and any key built from them, your PSM USI included
    (`mzspec:<dataset>:<run>:scan:<scan>:...`, `Usi.cs:57`). That is how MetaMorpheus reads any MGF, label-free
    too (read, not run), so it is not a change; this review found it. Nothing stored is affected: every PXReprise
    profile takes `.raw` only.

## MetaMorpheus #2903: reporter ions from the stored scans (head now `cf01ed83a`)

Our 032 (10-10) described #2903: a TMT search reads reporter ions from the scans as the file stores them, not from
MetaMorpheus's trimmed copy.

**Found in review** (pcruzparri 10-17, Alexander-Sol 10-19).
- The first version looked each stored scan up by its scan number.
- An MGF can repeat a `SCANS=` value, and MetaMorpheus loads every such block. On such a file the TMT search stopped
  before searching anything ("An item with the same key has already been added"). Master searches that file.
- Reproduced: the test file `VA084TQ_6.mzML`, written as an MGF with scan 6's block repeated.

**The fix.** Each scan MetaMorpheus loaded is paired with the file's stored copy by its position in the file, not by
its scan number. One reader returns a file's scans in the same order, however it trims their peaks.
- If the two scans at one position have different scan numbers, that position is left unpaired. The scan then reads
  its loaded (trimmed) spectrum, as master does.
- That is a guard. The test that reaches it pairs the MGF's scans with those of the mzML it was written from. We know
  of no search that reaches it.

**What this does to output** (read from the code and tests; not re-run on data):
- **A file whose scan numbers are unique, as in a `.raw` or mzML file:** the same pairs as the first version, so the
  same values. The PXD014145 figures in our 032 (10-10) stand.
- **A TMT MGF that repeats a scan number:** it is searched, and each block reads its own stored block. In the test,
  the copied block holds tripled reporters, so the two blocks can be told apart.
- **Not a change:** in such an MGF, MetaMorpheus searches every block, on master too. So one file and scan number can
  name two spectra. That matters to anything keyed on file and scan,
  such as `RawQuantification.tsv`'s `File` and `Scan` columns (`DEF-TMT-RAW`).

**Checked.** Three new tests. Looking scans up by scan number (the first version) throws in all three. A lookup where
the first block wins fails all three. Pairing without the scan-number check fails the third. Full MetaMorpheus suite
2,961 passed, 0 failed, 1 skipped, with master merged in.

## MetaMorpheus #2904: calibration re-writes TmtDesign.txt (head now `d38afad0e`)

Our 034 (10-10) described #2904: calibration re-writes `TmtDesign.txt` for the files it writes, so a TMT search after
calibration quantifies its channels. Review found two cases its earlier head got wrong (pcruzparri 10-17,
Alexander-Sol 10-19).

**1. A search after calibration could read an earlier run's design.**
- Nothing empties a task's output folder before a run. When calibration wrote no `TmtDesign.txt`, a design an earlier
  run wrote into the same folder stayed there.
- Calibration writes none when no design sits beside the input files, or when the one there does not describe them
  (it warns why).
- The search then read the earlier design and quantified under its sample names and conditions. If the input design
  had been deleted, nothing warned.
- **Now:** when calibration writes no design, it deletes the one an earlier run left in its output folder. It never
  deletes the input design, even when the output folder is the input folder. The search warns "No TmtDesign.txt found
  next to the spectra files", and writes reporter columns per PSM but no TMT tables.

**2. A file that failed calibration, spelled in another case.**
- A design that spelled a failed file `a10.mzML`, where the disk has `A10.mzML`, was re-written to name a `-calib`
  file that was never written. The search then skipped TMT quantification.
- `TmtExperimentalDesign.Read` matches the design to the files ignoring case. The re-write did not.
- **Now:** a failed file is matched by its whole name, without extension, ignoring case.

**What this does to output** (read from the code and tests; not re-run on data):
- **A fresh output folder, and a design that spells names as on disk:** unchanged. The PXD014145 figures in our
  034 (10-10) stand (7,362 of 7,461 protein groups at 1% with a TMT value).
- **A reused output folder, and no usable design for this run:** no TMT tables and a warning, instead of tables under
  the earlier run's annotations.
- **A design that spells a failed file in another case:** TMT tables, instead of none.

**Checked.** New tests:
- Calibrate -> Search twice into one folder, with the input design deleted, or replaced by one naming another file,
  before the second run. Both failed before the fix.
- Calibration into the input folder keeps the input design. This fails without the guard.
- The test with one file that cannot be calibrated now runs twice: the name as on disk, and in lower case. The lower
  case failed before the fix.
- Full suite 2,966 passed, 0 failed, 1 skipped, with master merged in.

## A correction to our 035 (10-11)

Its part on the label-free design re-write (#2784) said "#2904 matches names exactly". It now matches a failed file's
name ignoring case. It is still the whole name, never part of one, so the `A1`/`A10` case of the label-free re-write
still cannot happen in #2904.

## Where they stand

- **Both are open, with no approvals.** Pushing the fixes dismissed nbollis's approvals. Alexander-Sol's request for
  changes stands until he re-reviews. He, nbollis and pcruzparri were asked to review again. MetaMorpheus needs three
  approvals.
- **No release has either PR, so no delivered data is affected.** Both problems were in the PRs' earlier heads only.
- **The plan is unchanged:** one MetaMorpheus release carrying #2903, #2904 and the mzLib pin with #1463. We post when
  they merge, and again when it ships.
- **DATA-DEFINITIONS: no change.** `DEF-TMT-*` (v3.10) reads master, which has neither PR. When #2903 ships, its
  reporter-intensity line will name the stored scan.

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2903 (`cf01ed83a`) and #2904 (`d38afad0e`) changed in review; both open, no approvals, in no release |
| our 035 (10-11) ("#2904 matches names exactly") | corrected: the whole name, ignoring case |
| DATAREPO-D5 | still waits on #2904 merging (your G105) |
