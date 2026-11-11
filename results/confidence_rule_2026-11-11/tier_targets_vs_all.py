"""Scratch, read-only (1.5.0 build list item 2): for every bundle aging's serving catalog holds, the tier mzLib's
QuantifiedPsmRule.ChooseTier gives from the search's TARGET PSMs only (ptmQtl S7, our choice; the user, 2026-11-11) and
from every PSM's PEP, decoys included (mzLib's own doc comment). ChooseTier reads: any PEP q-value of a target in [0, 1];
any notch q-value of a target in [0, 1]; whether the finite PEPs it is given hold more than one distinct value. So the two
forms can differ only on the last test. Prints every bundle where they differ, and the tiers' counts."""
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
ROOT = "F:/aging_data/repo"
with open(f"{ROOT}/catalogs/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
print("catalog", latest["catalog_id"], latest["builder_version"])
cat = duckdb.connect(os.path.join(f"{ROOT}/catalogs", latest["catalog"]), read_only=True)
bundles = cat.execute("SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY dataset_id").fetchall()
cat.close()

con = duckdb.connect()
con.execute("SET threads=32")


def tier(pep_q_ok, notch_ok, distinct_peps, any_finite):
    pep_usable = pep_q_ok and (not any_finite or distinct_peps > 1)
    return "pep_q_value" if pep_usable else "q_value_notch" if notch_ok else "q_value"


counts, differ = {}, []
for dataset, bundle in bundles:
    path = f"{ROOT}/store/{dataset}/{bundle}/psms.parquet"
    r = con.execute(f"""
        SELECT bool_or(pep_q_value BETWEEN 0 AND 1) FILTER (WHERE target_decoy = 'target'),
               bool_or(q_value_notch BETWEEN 0 AND 1) FILTER (WHERE target_decoy = 'target'),
               count(DISTINCT pep) FILTER (WHERE target_decoy = 'target' AND isfinite(pep)),
               count(pep) FILTER (WHERE target_decoy = 'target' AND isfinite(pep)) > 0,
               count(DISTINCT pep) FILTER (WHERE isfinite(pep)),
               count(pep) FILTER (WHERE isfinite(pep)) > 0
        FROM '{path}'""").fetchone()
    targets = tier(bool(r[0]), bool(r[1]), r[2], r[3])
    everything = tier(bool(r[0]), bool(r[1]), r[4], r[5])
    counts[targets] = counts.get(targets, 0) + 1
    if targets != everything:
        differ.append((dataset, bundle, targets, everything))
    if targets != "pep_q_value":
        print(f"  {dataset} {bundle}: {targets} (target PEPs distinct {r[2]}, all PEPs distinct {r[4]})")
print(len(bundles), "bundles; tiers from target PSMs:", counts)
print("differ between target-only and all PSMs:", differ if differ else "none")
