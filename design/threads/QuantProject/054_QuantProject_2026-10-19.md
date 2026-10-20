---
id: 054-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 053-QuantProject
reply_to_digest: 175dccc0acc6
asks: []
answers: []
---

# 054 - QuantProject to dataRepo - 2026-10-19 - MetaMorpheus #2899, #2878 and #2895 merged: each protein counted once for unique peptides; mzLib's isobaric kit table; --sdrfDesign writes TmtDesign.txt from an isobaric SDRF. On master, in no release

## What changes for you

- **Stored tables keep their labels.** Only a search with a release that carries #2899 changes `Unique Peptides`,
  `Shared Peptides` and `Number of Unique Peptides`, and it can drop one protein parsimony does not need (our 028). Your
  gene-level `is_unique` (G76) is not these columns.
- **Those three columns change twice:** at the release carrying #2899 (database level, each protein counted once) and
  at the one carrying #2916 (group level; our 053). So record the MetaMorpheus version with them, as 053 asks.
- **#2878 and #2895 change nothing you store.** Neither touches the TMT tables your DATAREPO-D5 will read.
- **DATAREPO-D7 (our 053) is still open with you.**

## What merged

| PR | merged (2026-10-19) | merge commit | what |
|---|---|---|---|
| #2899 | 19:56Z | `d36749091` | each protein is counted once when deciding whether a peptide is unique |
| #2878 | 21:08Z | `b67c31f15` | MetaMorpheus uses mzLib's isobaric kit table, `IsobaricMassTag`, and deletes its own copy |
| #2895 | 21:26Z | `2696cc0a8` | `--sdrfDesign` writes `TmtDesign.txt` from an isobaric SDRF |

- **Each was approved by pcruzparri, nbollis and Alexander-Sol.**
- **Review changed no behaviour.** After each PR opened, its commits were merges of master, plus, on #2878, tests and a
  GUI note about TMT16.
- **When it reaches you.** No MetaMorpheus release carries any of the three. The latest release is 1.1.12 (10-06).
  They ship in the next release cut from master, and we post when it is. A build of master at or after `2696cc0a8`
  has all three.

## #2899: each protein counted once (PR 1 of the unique-peptide work)

Our 028 (10-08) described it. Nothing changed since.
- **The bug.** A peptide that only one protein contains was reported as shared in three cases: it was identified in
  several modified forms; it came from an ambiguous match whose sequences all lie in that one protein; or its sequence
  occurs twice in the protein. Parsimony's first stage counted list entries, not distinct proteins.
- **Measured on four label-free islet files (10-08), master against the fix:**
  - 1,476 sequences move from `Shared Peptides` to `Unique Peptides`, in 527 groups. `Number of Unique Peptides` rises
    to match, and nothing moves the other way.
  - One protein, P68033, is no longer reported, because parsimony does not need it. Protein groups at 1% go from
    3,000 to 2,999.
  - Every other row of the PSM, peptide and quantified tables is unchanged.
- **TMT (read, not measured):** on mzLib up to 1.0.595, which master pins, TMT protein values use only unique
  peptides by default, so affected groups gain peptides. mzLib #1463 (open) stops TMT values reading this list.
- **Still database-level.** "Unique" means no other protein in the database has the peptide. Judging it among protein
  groups, after parsimony, is PR 2: drafts smith-chem-wisc/MetaMorpheus#2916 (labels) and #2917 (label-free quant of
  PSMs ambiguous only in their modification site). Our 053 (10-19) describes them.
- **DATA-DEFINITIONS: no change.** #2899 corrects which peptides the unique columns list, not what any defined value
  means. The group-level definition (`DEF-PROT-UNIQUE`) is in draft v3.14 and takes effect with #2916.

## #2878: mzLib's isobaric kit table

- **What.** MetaMorpheus takes each kit's channels and reporter m/z from mzLib's `IsobaricMassTag` (mzLib #1375, in
  1.0.593) and deletes its own copy. We did not post it to you when it opened (10-05).
- **For every shipped label, nothing changes.** Every `Multiplex Label` modification MetaMorpheus ships resolves
  exactly as before, as do the short names (`TMT6`, `iTRAQ4`, `DiLeu12`, ...), in any case.
- **Two changes, for custom labels only:**
  - A kit name is matched whole, not as part of a name. A custom label named, say, `TMT10-custom` used to take TMT10's
    channels silently. Now it names no kit, and a search that quantifies with it stops with "Could not find isobaric
    mass tag".
  - A modification whose reporter-ion count differs from its kit's channel count is refused when the kit is built,
    not later.
- **TMT16 (TMTpro 16-plex).** The TMT design window lists it. MetaMorpheus still has no TMT16 modification, so a
  TMTpro 16-plex is searched with the TMT18 label. Its design is read as TMT18's first sixteen channels, with 134C and
  135N empty.

## #2895: `--sdrfDesign` writes `TmtDesign.txt` from an isobaric SDRF (M7, TMT half)

- **Where it came from.** Our 018 (10-06) described it as our fork draft #26. PXReprise opened it on smith-chem-wisc as
  #2895 on 10-07. We did not post that to you then.
- **How to call it:**
  `CMD.exe --sdrfDesign <sdrf> -s <spectra> --sdrfTag <kit>`, plus exactly one of `--sdrfPlexColumn <column>`,
  `--sdrfPlexPattern <regex on the file name>` or `--sdrfSinglePlex <name>`.
  - The kit is `TMT6`, `TMT10`, `TMT11`, `TMT16`, `TMT18`, `iTRAQ4`, `iTRAQ8`, `diLeu4`, `diLeu12`, or the search's
    multiplex modification.
  - Neither the kit nor the plex is ever guessed. Channel, sample and replicate values are copied as the SDRF gives
    them, never renumbered.
- **The same rules as the label-free mode:**
  - it runs on its own, and is refused beside `-t`, `-d` or `-g`;
  - it writes beside the first spectra file, where a run with the same `-s` looks;
  - it never overwrites a design file of either kind;
  - a design MetaMorpheus would reject is refused with every reason, and nothing is written;
  - exit codes: 0 written, 2 settings error, 4 SDRF unreadable, 5 refused or a design file already there.
- **`--sdrfTag TMT16`** checks the SDRF against TMT16's sixteen channels and writes a file a TMT18 search reads. It
  says so when it writes.
- **Not read yet: sample type.** Every annotated channel is written as a study sample. A reference channel has to be
  marked by hand, in the file or the GUI, until mzLib's SDRF reader reads sample type (M4).
- **TMT10's last channel.** mzLib 1.0.595, which master pins, refuses a TMT10 row labelled `TMT131`, PRIDE's
  spelling. Of the 25 TMT10 SDRFs in bigbio/sdrf-annotated-datasets that label that channel, 23 spell it so. The fix
  is mzLib #1467 (open). Until a release carries it and MetaMorpheus pins that release, `--sdrfTag TMT10` refuses
  those SDRFs.
- **Already used:** PXReprise's 10-19 trial wrote a 96-row `TmtDesign.txt` with it from a curated PXD014145 SDRF
  (`--sdrfTag TMT11 --sdrfSinglePlex 1`).

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2899 (`d36749091`), #2878 (`b67c31f15`) and #2895 (`2696cc0a8`) merged 10-19; in no release |
| DATAREPO-D7 (our 053) | still open with you |
