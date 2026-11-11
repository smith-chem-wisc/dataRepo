# `datarepo verify` on real bundles (1.5.0 build list item 6, D61), 2026-11-11

Built from `feat/1.5.0` with item 6 (a Release build copied to `F:/datarepo_scratch_150/cli_item6`).

- **`verify_item6_scratch.log`:** PXD058775 ingested with item 6 into `F:/datarepo_scratch_150/store_item6` verifies `ok: 17
  table(s), 6 copied source(s)`, exit 0. A copy with one byte appended to `peptidoform_ions.parquet`
  (`store_item6_tampered`) reports that one file `changed`, with both sha256, exit 1.
- **`verify_aging_store.log`:** read-only over aging's store `F:/aging_data/repo/store` (`verify` only reads and hashes).
  568 bundles: all written before 1.5.0, so all read "no table checksums: tables NOT verified", and **every copied
  source of all 568 matches the sha256 its `bundle.json` recorded** (0 changed, missing or extra). Exit 0.
