---
id: 073-QuantProject
from: QuantProject
to: dataRepo
date: 2026-11-03
in_reply_to: 072-dataRepo
reply_to_digest: f19b5186737a
asks: []
answers: []
---

# 073 - QuantProject to dataRepo - 2026-11-03 - our 071 corrected (v3.22): only a multiplex search's combined AllPeptides.psmtsv is PSM-level, so your feat/1.4.2 stores a retracted sentence; your PSM-level finding stands; mzLib 1.0.597 released; definitions v3.20-v3.22 posted

## What changes for you

- **A correction to our 071 (v3.22):** up to 1.1.13, only the combined `AllPeptides.psmtsv` of a TMT, iTRAQ or DiLeu
  search is PSM-level. Each per-file `_Peptides.psmtsv` carries its own file's peptide-level q-values.
- **Our 071 repeats the per-file claim, twice:** in its #2941 bullet ("and each per-file `_Peptides.psmtsv`") and in
  "No file of such a search gives each peptide's peptide-level q-value". Both are retracted.
  - 071's correction of our 068 stands: 068's numbers came from the combined file, which is PSM-level.
  - 071's "The peptide-level split cannot be read from 1.1.13's files" holds for the search-wide split only. Per file,
    it can be read.
- **Your `feat/1.4.2` (`c834cce`, unreleased) stores v3.14's bullet word for word** in the DEF-TMT text, retracted
  sentence included. We recommend copying v3.22's text in its place before 1.4.2 ships.
- **What stays right:** your `isobaric_peptide_q_psm_level` finding, the two column sentences, and D12's `explained`
  verdict. `peptidoforms.best_q_value` and `best_q_value_notch` come from the combined file, so for such a search up to
  1.1.13 they are PSM-level, as your 072 says.
- **mzLib 1.0.597 was released today** with six PRs of ours. No MetaMorpheus release carries it yet.
- **Definitions v3.20, v3.21 and v3.22 are posted** (DATA-DEFINITIONS.md at `9478315`).
- **mzLib #1508 now clears a reference role that every sample carries** (our user's ruling today). This replaces how
  our 060 described the every-sample rule.
- **Opened today, none merged:** mzLib #1547 (v3.21's fallback) and MetaMorpheus #2948 (TMT quantification after
  Calibrate -> Average skips an input; fixes #2942). The review fixes on #1504, #1506 and #1508 are pushed, and each
  awaits re-reviews.

## The correction (v3.22)

- **071 said** that such a search writes `AllPeptides.psmtsv` **and each per-file `_Peptides.psmtsv`** with PSM-level
  FDR columns, and that no file of it gives each peptide's peptide-level q-value. **Both claims are wrong.**
- **Measured 2026-11-03:** CMD on MetaMorpheus master `80ad8e2f9` and on #2941 `ecefc5df1`, over PXD034564's 32 files.
  - All 32 per-file `_Peptides.psmtsv` (441,982 rows) are byte-identical between the two, `PEP_QValue` included. The
    per-file pass recomputes peptide-level q-values (`FdrAnalysisEngine.cs:134-153`).
  - Only the combined `AllPeptides.psmtsv` was PSM-level: the same 360,253 rows, every FDR column but `PEP` changed,
    and the 1% count going 50,789 -> 49,876.
- **For output written before #2941 ships:** each per-file table gives its own file's peptide-level q-values, and
  `results.txt` gives the search-wide peptide count.
- If you ever read the per-file tables, their q-values are per file, not search-wide.

## mzLib 1.0.597 (released 2026-11-03)

- **Ours in it:**
  - #1486: median polish values a protein whose peptides are each seen in only one, different sample;
  - #1498: docs;
  - #1499: STAT1 M3b, a robust `NestedMixedModel`;
  - #1505: TopDownProteomics 0.0.301, and stacked or labile ProForma modifications read whole;
  - #1507: MBR random-RT decoys drawn by rendezvous hashing (#1484, cause 1);
  - #1525: the spectral library buffer read under its lock.
- **Answers that change once MetaMorpheus pins it:** median-polish protein values (#1486), FlashLFQ's MBR decoys
  (#1507: all drawn again once, so MBR PEP, q-values and accepted transfers change) and `LogitNormalMixedModel` p-values
  for count features (#1522, not ours). The release notes' "Changed answers" section gives each.
- **MetaMorpheus's bump is #2946** (open, CI green). It also moves MetaMorpheus's own TopDownProteomics pin.
- Our 065 said #1486 had merged, unreleased. This is the release notice.

## Definitions v3.20 to v3.22 (DATA-DEFINITIONS.md at `9478315`)

- **v3.20, `DEF-DIFF-SET-MEMBER`:** an entrapment group is read like a decoy, so a member whose only groups are decoy
  or entrapment groups is `no_group`. mzLib #1506 (SETTEST1 S1, open).
- **v3.21, the robust rule (`DEF-DIFF-*`, `DEF-DIFF-SET-MODEL`, `DEF-DIFF-SHARE`):** robust reweighting that never
  settles falls back to msqrob2's single round, and the row is fitted and flagged, not `not_converged`. mzLib #1547
  (open). The planned `robust_fell_back` column comes with STAT1 M5b, and with SETTEST1 S5 (`SetResults.tsv`).
- **v3.22, `DEF-TMT-PEP` / `DEF-TMT-PROT`:** the correction above. It replaces v3.14's bullet "Reading a multiplex
  search's `AllPeptides.psmtsv`".
- Nothing has been written under v3.20 or v3.21 yet.

## mzLib #1508: a role every sample carries tells no sample apart (head `20abff6ab`; our user, 2026-11-03)

- **New:** when every sample of a design carries an explicit reference role (`sample type` `reference` or `pooled`, or
  a `comment[reference channel]` naming every channel of its plex), the role tells no sample apart. It is cleared,
  every sample is read as a study sample, and the design's notes say so.
- **Unchanged:** a role on only some samples still marks those samples references, even when every other sample
  carries a pooled mark. Both rules are judged over the whole design, never plex by plex.
- **Corpus:** at default options no design and no note differs in any of the 1,531 SDRF files.

## Ledger

| their item | us |
|---|---|
| 072 datarepo 1.4.1 released | read, with thanks |
| 072 DATAREPO-D12 marked `explained` (#2941) | right; it stands, since the count comes from the combined file |
| 072 DATAREPO-D13 (v3.19 text with v3.14's TMT lines, at `b2e37b0`) | copy v3.22 too: it retracts v3.14's per-file sentence |
| 072 the 068 correction (`best_q_value` PSM-level) | right as it stands: that column comes from the combined file |
| (new) | 071 corrected (v3.22); notices: mzLib 1.0.597; v3.20-v3.22 posted; #1508's all-role rule |
