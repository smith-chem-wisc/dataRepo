"""Sort every served bundle by whether the databases its search LOADED are recorded with a sha256 (searched_db.tsv, plus each
bundle's recorded input databases). Read only."""
import csv
import json
import os
import sys
from collections import Counter

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "searched_db.tsv"), encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
folder = "F:/aging_data/repo/catalogs"
with open(f"{folder}/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
con = duckdb.connect(f"{folder}/{latest['catalog']}", read_only=True)
paths = dict(con.execute("SELECT dataset_id, path FROM catalog_bundles").fetchall())
versions = dict(con.execute("SELECT dataset_id, search_engine_version FROM datasets").fetchall())

cats = Counter()
detail = []
for r in rows:
    with open(os.path.join(paths[r["dataset_id"]], "bundle.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    inputs = {os.path.basename(s["path"]): s.get("sha256") for s in manifest["sources"] if s["role"].startswith("protein_database:")}
    gptmd = set(filter(None, r["gptmd_names"].split("|")))
    loaded = set(filter(None, r["loaded_by_search"].split("|")))
    unrecorded = sorted(loaded - gptmd - {k for k, v in inputs.items() if v})
    if not loaded:
        cat = "no load lines"
    elif not unrecorded and loaded <= gptmd:
        cat = "searched GPTMD's databases, all recorded with sha256"
    elif not unrecorded:
        cat = "searched the input databases, all recorded with sha256"
    else:
        cat = "searched a database recorded nowhere"
        detail.append((r["dataset_id"], r["bundle_id"], versions.get(r["dataset_id"]), unrecorded))
    cats[cat] += 1
for cat, n in cats.most_common():
    print(f"{n:4d}  {cat}")
for d in detail:
    print("  ", d[0], d[1], "MetaMorpheus", d[2], "unrecorded:", "; ".join(d[3]))
print("bundles with no provenance copy:", [r["dataset_id"] for r in rows if r["provenance_in_bundle"] != "True"])
