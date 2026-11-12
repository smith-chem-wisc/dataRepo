# TMT channel designs, reporter level and empty channels (1.5.0 item 14 a and b; PXR-R54), 2026-11-12

**Built as recommended and agreed by the user (2026-11-12).**

- **Ingest (schema 0.0.17):** each assay keeps its design's `Plex` and `Sample Type` verbatim (`assays.plex`,
  `assays.design_sample_type`). A channel the design marks `empty` (PXReprise's default design since v0.4.41) is an assay with its
  values and **no sample** (`assays.sample_id` NULL, relaxed from required), unless an SDRF names one for it. Each run keeps
  `reporter_level` (`ms2`/`ms3`) from its QC report's `sps_ms3` (PXReprise 098, PXR-R50), only for an isobaric search.
- **Catalog (format 17):** `dataset_overview.quant_scale` (`label_free_apex`; `reporter_ms2`, `reporter_ms3`,
  `reporter_level_mixed`, `reporter_level_not_recorded`; NULL otherwise) and the view `isobaric_channels`, one row per (run,
  channel).

**`quant_scale_survey.py`** (read-only on aging's serving catalog `3bde62130d08a4c4`): the 43 served isobaric searches, by the
build's rule from the QC report each bundle copied. 39 on MetaMorpheus 1.1.14: 29 `reporter_ms2`, 10 `reporter_ms3`. The four on
1.1.13 (out of 1.5.0 until re-searched, D64): 2 and 2, as PXReprise 098 said. None mixed, none unrecorded.

**Empty channels are common, not rare.** 4,884 design rows read `empty` across the 203 TmtDesign.txt copies under
`F:\aging_data` (searches and served bundles). Today each is a sample.

**`compare_pxd002528.py`:** PXD002528 (1.1.14, 20 runs, TMT, MS2) ingested by this code against its served 1.4.5 bundle. Its design
marks 116 of its 200 channels `empty`.

- assays 200 both; samples 200 -> **84** (the 116 empty channels' samples are gone); quant_values 770,446 both.
- the 116 empty assays carry no sample and `design_sample_type = empty`; 20 plexes, one per run; every run `ms2`.
- values on empty channels: 254,704 at a median of 1.565e4; on study samples 515,742 at 6.476e5 (about 1/40: spill-over).
- **Every value is the same** once the feature key is set aside. 521 rows moved key only, all item 1's (mzLib 1.0.597 links
  UniProt modifications such as N6-succinyllysine to Unimod, here from `[Info:...]` names), to be announced with it.
