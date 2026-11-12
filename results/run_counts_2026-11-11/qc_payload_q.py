"""Read-only (item 7): for every deposit aging serves, is there a 05_qc/qc_payload.json, which schema, and do its
per-file metrics carry psms / peptides / protein_groups, under which definitions? Does the served bundle copy it?"""
import json, sys, collections
from pathlib import Path
import duckdb, yaml
sys.stdout.reconfigure(encoding="utf-8")
root = "F:/aging_data/repo/catalogs/"
latest = json.load(open(root + "latest.json"))
con = duckdb.connect(root + latest["catalog"], read_only=True)
served = dict(con.sql("SELECT dataset_id, bundle_id FROM catalog_bundles").fetchall())
runs = dict(con.sql("SELECT dataset_id, count(*) FROM runs GROUP BY 1").fetchall())
manifest = yaml.safe_load(open("F:/aging_data/batch/manifest.yaml", encoding="utf-8"))
run_of = {e["accession"]: e.get("run") for e in manifest["datasets"]}
store = Path("F:/aging_data/repo/store")
summary = collections.Counter()
rows = []
for ds in sorted(served):
    run = run_of.get(ds)
    payload = Path("F:/aging_data") / run / "05_qc" / "qc_payload.json" if run else None
    bundle = json.load(open(store / ds / served[ds] / "bundle.json", encoding="utf-8"))
    roles = sorted({s.get("role") for s in bundle.get("sources", [])})
    copied = any("payload" in (s.get("role") or "") or "qc_payload" in (s.get("bundle_path") or "") for s in bundle.get("sources", []))
    if not payload or not payload.exists():
        rows.append((ds, "no payload", "", "", "", copied)); summary["no payload"] += 1; continue
    p = json.load(open(payload, encoding="utf-8"))
    files = p.get("files") or []
    have = {k: sum(1 for f in files if (f.get("metrics") or {}).get(k) is not None) for k in ("psms", "peptides", "protein_groups")}
    defs = {k: (p.get("definitions") or {}).get(k, {}).get("id") for k in ("psms", "peptides", "protein_groups")}
    rows.append((ds, p.get("schema"), len(files), runs.get(ds), have, copied, defs))
    summary[p.get("schema")] += 1
print("catalog", latest["catalog_id"], "deposits", len(served))
print(dict(summary))
print("bundles copying a payload:", sum(1 for r in rows if r[5]))
for r in rows:
    print("\t".join(str(v) for v in r))
