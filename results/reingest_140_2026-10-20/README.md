# 1.4.0's whole-store scratch re-ingest (2026-10-20)

The measurement 1.4.0's date waits on (G103; PXReprise 051, our 052). Every deposit in aging's store was re-ingested
with the 1.4.0 branch and compared with the bundle the store holds. Each difference is traced to one of 1.4.0's items,
or to an input that changed on disk.

**Result:**
- 168 of 171 deposits re-ingested without error.
- Every difference in rows is explained.
  - Two exact checks pass: G101 touches only the two keratins, and PXR-R23 adds only pooled rows.
  - Nothing is unexplained.
- Three deposits could not be re-ingested, because their search outputs are gone while PXReprise re-searches them.
- On the 1.4.0 window: three ingests at a time take **5.0 h of wall time**, alongside PXReprise's running batch.

## How

- **Code:** `feat/1.4.0-ingest` at `54453e1`, published self-contained as `datarepo 1.4.0-scratch.54453e1` (ingest path
  `cs-1.2.0`, schema 0.0.16, mzLib 1.0.595).
- **Inputs:** a snapshot of `F:\aging_data\batch\manifest.yaml` taken at 00:15 UTC: 179 entries, 171 `include`, and the
  seven `operator_sdrf` entries aging named.
  - Called as PXReprise calls it: `ingest <manifest> <accession> --json --store <scratch>`, three at a time, largest
    first (`one.sh`).
  - It read `F:\aging_data` only and wrote only to a scratch folder off it.
- **Baseline:** each deposit's newest bundle in `F:\aging_data\repo\store`, all `cs-1.1.0` on schema 0.0.15 (`prep.py`).
  Four of these are newer than catalog `c4a89ff3b31f3d62` (PXReprise 055's re-ingests).
- **Comparison:**
  - `compare.py`: bundle ids, rows per table, sources changed (by role and sha256), and findings gone or new.
  - `explain.py`: the cause of each difference.
  - `strict.py`: the two exact checks.
- **Not covered by row counts:** values that change inside an unchanged count.
  - G26 writes another ProForma tag for ten modification tokens.
  - The new columns `assays.assay_kind`, `assays.design_label` and `ptm_sites.sequence_window`.
  - These were measured where they were built, not here.

## Timing

- **Wall time:** 00:16 to 05:15 UTC, 5.0 h, three ingests at a time.
- **Serial time:** 15.0 h.
- **Per deposit:** median 151 s, 90th percentile 751 s.
- **Longest:** PXD002467, 6,521 s; PXD027754 2,876 s; PXD018545 2,651 s. The largest ingests held about 36 GB of memory
  each.
- **Output:** 19 GB of scratch bundles.

## Every difference, by cause (`explained.tsv`)

| cause | deposits | what changed |
|---|---|---|
| G26 (registry from mzLib's loaders) | 159 | the `unresolved_modifications` finding is gone; no row count moves |
| G101 (the keratins' searched sequence) | 28 | 375 fewer `ptm_sites` rows. **Only O76011 and P19013 change, in every one of the 28** (`strict.py`): the double placement of their shared stretch is gone |
| PXR-R22 (the SDRF the search used; G107's `operator_sdrf`) | 10 | samples and characteristics as the search's own SDRF has them. E.g. PXD002467: 48 samples where the deposit's SDRF has 96; PXD011740: 12 samples and 24 characteristics where there were none |
| PXR-R23 (pooled assays) | 9 | 165 pooled assays, 354 `assay_runs` rows, **908,303 protein-group values and 49,893 occupancy rows that 1.3.x withheld**. Each gained row sits on a `design_sample` assay, in all 9 (`strict.py`) |
| G106 (conflicting SDRF rows) | 1 | PXD012307: one characteristic fewer and `sdrf_conflicting_rows`, as built for |
| contaminant database restored (below) | 2 | PXD038328 and PXD061654: +338 sites and +3,995 occupancy rows; `contaminant_label_unresolved` is gone |
| no row difference | 8 | |
| not re-ingested | 3 | PXD031223, PXD031782, PXD038718: their `04_search` is gone (below) |

- The PXR-R22 and PXR-R23 sets overlap: seven of them come from the seven `operator_sdrf` entries (aging 114).
  - These are the Jarome ubiquitin captures, two injections per animal.
  - With the curated SDRF their samples are pooled assays of two injections. Their values are now stored.
  - The ptmQtl engines leave those values out, as DATAREPO-P32 (b) asks.
- Every bundle id moves, as a new ingest path must.
  - These ids are not the release's: the branch has changed the ingest since `54453e1`, in `ccf7acf`.
  - That change gives a protein N-terminal site the window of residue 1. It moves no row count.

## Found on the way

1. **24 deposits read a contaminant database from PXReprise pin folders that had been deleted**
   (`pxreprise-0ba5e4c`, `-2eb9a52`, `-cfbe603`; their 2026-10-12 cleanup).
   - A re-ingest then had no contaminant sequences. PXD027754, for one, lost 33 site rows and got
     `contaminant_label_unresolved`.
   - Every file had a copy with the same sha256 in a later pin (`missing.py`, `missing_sources.tsv`).
   - **PXReprise restored all three at 01:48 UTC** (copy checked by sha256, a README guarding each folder) and keeps
     every old pin's `profiles\lists` until 1.4.0's re-ingest.
   - The three deposits read before the restore were re-ingested after it, and match.
   - Two stored bundles had been ingested on 2026-10-12, after the cleanup: PXD038328 and PXD061654. The bundles aging
     serves today lack their contaminant sequences. 1.4.0's re-ingest repairs them (the table's last cause row).
   - The lasting fix, databases out of pin folders or G96's sha256 registry, is on PXReprise's list.
2. **Three deposits have no search outputs**, being re-searched (PXReprise, 2026-10-20):
   - PXD031223, a catch-up re-search, searched tonight;
   - PXD038718, re-searched in tonight's swap gap;
   - PXD031782, parked until aging gives a protease per file.
   - At the 1.4.0 swap a 0.0.16 catalog refuses their 0.0.15 bundles, so they drop out until their new searches are
     ingested. PXD031782 will.

## The ptmQtl engines on the new bundles

- The engines' reader and rules ran on every re-ingested bundle (scratch harness, `ptmqtl_check`).
- Two refusals followed. One was a fault, fixed in `c4f9b51`; the other is correct.
  - 8 deposits were refused because a sample's two repeat injections were read as unknown fractions: PXD042301 and the
    seven ubiquitin captures. The fix keeps each injection a run, as S4 says, reading the technical replicate.
  - PXD012307 stays refused: its SDRF puts eight animals under one source name. aging's `operator_sdrf` for it (G107) is
    the fix.
- S2c and S2d reproduce ptmQtl's own exclusion lists site for site on the deposits compared:
  - S2c: PXD018545 and PXD027754;
  - S2d: PXD047288, PXD057490 and PXD009212.
  - See `design/PTMQTL_ENGINE.md`.

## For 1.4.0's window

- Plan on about 5 h with three ingests at a time beside the batch. PXD002467 alone takes 1.8 h; start it first.
- Every failure here was a missing input, not code.
- Before the window:
  - check each deposit's database files and search folder exist (`missing.py`);
  - expect PXD031782 to drop out;
  - and PXD031223 and PXD038718 too, unless their new searches are ingested first.
