"""Would aging's served bundles raise #48's findings? Read-only.

For each bundle aging's latest catalog serves: the databases its bundle.json recorded as missing at ingest, and whether
each database its search provenance names is on disk now (resolved as the manifest's work_root resolves it). And
whether <work_root>/mm_settings/<release> exists for every MetaMorpheus release served.
"""
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
REPO = "F:/aging_data/repo"
WORK_ROOT = "F:/aging_data"
latest = json.load(open(f"{REPO}/catalogs/latest.json", encoding="utf-8"))
con = duckdb.connect(f"{REPO}/catalogs/{latest['catalog']}", read_only=True)
rows = con.execute("SELECT b.dataset_id, b.path, d.search_engine_version FROM catalog_bundles b "
                   "LEFT JOIN datasets d USING (dataset_id) ORDER BY 1").fetchall()
con.close()

recorded_missing, missing_now, checked = [], [], 0
for ds, path, mm in rows:
    meta = json.load(open(f"{path}/bundle.json", encoding="utf-8"))
    dbs = meta.get("protein_databases") or {}
    if dbs.get("missing"):
        recorded_missing.append((ds, dbs["missing"]))
    prov_path = f"{path}/sources/provenance_04_search.json"
    if not os.path.exists(prov_path):
        continue
    prov = json.load(open(prov_path, encoding="utf-8"))
    for item in prov.get("inputs") or []:
        p = str(item.get("path", ""))
        if p.lower().endswith((".xml", ".fasta", ".fa", ".xml.gz", ".fasta.gz")):
            checked += 1
            full = p if os.path.isabs(p) else os.path.join(WORK_ROOT, p)
            if not os.path.exists(full):
                missing_now.append((ds, p))

releases = sorted({mm for _, _, mm in rows if mm})
print(f"catalog {latest['catalog_id']}: {len(rows)} bundles")
print(f"bundles whose bundle.json recorded a missing database at ingest: {len(recorded_missing)}")
for ds, m in recorded_missing[:10]:
    print(f"  {ds}: {m}")
print(f"search-provenance databases checked on disk now: {checked}; missing now: {len(missing_now)}")
for ds, p in missing_now[:15]:
    print(f"  {ds}: {p}")
for r in releases:
    d = f"{WORK_ROOT}/mm_settings/{r}"
    print(f"mm_settings/{r}: {'present' if os.path.isdir(d) else 'MISSING'}"
          + (f" (Mods {os.path.isdir(d + '/Mods')}, Data {os.path.isdir(d + '/Data')})" if os.path.isdir(d) else ""))
