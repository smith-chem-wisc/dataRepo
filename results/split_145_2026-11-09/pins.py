"""Print `--bundle acc=id` pins for every bundle aging's serving catalog holds, one per line. Read only."""
import json
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
folder = "F:/aging_data/repo/catalogs"
with open(f"{folder}/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
con = duckdb.connect(f"{folder}/{latest['catalog']}", read_only=True)
rows = con.execute("SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY dataset_id").fetchall()
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as out:
    json.dump({"catalog": latest["catalog"], "catalog_id": latest["catalog_id"], "builder": latest["builder_version"],
               "bundles": rows}, out, indent=1)
print(latest["catalog"], latest["builder_version"], len(rows), "bundles;",
      sum(1 for d, _ in rows if "-" in d), "split keys")
