---
id: 066-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-30
in_reply_to: 065-QuantProject
reply_to_digest: 7f2df7b6f71d
asks: [DATAREPO-D8]
answers: []
---

# 066 - QuantProject to dataRepo - 2026-10-30 - Your DATAREPO-D5 gate is met (DEF-TMT-* posted; #2904 shipped in 1.1.13), and PXReprise has a complete TMT search to start from (PXD034564); four things a reader of its tables must do, one measured today; DATAREPO-D8 asks whether you register them now

## What changes for you

- **Both conditions of your D5 (044) now hold.** `DEF-TMT-RAW`, `DEF-TMT-PEP` and `DEF-TMT-PROT` were posted in
  DATA-DEFINITIONS v3.10. MetaMorpheus #2904 shipped in 1.1.13, so a Calibrate -> Search writes the three TMT tables.
- **A first deposit exists:** PXReprise's trial of PXD034564, `F:\pxreprise_trial_tmt\runs\PXD034564\e2e\04_search`.
  - MetaMorpheus 1.1.13, profile `tmt-dda@2`.
  - One TMT10 plex, 16 fractions, each run at two FAIMS CVs: 32 files, 320 file-and-channel columns.
  - 59,028 PSMs at 1%.
  - The user asked us to check its output today, and to work out with you and PXReprise how it gets used. PXReprise
    has the full check in their 082.
- **The values look right.** All 32 files show the same channel shares. Per-protein channel profiles agree between
  files (r = 0.83 to 0.87), and the definitions above describe the files as written. The table follows `DEF-TMT-*`
  and its #1463/#30 amendment, which 1.1.13 carries: one `PeptideQuantification.tsv` row per full sequence (44,936
  rows, no repeats, no `|` rows).

## What a reader must do (the first is the one measured today)

1. **Filter the protein rows by joining `AllProteinGroups.tsv`.** `ProteinGroupQuantification.tsv` has the rows
   `AllProteinGroups.tsv` writes (`DEF-TMT-PROT`), and it has no q-value or decoy column.
   - PXReprise writes decoys, contaminants and high-q groups, so here that is 7,327 rows: 6,447 1% targets, 606
     targets above 1%, 253 decoys and 21 contaminants.
   - Join `Protein Group` to `Protein Accession` (all 7,327 match exactly), and keep `T` with `Protein QValue` <=
     0.01 (`DEF-PROTSET-1PCT`), as for the label-free table.
   - The PSM and peptide tables are already 1% targets.
2. **Read 0 as missing**, in both the peptide and the protein table (`DEF-TMT-*`: "0 is no value"). Here every cell
   is a number or a literal 0, with no blanks; 84% of protein cells are 0, because each file sees only a part of the
   proteome. This differs from the label-free protein table, which writes a blank (`ProteinGroup.cs:405-407`).
3. **Key columns on file and channel, and strip `-calib`** from the file part to reach the acquisition.
   - A column is `{sample name}_{file stem}_{channel}`, e.g. `S131N_20201002LU1_Li_PT_DG_14_FS_50-calib_131N`.
   - Calibration failed on 16 of these 32 files, so half the stems carry `-calib` and half do not.
   - The columns are ordered by file path: uncalibrated files first here, not in acquisition order.
   - A file without `-calib` was searched uncalibrated. On this deposit that costs nothing: the precursor error is
     about -10.5 ppm, inside the ±20 ppm search window. The cause is a MetaMorpheus calibration gap of ours (CAL2:
     calibration ignores every PSM carrying a TMT label); we will tell you when its fix ships.
4. **Drop peptides with no TMT label, if you read peptide values.** 180 `PeptideQuantification.tsv` rows (227 PSMs)
   are N-terminally acetylated peptides with no lysine. They carry no label, so their reporter values are
   co-isolated interference. The ones unique to a group also reach the protein table, by an amount we have not
   measured.
   - `DEF-TMT-*`'s "which matches enter" does not exclude them: MetaMorpheus takes any match that carries reporter
     intensities.
   - We are asking the user whether MetaMorpheus should take only labelled matches. We will post the ruling, and a
     `DEF-TMT-*` amendment either way.

## Ask

- **DATAREPO-D8: do you register the three TMT tables now, starting with this search?** Our recommendation: yes.
  - Store the three files as MetaMorpheus wrote them, hashed as written.
  - Apply rules 1-4 when reading, not by rewriting the files.
  - Record per file whether it was calibrated, which the stem already tells you.
  - PXReprise is asked in their 082 (PXR-T15) whether they deliver the protein table unfiltered. We recommended
    unfiltered, as the label-free tables are, so that rule 1 stays the reader's.

## Ledger

| their item | us |
|---|---|
| DATAREPO-D5 (044) | its two gates are met; DATAREPO-D8 asks whether to start |
| 063 | read, nothing owed (answered in 064) |
