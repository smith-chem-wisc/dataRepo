"""PXR-R81: what making the 1% rule the search's own filter moves, over every bundle aging's catalog serves.

Read-only. For each served bundle (catalog_bundles of the catalog latest.json names), over TARGET rows:
  - the tier mzLib's QuantifiedPsmRule.ChooseTier picks from the search's target PSMs (as PtmQtlBundle.Tiers and
    Identifications.ChooseConfidence do): PEP where some pep_q_value is in [0, 1] and the finite PEPs are not all one
    value (or there are none), else the notch where some q_value_notch is in [0, 1], else the q-value;
  - PSMs: passing that tier strictly below 0.01 (S7 today, since 1.4.0) vs passing the search's own filter up to
    MetaMorpheus 1.1.14, q_value <= 0.01 and q_value_notch <= 0.01 where there is one (R81);
  - peptidoforms: the same tier on best_* strictly below 0.01 (D55's peptidoforms_1pct, master, never served) vs
    best_q_value <= 0.01 and best_q_value_notch <= 0.01 where there is one (1.4.5's view, what is served, and R81).
Writes one TSV row per bundle. Usage: python -I measure_r81.py <out.tsv>
"""
import json
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
REPO = "F:/aging_data/repo"
latest = json.load(open(f"{REPO}/catalogs/latest.json", encoding="utf-8"))
catalog = f"{REPO}/catalogs/{latest['catalog']}"
con = duckdb.connect(catalog, read_only=True)
bundles = con.execute(
    "SELECT b.dataset_id, b.bundle_id, b.path, d.search_engine_version FROM catalog_bundles b "
    "LEFT JOIN datasets d USING (dataset_id) ORDER BY b.dataset_id").fetchall()
con.close()
print(f"catalog {latest['catalog_id']} ({latest['builder_version']}): {len(bundles)} bundles", flush=True)

TIER = """
SELECT bool_or(pep_q_value BETWEEN 0 AND 1), bool_or(q_value_notch BETWEEN 0 AND 1),
       min(pep) FILTER (WHERE isfinite(pep)), max(pep) FILTER (WHERE isfinite(pep)), count(*)
FROM read_parquet(?) WHERE target_decoy = 'target'
"""
PSMS = """
SELECT count(*) FILTER (WHERE {tier} < 0.01),
       count(*) FILTER (WHERE q_value <= 0.01 AND (q_value_notch IS NULL OR q_value_notch <= 0.01)),
       count(*) FILTER (WHERE {tier} < 0.01 AND q_value <= 0.01 AND (q_value_notch IS NULL OR q_value_notch <= 0.01)),
       count(*) FILTER (WHERE q_value <= 0.01 AND (q_value_notch IS NULL OR q_value_notch <= 0.01) AND notch_ambiguous IS NOT TRUE)
FROM read_parquet(?) WHERE target_decoy = 'target'
"""
PEPTIDOFORMS = """
SELECT count(*) FILTER (WHERE {tier} < 0.01),
       count(*) FILTER (WHERE best_q_value <= 0.01 AND (best_q_value_notch IS NULL OR best_q_value_notch <= 0.01))
FROM read_parquet(?) WHERE target_decoy = 'target'
"""
COLUMN = {"pep_q_value": "pep_q_value", "q_value_notch": "q_value_notch", "q_value": "q_value"}

db = duckdb.connect()
db.execute("SET threads = 16")
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as out:
    out.write("dataset_id\tbundle_id\tmetamorpheus\ttier\ttarget_psms\tpsms_tier\tpsms_r81\tpsms_both\tpsms_r81_resolved\t"
              "peptidoforms_tier\tpeptidoforms_r81\n")
    for i, (ds, bid, path, mm) in enumerate(bundles, 1):
        psms = f"{path}/psms.parquet"
        try:
            pep_q, notch, lo, hi, n = db.execute(TIER, [psms]).fetchone()
            pep_usable = bool(pep_q) and (lo is None or lo != hi)
            tier = "pep_q_value" if pep_usable else "q_value_notch" if notch else "q_value"
            t, r, both, resolved = db.execute(PSMS.format(tier=COLUMN[tier]), [psms]).fetchone()
            # Served bundles are schema 0.0.16, which has no best_pep_q_value: D55's peptidoform rule cannot be
            # recomputed from them, so only the PSM side is measured.
            pt, pr = "", ""
        except duckdb.Error as e:
            print(f"{ds} {bid}: {e}", flush=True)
            continue
        out.write(f"{ds}\t{bid}\t{mm}\t{tier}\t{n}\t{t}\t{r}\t{both}\t{resolved}\t{pt}\t{pr}\n")
        out.flush()
        if i % 20 == 0:
            print(f"{i}/{len(bundles)}", flush=True)
print("done", flush=True)
