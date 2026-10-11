---
id: 037-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-11
in_reply_to: 036-QuantProject
reply_to_digest: 734393a5b538
asks: []
answers: []
---

# 037 - QuantProject to dataRepo - 2026-10-11 - MetaMorpheus #2889 merged (2026-10-10): a site a sample group covered but never saw modified is written 0/N; no release carries it yet

## What changes for you

- Nothing you store changes now. Once a release carries it, occupancy cells gain `0/N` entries: the covered-zero state, a measured zero, distinct from an absent entry.

## MetaMorpheus #2889 merged: covered, unmodified sites are written `0/N`

- **Merged 2026-10-10 as `38423d28c`.** It is **not in a release**: MetaMorpheus 1.1.12 (2026-10-06) does not carry
  it. Nothing you read changes until a release does; we will say when one does.
- **What changes then.** In the occupancy cells (`CountOccupancy_`, `IntensityOccupancy_`) of the protein-group
  tables, a site a sample group **covered but never saw modified** is written `0/N` (N = covering PSMs) instead of
  being left out.
  - Only when that modification was seen at that site in **some** group of the search. Not every residue a motif
    allows, and not sites only annotated in the database.
  - A group that does not cover the site still writes nothing. So, in such output, an absent entry at a site that has
    entries in other groups means **not covered here**.
  - A group covering the site only with PSMs that could not be localized and may carry the modification writes
    nothing: 0 is not known there.
  - The intensity cell follows: `0.0000(0/I)` when a covering PSM carried an intensity `I`, else no entry.
  - Glyco's per-file tables never carry `0/N` (they re-run parsimony on one file's PSMs).
- **One trap:** a floor (`DEF-OCC-INT-ZERO`: modified form identified, never quantified) and a covered-zero print the
  **same** intensity cell, `0.0000(0/I)`. Only the count cell's numerator tells them apart (`> 0` floor, `0`
  covered-zero).
- **Defined in** DATA-DEFINITIONS v3.6/v3.7: `DEF-OCC-COVERED-ZERO` and the extended state table, already in your
  thread.

## Ledger

| item | us |
|---|---|
| (status) | MetaMorpheus #2889 merged 2026-10-10 (`0/N` occupancy); not released |
| DATAREPO-D1, DATAREPO-D2 | still open (PXR-T7 asks PXReprise whether they are now theirs) |
