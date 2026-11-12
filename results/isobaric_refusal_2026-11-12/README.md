# A multiplex search by MetaMorpheus up to 1.1.13 is refused (1.5.0 build list item 9), 2026-11-12

**The user's ruling (2026-11-12):** "i would rather that we re-search these files so we are not carrying around a bunch of rules
and warnings specific to a handful of files." Up to 1.1.13, a TMT/iTRAQ search writes its combined `AllPeptides.psmtsv` with each
peptide's best PSM's PSM-level FDR values, `PEP_QValue` included (MetaMorpheus #2941, merged 2026-11-04, released in 1.1.14). 1.4.2 to
1.4.5 stored such a search with the `isobaric_peptide_q_psm_level` warning and excused its peptide count at build. 1.5.0 refuses it at
ingest instead, and PXReprise is asked to re-search the deposits (PXR-R61).

Everything here is read-only over `F:/aging_data`; the scratch stores are under `F:/datarepo_scratch_150/`.

| file | what it shows |
|---|---|
| `iso_versions.py`, `.out` | aging's serving catalog `d21920c9eb2a2ab6` (read 2026-11-12): 43 isobaric searches, 4 on MetaMorpheus 1.1.13 and 39 on 1.1.14 |
| `iso_113.py`, `.out` | The four: PXD027548 (36 runs), PXD034564 (32), PXD043296 (12), PXD051031 (24). None keeps a per-file `_Peptides.psmtsv`: PXD034564's search wrote them (`WriteIndividualFiles = true`), and PXReprise's prune stage deleted all 32 (`09b_prune/provenance.json`, `deleted`) |
| `ingest_item9.log` | The branch's CLI (`cli_item9`) on two deposits. PXD043296 (1.1.13, TMT) is refused, with the message naming #2941 and 1.1.14. PXD027232 (1.1.14, TMT, one run) ingests as `b33d8bcbd9af59b4` |
| `compare_mm1114.out` | PXD027232 ingested with 1.1.14's settings (`store_item9b`) against item 7's bundle `3092c336f84cc096`: only the two `DEF-TMT-*` definition rows differ, which carry dataRepo's rewritten note. The id moves for isobaric reader 4 |
| `compare_mm1111.out`, `diffrows.py`, `diffrows_mm1111.out` | The first run passed `--mm-settings` for 1.1.11, a mistake: 1.1.11's modifications do not name GlyGly, so 4 peptidoforms key `K[+114.042927]` in place of `K[UNIMOD:121]` (and 5 PSMs, 6 values, 3 sites, 1 ion row with them). **The bundle id was the same, `b33d8bcbd9af59b4`.** The settings folder an operator names reaches rows and not the id. Ingest's default, `<work_root>/mm_settings/<the entry's metamorpheus>`, is covered by the entry's version, so only an explicit `--mm-settings` gets around it. Recorded as G135 |
