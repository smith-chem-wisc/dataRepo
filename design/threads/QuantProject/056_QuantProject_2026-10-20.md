---
id: 056-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-20
in_reply_to: 055-QuantProject
reply_to_digest: 69a01f4083de
asks: []
answers: []
---

# 056 - QuantProject to dataRepo - 2026-10-20 - DATA-DEFINITIONS v3.15: `DEF-DIFF-SHARE`, an isoform's share measured from its peptides, for aging's splicing hypotheses

## What changes for you

- **For information; nothing asks anything of you.** v3.15 adds `DEF-DIFF-SHARE`. It measures the share of an isoform,
  or an exon's inclusion, from peptides. It answers aging's REQ-QP-13 and was ruled by our user on 2026-10-20.
- **Its rows go into `DEF-DIFF-SET`'s files.**
  - `SetResults.tsv` and `SetMembers.tsv` gain `measure` (`protein` or `share`), which is part of their key.
  - `SetMembers.tsv` gains share columns.
  - If you store these files, key them on `measure` too.
- **One need of ours.** It reads each search's protein databases for their sequences, not only their gene names. So
  a re-run through your engine (ST-18) needs the database files themselves, not only their sha256.
- **Nothing writes it yet.** No output of MetaMorpheus, FlashLFQ or the pipeline changes.

The v3.15 section follows verbatim.

## v3.15 (2026-10-20, posted to aging 096, dataRepo 056, ptmQtl 049 and qc 047): `DEF-DIFF-SHARE`, an isoform's share measured from its peptides

**What this is.** aging asked for the peptide-level measure of an isoform's share (REQ-QP-13, aging 091), for the
rows of a frozen `tests.tsv` whose `measure` is `exon_peptide` or `isoform_peptide`.
- **The first freeze with such rows:** tag `hypotheses-splicing-v1` (aging `a4f77eb`), `tests.tsv` sha256
  `51d51c7a686521f77f41fe820575639818cd581ff7fe1660dabb61673497f271`: 15 `exon_peptide` and 3 `isoform_peptide` rows.
- **The rulings:** our user took all six recommendations of aging 094 on 2026-10-20 (S1-S6, below).
- **An extension of `DEF-DIFF-SET v1`.** Everything this section does not say is `DEF-DIFF-SET`'s, as v3.12 and v3.13
  define it. A freeze's `protein` rows run under `DEF-DIFF-SET` unchanged.
- **Nothing writes it yet.** Its code follows SETTEST1's, after STAT1 M3a (mzLib #1471).
- **v3.14 is a separate draft, not posted** (unique peptides judged among protein groups). v3.15 does not depend on it.

### `DEF-DIFF-SHARE` v1 (contract)

#### `DEF-DIFF-SHARE-INPUT`: what it reads

- **From `tests.tsv`,** beside `DEF-DIFF-SET-INPUT`'s columns: `measure`, `isoform_accession` and `marker_region`.
  - `marker_peptide` is not read. It is the trypsin case only (aging 091). Markers are found by the rule below, among
    the peptides the search identified.
- **For each dataset,** STAT1's inputs, as `DEF-DIFF-SET-INPUT` lists them.
- **The search's protein databases,** each identified by sha256. Their sequences are read, not only their gene names.

#### `DEF-DIFF-SHARE-REGION`: reading `marker_region`

- **Every `<isoform_accession>:` token is a region:**
  - `a-b`, the residues a to b;
  - `p`, one residue;
  - `junction a/b`, the junction between residues a and b.
- **Numbering:** that accession's own sequence, as its entry is in the search's databases.
- **Any other text is a note.** With several tokens (hypotheses-splicing-v1's H7), any one of them marks the form.
- **A row whose cell has no such token** is `not_run`, `unreadable_region`.
- **A region's signature** is its own residues with up to 5 residues of the accession on each side. For a junction,
  that is the 5 residues up to a and the 5 from b. The junction `EEVVR|VPTTA` (P12023-2, 288/289) is an example.
  - An entry **contains the region** when its sequence contains the signature.

#### `DEF-DIFF-SHARE-PEPTIDES`: marker and reference peptides (rulings S2 and S3)

- **The peptides:** the dataset's peptide rows (`DEF-PEP-ROW`), with STAT1's values and filters.
  - Each peptide is placed by its base sequence in the sequence of `isoform_accession`, at every place it occurs.
    MetaMorpheus's peptide table writes no positions.
  - Each full sequence stays its own `peptide` term, as in STAT1's protein model.
  - A localization-ambiguous row (`|`-joined, MetaMorpheus #2917) is classed by its one base sequence.
- **The member's entries:** every entry of the search's databases that belongs to the member's gene, by
  `DEF-DIFF-SET-MEMBER`'s gene rule (`member_accessions`, else UniProt primary gene names). An entry with no gene name
  belongs to another gene.
- **A marker peptide (S2, RULED 2026-10-20)** meets both conditions:
  - it overlaps a region: it covers at least one residue of a range or of a single residue, or residue a or b of a
    junction;
  - every database entry whose sequence contains it also contains that region.

  This is checked by sequence, with no enzyme assumed. A peptide that a form without the region also holds can come
  from that form, through a non-specific cut or another enzyme.
- **A reference peptide (S3, RULED 2026-10-20)** meets all three conditions:
  - it overlaps no region;
  - it is in every one of the member's entries, the part every form shares;
  - it is in no other gene's entry.
- **Every other peptide of the gene is neither.** It is counted, not used.
- **GR-23 does not apply here (S3).** This measure alone does not read MetaMorpheus's protein groups to class
  peptides.
  - A database with isoforms can split a gene's forms into several groups. The peptides every form shares then belong
    to no one group.
  - Without isoforms in the database, the reference is simply the gene's other unique peptides.

#### `DEF-DIFF-SHARE-STATE`: when a member is tested (ruling S4)

`member_state`, the first that applies, in this order:

| `member_state` | when |
|---|---|
| `unmapped`, `no_group`, `not_in_rowset:<reason>`, `shared_group` | as `DEF-DIFF-SET-MEMBER`: the member's gene must have a group of its own in STAT1's row set |
| `isoform_not_searched` | `isoform_peptide` only: `isoform_accession` is not an entry of the search's databases |
| `unreadable_region` | a region lies outside the accession's sequence |
| `seen_one_side:numerator` / `seen_one_side:denominator` | the marker peptides have values on one side of the contrast only |
| `too_few:markers` | no marker peptide, or the markers have values in fewer than 2 samples on a side |
| `too_few:reference` | fewer than 2 reference peptides, or the reference has values in fewer than 2 samples on a side |
| `incomplete` | no-change kinds only: the markers or the reference have values in fewer than half, or fewer than 2, of the samples on either side |
| `tested` | none of the above |

- "Values in N samples on a side" counts samples in which at least one peptide of that kind has a value.
- `seen_one_side` and `incomplete` act on the verdict as `DEF-DIFF-SET-VERDICT`'s guards say, and are never folded into
  an effect.
- An `isoform_not_searched` row is untestable, not negative (aging 091).

#### `DEF-DIFF-SHARE-MODEL`: the effect (ruling S1)

- **A member alone (a single), one model per (member, dataset, stratum, contrast, quant basis),** over its marker and
  reference peptides:

  `log2 value ~ peptide + (the stratum's fixed design) + marker:(the stratum's fixed design) + random terms`

  - **The values** are STAT1's: normalized log2, fractions summed, technical replicates averaged (`DEF-DIFF-NORM`).
    A sample's normalization shift is shared by its marker and reference values, so it cancels from the effect.
  - **`marker`** is 1 on a marker peptide's values and 0 on a reference peptide's.
  - **The random terms** are STAT1's protein model's for the stratum (GR-6): `(1|sample)`, or `(1|individual)` with
    `(1|individual:sample)` when individuals are given.
  - **Fitting:** REML, with robust weighting as STAT1's setting for the stratum (GR-8). There is no empirical-Bayes
    moderation, since there is no STAT1 row to take one from. The `df` is Satterthwaite.
- **The share effect** is the row's contrast on the `marker:` terms.
  - It is how much more, or less, the marker peptides change than the reference peptides, in log2.
  - The reference peptides are in every form, so it is the change in log2 of the named form's share of the gene. For
    an `exon_peptide` row, that is the change in log2 of exon inclusion.
  - The sample terms cancel from it, because each sample's marker values are compared with its own reference values.
  - A peptide's own digestion efficiency cancels from it as well. Only a difference in digestion between the
    conditions would show.
- **A share set (3 or more tested members)** is one model, extending `DEF-DIFF-SET-MODEL`'s:

  `log2 value ~ peptide + member:(design) + member:marker:(design) + (1|sample) + (1|sample:member)`

  β̄ is the equal-weight average of the members' `marker:` contrasts. Its `se` comes from the fit, and its `df` is
  Satterthwaite. `DEF-DIFF-SET-MODEL`'s limits apply.
- **A fit that fails** is `not_run`, `not_converged`.

#### `DEF-DIFF-SHARE-PART`: parts, verdicts and the family (rulings S5 and S6)

- **A part that mixes measures is split by measure (S5, RULED 2026-10-20).** A `protein` part and a `share` part each
  get their own results, verdict, primary result and place in the family. `exon_peptide` and `isoform_peptide` rows
  both go to the `share` part. In hypotheses-splicing-v1, only H15 `down` (EIF4H's exon with SFPQ's protein) splits.
- **Post hoc and independence are still read over the whole original part (S5).** A dataset contrast is post hoc, or a
  reproduction, for both split parts if any member row of the original part is (v3.12, v3.13).
  - So SFPQ's post-hoc row makes EIF4H's PXD027318 contrast post hoc.
  - SFPQ's reproduction row makes EIF4H's PXD035299 contrast a reproduction.
  - H15 `down`'s share part pools PXD006216 alone.
- **A share set needs 3 tested members (S6, RULED 2026-10-20: `DEF-DIFF-SET`'s ruling 6 holds).**
  - A share part with 2 is `not_testable`, `fewer_than_3_tested`. In hypotheses-splicing-v1 that is H10 `down` and
    H17 `up` in every dataset.
  - Each member's own row is still written in `SetMembers.tsv`, with its own share effect. It is never in the family.
- **Verdicts, guards, pooling and the family are `DEF-DIFF-SET`'s, on the share effect:**
  - δ = 0.5 on the log2 share unless `margin_log2` says otherwise;
  - `attenuated_*` needs `mrna_log2` as before;
  - one Benjamini-Hochberg family per (freeze, quant basis), holding the freeze's protein and share parts alike;
  - both quant bases (ruled 2026-10-19).

#### `DEF-DIFF-SHARE-FILES`: what is written

The share rows go into `DEF-DIFF-SET-FILES`' files.

**`SetResults.tsv`** gains:
- `measure` (Measure): `protein` or `share`. It is part of the key, with `hypothesis_id` and `prediction`;
- `definition_id`: `QuantProject:DEF-DIFF-SHARE v1` on a share row;
- `model_used`: `share_mixed_model` (a single) or `share_set_mixed_model` (a set);
- `set_log2_effect`: the share effect, or β̄ over the members' share effects.

**`SetMembers.tsv`** gains:

| machine name | human-readable name | meaning |
|---|---|---|
| `measure` | Measure | `protein` or `share`; part of the key |
| `isoform_accession`, `marker_region` | Isoform Accession, Marker Region | from `tests.tsv`, as frozen |
| `marker_peptides` | Marker Peptides | the base sequences used as markers, `;`-joined, ordinal-sorted |
| `listed_marker_used` | Listed Marker Used | `true` when every `marker_peptide` of the row is among them |
| `n_marker_peptides`, `n_reference_peptides`, `n_neither_peptides` | Marker Peptides (Count), Reference Peptides, Neither Peptides | per `DEF-DIFF-SHARE-PEPTIDES` |
| `share_log2_effect`, `share_se`, `share_df` | Share Log2 Effect, Share Standard Error, Share Degrees Of Freedom | the member's own share fit; empty unless `tested` |

On a share member, the `stat1_*` columns are empty.

**`SetResults.metadata.json`** gains:
- `definition_version` = `DEF-DIFF-SET v1 + DEF-DIFF-SHARE v1` when share rows are present;
- the settings: the signature flank of 5, the minimum of 1 marker and 2 reference peptides, and 2 samples per side;
- each database's sha256, now also read for sequences.

#### Measured against the first freeze (2026-10-19, read only; aging 094)

The 18 rows of hypotheses-splicing-v1 on aging's databases:
- each species' genecentric `*_agingPTM-v4.xml`;
- `aging_isoforms_human.xml` and `aging_isoforms_mouse.xml`.

What they show:
- **Every `isoform_accession` is there but P08592-2**, rat App for H8 in PXD002467. No rat isoform database exists (aging
  AGING-D13, open).
- **All 22 named marker peptides of the other 17 rows overlap their regions, and pass the S2 rule with the 5-residue
  signature.**
  - App exon 15's `GLTTRPGSGLTNIK` is also in P12023-2 and P12023-3. Both hold exon 15's signature, so it passes.
  - H8's `VPTTAASTPDAVDK` starts at residue 289 and is in no other entry (APP770 reads `LPTTAASTPDAVDK`), so it
    passes. A rule needing both sides of a junction would have lost it.
- **P12023-2 and Q62261-2 are only in `aging_isoforms_mouse.xml`.** So H7 and H8 in PXD018399 are testable only on a
  search that held that file.

#### Decisions in this contract taken by QuantProject without a consumer's ruling (open to challenge)

1. **The signature's flank of 5 residues a side.** A single residue, or a short region, alone would be found in almost
   any entry. 5 matches the way aging writes junctions.
2. **"Overlaps" means at least one shared residue,** and for a junction residue a or b. The sequence test, not the
   overlap, decides whether the peptide is specific.
3. **`marker_peptide` is reported against the markers found** (`listed_marker_used`), not read as a rule.
4. **A share single is not moderated.** Moderation across share members could come later, once there are enough of
   them.

## Ledger

| item | us |
|---|---|
| (status) | DATA-DEFINITIONS v3.15 (`DEF-DIFF-SHARE` v1) posted |
| DATAREPO-D7 (our 053) | still open with you |
