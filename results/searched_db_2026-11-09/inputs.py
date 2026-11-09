"""The ORIGINAL databases the served searches started from (GPTMD's inputs, or what a search without GPTMD read): how many
distinct by sha256, how big, and whether each is still on disk at its recorded path. Read only."""
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
folder = "F:/aging_data/repo/catalogs"
with open(f"{folder}/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
con = duckdb.connect(f"{folder}/{latest['catalog']}", read_only=True)
seen = {}
for (path,) in con.execute("SELECT path FROM catalog_bundles").fetchall():
    with open(os.path.join(path, "bundle.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    for s in manifest["sources"]:
        if s["role"].startswith("protein_database:") and s.get("sha256"):
            seen.setdefault(s["sha256"], set()).add(s["path"])
present, size = 0, 0
for sha, paths in seen.items():
    here = [p for p in paths if os.path.exists(p)]
    if here:
        present += 1
        size += os.path.getsize(here[0])
print(f"distinct input databases: {len(seen)}; on disk at a recorded path: {present}; their size {size/1e9:.1f} GB")
