# Measurements behind design/PUBLIC_DATA.md (2026-10-11)

These are scratch measurement scripts in Python (quick work, never shipped), run on DuckDB 1.5.5. They read aging's
store (`F:\aging_data\repo\store`) and never write to it. Their output went to a scratch folder.

| script | measures | used in |
|---|---|---|
| `views_proto.py <outdir>` | a catalog of views over the newest bundle of every deposit: build time, size, query times, file pruning, the sandbox | PUBLIC_DATA §1 |
| `derived_proto.py <catalog>` | today's `BuildDerived` SQL over those views | PUBLIC_DATA §1 |
| `sandbox_allowed.py <catalog>` | D14's sandbox with `allowed_directories` set, then external access off and locked | PUBLIC_DATA §1 |
| `bundle_cols.py <bundle dir>` | which bundle tables carry `dataset_id` / `bundle_id` | PUBLIC_DATA §1 |
| `ducklake/t0`-`t8_*.py`, `rangeserver.py` | the DuckLake evaluation (PXR-R16), on copies of three small bundles. `rangeserver.py` is a static HTTP server with Range support, standing in for Hugging Face or R2 | PUBLIC_DATA §5, §8 |

The DuckLake scripts expect `ducklake/store/` to hold copies of three bundles: PXD035446/5c5f8f73a717d7c4,
PXD058775/ef86a0f83b59b75d and PXD012754/eff05a7486afcee0. `t6_maint.py default1` is the run that shows one default
`CHECKPOINT` scheduling registered bundle files for deletion. It was re-run independently before the result was
reported to PXReprise.
