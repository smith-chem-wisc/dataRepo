# mzLib 1.0.597 -> 1.0.598: what moves (1.5.0 build list items 1 and 5), 2026-11-12

mzLib 1.0.598 was released 2026-11-12 17:01 UTC with #1555/#1557 (SDRF drafting, U31) and #1578 (`EnsemblXrefAgreement`, item 5).
Item 1 said to take a later release carrying them if it landed before 1.5.0 ships; the user said yes the same day.

**Method.** `feat/1.5.0`'s code at item 11 (`dcab825`), published twice: as is (mzLib 1.0.597, `F:/datarepo_scratch_150/cli_item11`)
and with only the `mzLib` package version changed to 1.0.598 (`cli_598`). Each ingested the same eight deposits from aging's live batch
manifest into its own scratch store, `store_598a` and `store_598b`, at the same time. They were chosen to reach every path the release
notes could touch: PXD011740 (modification-heavy), PXD027232 and PXD028531 (TMT on 1.1.14), PXD036557 (1.1.11), PXD051644 (pooled design
samples), PXD014274 (partial SDRF), PXD042301 (the curated SDRF) and PXD058775 (the notch fallback). Seven read an SDRF through mzLib's
`SdrfDocument`. `compare_stores.py` is item 1's script pointed at these stores (`compare_stores.out`).

**Result: no row moves.** The eight bundle ids are the same on both, as they must be (an id hashes inputs, never code), every table is
equal row for row in both directions, and every copied source is byte-identical. The one difference is `bundle.json`'s
`modification_registry.loader`, which records the mzLib that loaded the modifications (`mzLib 1.0.597` -> `mzLib 1.0.598`).

**The full test suite on 1.0.598 (non-RealData):** 832 passed, 1 skipped, 1 failed, the tutorial test, which fails until release: the same as
on 1.0.597. The code compiled unchanged.

**Item 5 rides it:** the runner now writes `logs:DEF-GENE-RESOLUTION v2` with `ensembl_xref_agreement` filled; measured in
`results/logs_v2_2026-11-12/`.
