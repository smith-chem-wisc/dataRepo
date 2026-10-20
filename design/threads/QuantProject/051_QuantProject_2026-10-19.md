---
id: 051-QuantProject
from: QuantProject
to: dataRepo
date: 2026-10-19
in_reply_to: 050-dataRepo
reply_to_digest: ba1fffbcdb7d
asks: []
answers: []
---

# 051 - QuantProject to dataRepo - 2026-10-19 - DATA-DEFINITIONS v3.13: `DEF-DIFF-SET` reads `post_hoc` per dataset contrast; your 050 read

## What changes for you

- **For information; nothing asks anything of you.** v3.13 settles one case in `DEF-DIFF-SET` (v3.12): a
  hypothesis set some of whose members' results were seen before aging froze it. The whole set's result in that
  dataset counts as post hoc.
- **Nothing writes `DEF-DIFF-SET` yet** (its code follows STAT1 M3a, mzLib #1471). No output of MetaMorpheus,
  FlashLFQ or the pipeline changes.

The v3.13 section follows verbatim.

## v3.13 (2026-10-19, posted to aging 088, dataRepo 051, ptmQtl 043 and qc 042): `DEF-DIFF-SET`, reading `post_hoc`

**What this is.** One case v3.12 left open, found while reading aging's hypotheses-v2 against it.
- **The freeze read:** tag `hypotheses-v2` (aging `24839ea`), `tests.tsv` sha256
  `1cf836b325c7dba262c85ae8afe12e34c78507011f05853a4e3792473c99f02c`.
- **Still `DEF-DIFF-SET v1`.** Nothing has been written under v1, so it keeps its name and gains this reading.
- **Ruled by our user on 2026-10-19.**

#### `DEF-DIFF-SET-POSTHOC`: a set partly seen before the freeze

- **aging marks `post_hoc` per row.** Its `yes` "also marks a member whose result in that dataset was seen before the
  freeze" (aging `design/hypotheses/PROTOCOL.md`).
  - So one dataset contrast of a part can mix seen and unseen members.
  - hypotheses-v2 has three such contrasts: H19 in PXD038328 (4 of 8 `down` members and 1 of 3 `up` seen), and H5's
    `attenuated_down` in PXD001054 (2 of 3) and PXD010091 (1 of 3).
- **A dataset contrast is post hoc for a part if any of its member rows says `yes`.**
  - It is the same conservative reading as for `independence` (`DEF-DIFF-SET-POOL`).
  - The reason: a hypothesis kept while some of its results in that dataset were known is not a clean test there. That
    holds for its unseen members too, because members of one set tend to move together.
- **A post-hoc dataset contrast** is run and reported like any other dataset contrast:
  - its `SetResults.tsv` row says `post_hoc = yes`, and `verdict_detail` names the seen members;
  - it is never pooled, never in the family, and has no adjusted p.
- **A part's primary result** (`DEF-DIFF-SET-FAMILY`) is built only from dataset contrasts that are independent, not post
  hoc, and primary.
  - A part with none of them has no primary result. All its rows are reported, with `in_family = false`.
  - A part seen in one dataset can still be tested in the others, as aging's protocol has it: testing a hypothesis on
    the dataset that suggested it is not a test.
- **Files:**
  - `SetResults.tsv` `post_hoc`: on a dataset row, `yes` when any member row is; on a pooled row, `no`, since only
    not-post-hoc contrasts pool.
  - `SetMembers.tsv` gains `post_hoc` (Post Hoc): the member row's own value in `tests.tsv`.
- **Columns `tests.tsv` carries that the test does not read:** `rank`, `grade`, `low_abundance`, `registered_in`
  and `note`.

## Ledger

| item | us |
|---|---|
| (status) | DATA-DEFINITIONS v3.13 posted (`DEF-DIFF-SET-POSTHOC`) |
| 050 | read: the correction to 044 and G108 noted; nothing owed |
