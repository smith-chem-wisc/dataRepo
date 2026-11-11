"""Scratch, read-only (1.5.0 build list item 2): PXD058775 (the one notch search) and PXD057502 (no peptidoform passes
the PEP rule) ingested by feat/1.5.0's item-2 code into F:/datarepo_scratch_150/store_item2, against the bundles aging's
serving catalog holds (datarepo 1.4.5, cs-1.2.0, mzLib 1.0.595). Prints the new columns and findings, then compares
every table row for row with the new columns left out, so what else moved is visible (mzLib 1.0.597's peptidoform keys
are expected to)."""
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
ROOT = "F:/aging_data/repo"
NEW = "F:/datarepo_scratch_150/store_item2"
with open(f"{ROOT}/catalogs/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
cat = duckdb.connect(os.path.join(f"{ROOT}/catalogs", latest["catalog"]), read_only=True)
served = dict(cat.execute("SELECT dataset_id, bundle_id FROM catalog_bundles WHERE dataset_id IN ('PXD058775', 'PXD057502')").fetchall())
cat.close()
print("catalog", latest["catalog_id"], served)
con = duckdb.connect()
NEW_COLUMNS = {"datasets": ["confidence_rule"], "peptidoforms": ["best_pep_q_value"]}
for ds, old_bundle in sorted(served.items()):
    new_bundle = os.listdir(f"{NEW}/{ds}")[0]
    a, b = f"{ROOT}/store/{ds}/{old_bundle}", f"{NEW}/{ds}/{new_bundle}"
    print(f"\n{ds}: served {old_bundle} -> item 2 {new_bundle}")
    print("  confidence_rule:", con.sql(f"SELECT confidence_rule FROM '{b}/datasets.parquet'").fetchone()[0])
    print("  target peptidoforms: pep_q < 0.01 / notch < 0.01 / q-value rule (1.4.5 view) / best_pep_q_value NULL / > 1:",
          con.sql(f"""SELECT count(*) FILTER (WHERE best_pep_q_value < 0.01), count(*) FILTER (WHERE best_q_value_notch < 0.01),
                             count(*) FILTER (WHERE best_q_value <= 0.01 AND (best_q_value_notch IS NULL OR best_q_value_notch <= 0.01)),
                             count(*) FILTER (WHERE best_pep_q_value IS NULL), count(*) FILTER (WHERE best_pep_q_value > 1)
                      FROM '{b}/peptidoforms.parquet' WHERE target_decoy = 'target'""").fetchone())
    for code, message in con.sql(f"SELECT code, message FROM '{b}/findings.parquet' WHERE code LIKE 'confidence_rule%'").fetchall():
        print(f"  finding {code}: {message}")
    for table in sorted(f for f in os.listdir(b) if f.endswith(".parquet")):
        name = table[:-8]
        if not os.path.exists(f"{a}/{table}"):
            print(f"  {name:<32} new table")
            continue
        keep = [c for c, *_ in con.sql(f"DESCRIBE SELECT * FROM '{a}/{table}'").fetchall()]
        cols = ", ".join(f'"{c}"' for c in keep)
        only_a = con.sql(f"SELECT count(*) FROM (SELECT {cols} FROM '{a}/{table}' EXCEPT ALL SELECT {cols} FROM '{b}/{table}')").fetchone()[0]
        only_b = con.sql(f"SELECT count(*) FROM (SELECT {cols} FROM '{b}/{table}' EXCEPT ALL SELECT {cols} FROM '{a}/{table}')").fetchone()[0]
        added = [c for c, *_ in con.sql(f"DESCRIBE SELECT * FROM '{b}/{table}'").fetchall() if c not in keep]
        print(f"  {name:<32} {'equal' if only_a == only_b == 0 else f'{only_a} only served, {only_b} only new'}"
              + (f"  (+ columns {added})" if added else ""))
