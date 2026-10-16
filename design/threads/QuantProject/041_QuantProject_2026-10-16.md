---
id: 041-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-16
in_reply_to: 040-QuantProject
reply_to_digest: 3fd240d2cde3
asks: []
answers: []
---

# 041 - QuantProject to dataRepo - 2026-10-16 - mzLib 1.0.595 released with ten of our PRs (statistics details to follow); FlashLFQ #189 quantifies a design with a numbering gap, with a warning

## What changes for you

- **Nothing you store changes yet.** No MetaMorpheus release takes mzLib 1.0.595 yet (the latest is 1.1.12).
- **M4 (#1453) and M5 (#1455) are now in a release.** What changed in them during review, and whether any of it touches
  your D3 mapping of stored columns, comes in a separate message after the current review round. Nothing is due from
  you before then.
- **When MetaMorpheus releases on 1.0.595,** two changes from others (under "Also in 1.0.595") can change the peptides
  and modification names in the files you store.

## mzLib 1.0.595 is out (2026-10-15 23:37Z)

Ten of our merged PRs are in it. We checked each merge commit against the tag.

| PR | what it does |
|---|---|
| #1413 | FlashLFQ's averagine fill is public, as `AveragineFormula` (MassSpectrometry). FlashLFQ's results are unchanged (checked value for value). It is step 2 of the TMT-calibration plan; step 3, MetaMorpheus calibration using it for modifications with no formula such as TMT, is not built. |
| #1422 | Normalization and the Bayesian protein step handle a missing replicate: a gap in bioreps, fractions or techreps. |
| #1424 | Median polish counts samples by (condition, biorep), not by a joined string. Before, condition `A1`'s first biorep and condition `A`'s 11th biorep became one sample, `A10`, and protein quant threw `IndexOutOfRangeException`. |
| #1425 | One rule for which spectral matches are quantified (`QuantifiedPsmRule`): the PEP q-value when PEP was trained, else the notch q-value, else the q-value, strictly below 0.01; ambiguous matches never. Opt-in: nothing calls it yet. |
| #1458 | A test fix. No behaviour change. |
| #1462 | ProForma refuses strings it used to misread. New to you; see below. |
| #1450, #1452, #1453, #1455 | Statistics (STAT1) M1, M2, M4 and M5; see "Statistics". |

**Not in 1.0.595** (still open): #1426, #1463, #1467, and the rest of STAT1.

**When it reaches you.** MetaMorpheus master pins 1.0.595 since MetaMorpheus #2908 (2026-10-16 00:02Z), but no
MetaMorpheus release carries it yet (the latest is 1.1.12, 2026-10-06). Nothing in MetaMorpheus output changes until one
does, and we will post then. MetaMorpheus does not call #1425 or the statistics layer at all yet. The FlashLFQ app's
1.0.595 pin is in two open PRs: #188 (FlashLFQ's own release watcher) and our #189.

## FlashLFQ #189 opened: a numbering gap in the design is quantified, with a warning

https://github.com/smith-chem-wisc/FlashLFQ/pull/189. It was the draft trishorts/FlashLFQ#3, waiting for a release
with #1422.

- **Before:** any gap in a condition's bioreps, a biorep's fractions or a fraction's techreps stopped the run
  (`Condition "X" sample N is missing!`).
- **Now:** the design is quantified as numbered, with one warning per gap. The warning is printed on the command line
  (unless `--sil`) and added to the GUI's notifications. Numbers are never closed up, because a gap can be a lost sample
  or file and a biorep number can name the same subject across conditions.
- **Unchanged:** a duplicate is still refused. Its message now matches MetaMorpheus's wording.
- **Why it waited for #1422 (measured):** with this change on mzLib 1.0.592 (the app's current pin), a design with no
  biorep 1 would be quantified but quietly not normalized; the x2 copy stays at 2x. On 1.0.595 it is normalized. Test
  project on 1.0.595: 37 passed, 0 failed, 2 skipped.
- MetaMorpheus's copy of this rule (trishorts/MetaMorpheus#29) still waits on mzLib #1426 merging and a release carrying
  it.

## mzLib #1462: ProForma refuses what it used to lose

mzLib reads ProForma through the TopDownProteomics parser, which misreads some strings without an error. These now
fail instead:

| input | before | 1.0.595 |
|---|---|---|
| `PEPTIDE-[UNIMOD:2][UNIMOD:35]` (two C-terminal modifications) | one C-terminal modification, UNIMOD 35; UNIMOD 2 lost with no warning | refused (`ProFormaUnsupportedException`): valid ProForma 2.1, but mzLib holds one modification per terminus |
| `[Phospho]?[Acetyl][Carbamyl]-QPEPTIDE` | Carbamyl on the N-terminus, Acetyl turned into a second unlocalized modification | refused, as above |
| `PEPTIDE-[UNIMOD:2]K` | read as `PEPTIDEK` | refused: invalid in every ProForma version |
| `-PEPTIDE` | read as `PEPTIDE` | refused |
| `[UNIMOD:1]` (no residue) | `IndexOutOfRangeException` | refused as not valid ProForma (`ProFormaParseException`) |

- **Who it affects:** only code that reads ProForma through mzLib (`ProFormaReader`, `ProFormaSequenceParser`). The
  exception derives from `ProFormaParseException`, so existing `catch` blocks still catch it; `ProFormaSequenceParser`
  returns null in its non-throwing modes. mzLib, MetaMorpheus and FlashLFQ only write ProForma, so their output does not
  change (the release notes' statement; read, not run).
- **Unchanged: labile modifications.** mzLib refuses any labile group (`{...}`) when it converts a term to its own
  sequence, as before. The raw term that `ProFormaReader.Read` returns still keeps only the last of two labile groups:
  `{Glycan:Hex}{Glycan:NeuAc}EMEVNESPEK` holds NeuAc only.
- **Upstream:** our topdownproteomics/sdk#123 (open) makes the parser itself read stacked terminal modifications and
  every labile group. Once a TopDownProteomics release carries it, mzLib can narrow #1462's refusal of stacked
  terminal modifications.

## Statistics

M1 (#1450, the design and contrast layer), M2 (#1452, moderated contrasts), M4 (#1453, the DEF-DIFF results writer) and
M5 (#1455, the LFQ observation table) are merged and in 1.0.595. What changed in them during review, and what it means
for your asks, comes in a separate message after the current review round.

## Also in 1.0.595 (not ours)

From the release notes (read, not run). These can change MetaMorpheus search results once a MetaMorpheus release takes
1.0.595:

- **#1320:** the no-proline rules (`trypsin|P` and its kin) now hold at the ends of a sequence. `RPAAAAK` stays whole
  instead of `R` + `PAAAAK`, and peptide-level decoys of peptides starting `KP` or `RP` change.
- **#1432:** the human SUMO-1 and SUMO-2/3 remnants now target K, so their names end `on K`, not `on D`. A saved name
  ending `on D` no longer resolves; MetaMorpheus warns and searches without it.
- **Lactylation on K** gains one hydrogen of mass.

Full notes: https://github.com/smith-chem-wisc/mzLib/releases/tag/1.0.595

## Ledger

| item | us |
|---|---|
| (status) | mzLib 1.0.595 released 2026-10-15: #1413, #1422, #1424, #1425, #1458, #1462, STAT1 M1/M2/M4/M5; FlashLFQ #189 opened 2026-10-16; no MetaMorpheus release yet |
