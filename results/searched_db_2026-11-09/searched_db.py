"""Which database did each served search actually read, and does its bundle say so? (2026-11-09; the user: "without it there is
no hope of reproducing a result".) Read only: aging's serving catalog, each bundle's copy of the search provenance, the search's
results.txt, and the GPTMD files' sizes on disk. Writes searched_db.tsv beside this script."""
import csv
import json
import os
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))
folder = "F:/aging_data/repo/catalogs"
with open(f"{folder}/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
con = duckdb.connect(f"{folder}/{latest['catalog']}", read_only=True)
bundles = con.execute("SELECT dataset_id, bundle_id, path FROM catalog_bundles ORDER BY dataset_id").fetchall()
print(latest["catalog"], latest["builder_version"], len(bundles), "bundles")

LOADED = re.compile(r"^\t(.+?\.(?:xml|fasta)(?:\.gz)?): (\d+) Proteins", re.I)
rows = []
for dataset, bundle, path in bundles:
    with open(os.path.join(path, "bundle.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    inputs = [s for s in manifest["sources"] if s["role"].startswith("protein_database:")]
    prov_src = next((s for s in manifest["sources"] if s["role"] == "provenance:04_search"), None)
    gptmd, prov_ok = [], False
    if prov_src is not None:
        with open(os.path.join(path, prov_src["bundle_path"]), encoding="utf-8") as handle:
            prov = json.load(handle)
        prov_ok = True
        gptmd = [o for o in prov.get("outputs", []) if re.search(r"GPTMD\.xml$", o.get("path", ""), re.I)]
    results = next((s for s in manifest["sources"] if s["role"] == "results_txt"), None)
    loaded = []
    # The bundle's own copy: the run folder may have been searched again since this bundle was written.
    copy = os.path.join(path, results["bundle_path"]) if results is not None and results.get("bundle_path") else None
    if copy is not None and os.path.exists(copy):
        with open(copy, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        # Only the search task's own block (results.txt holds the last task's report).
        loaded = [m.group(1) for m in (LOADED.match(l) for l in lines) if m]
    work_root = manifest.get("manifest", {}).get("work_root") if isinstance(manifest.get("manifest"), dict) else None
    on_disk, same_size, total = 0, 0, 0
    for o in gptmd:
        full = os.path.join("F:/aging_data", o["path"])
        total += o.get("size_bytes") or 0
        if os.path.exists(full):
            on_disk += 1
            same_size += int(os.path.getsize(full) == o.get("size_bytes"))
    names = {os.path.basename(o["path"]) for o in gptmd}
    missing = [os.path.basename(o["path"]) for o in gptmd if not (os.path.exists(os.path.join("F:/aging_data", o["path"])) and os.path.getsize(os.path.join("F:/aging_data", o["path"])) == o.get("size_bytes"))]
    rows.append({
        "dataset_id": dataset, "bundle_id": bundle,
        "inputs_recorded": len(inputs),
        "provenance_in_bundle": prov_ok,
        "gptmd_outputs": len(gptmd),
        "gptmd_with_sha256": sum(1 for o in gptmd if o.get("sha256")),
        "gptmd_bytes": total,
        "loaded_by_search": "|".join(loaded),
        "loaded_all_gptmd_outputs": bool(loaded) and set(loaded) <= names,
        "gptmd_on_disk": on_disk, "gptmd_same_size": same_size, "gptmd_names": "|".join(sorted(names)), "gptmd_not_as_recorded": "|".join(missing),
    })

with open(os.path.join(here, "searched_db.tsv"), "w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

n = len(rows)
def count(pred): return sum(1 for r in rows if pred(r))
print("provenance copy in bundle:", count(lambda r: r["provenance_in_bundle"]), "of", n)
print("search ran GPTMD (outputs recorded):", count(lambda r: r["gptmd_outputs"] > 0))
print("every GPTMD output has a sha256:", count(lambda r: r["gptmd_outputs"] > 0 and r["gptmd_with_sha256"] == r["gptmd_outputs"]))
print("search loaded exactly GPTMD's outputs (results.txt):", count(lambda r: r["loaded_all_gptmd_outputs"]))
print("no results.txt load lines read:", count(lambda r: not r["loaded_by_search"]))
print("GPTMD files all still on disk at the recorded size:", count(lambda r: r["gptmd_outputs"] > 0 and r["gptmd_same_size"] == r["gptmd_outputs"]))
print("GPTMD bytes, all searches: %.1f GB" % (sum(r["gptmd_bytes"] for r in rows) / 1e9))
others = [r for r in rows if r["gptmd_outputs"] > 0 and not r["loaded_all_gptmd_outputs"]]
for r in others[:8]:
    print("  loaded other than GPTMD's outputs:", r["dataset_id"], "| loaded:", r["loaded_by_search"][:150], "| recorded:", r["gptmd_names"][:150])
for r in [r for r in rows if r["gptmd_outputs"] > 0 and r["gptmd_same_size"] < r["gptmd_outputs"]]:
    print("  GPTMD file not on disk as recorded:", r["dataset_id"], r["bundle_id"], r["gptmd_not_as_recorded"][:160])
for r in [r for r in rows if r["gptmd_outputs"] == 0][:3]:
    print("  no GPTMD output recorded:", r["dataset_id"], r["loaded_by_search"][:200])
