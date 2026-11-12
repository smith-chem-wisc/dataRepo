"""Read-only (1.5.0 item 7): for every deposit aging serves, find the QC-payload stage the way ingest will (a stage folder
of the run whose provenance.json says `stage: qc_payload` and names, by sha256, the search provenance the served bundle
copied), and report what reading its per-file psms / peptides / protein_groups would give: schema, definitions, files
matched to the bundle's runs, counts present, and the sums against results.txt's deposit-wide lines."""
import collections
import hashlib
import json
import sys
from pathlib import Path

import duckdb
import yaml

sys.stdout.reconfigure(encoding="utf-8")
WORK = Path("F:/aging_data")
root = WORK / "repo" / "catalogs"
latest = json.load(open(root / "latest.json"))
con = duckdb.connect(str(root / latest["catalog"]), read_only=True)
print("catalog", latest["catalog_id"], latest["builder_version"], latest["pointed_utc"])
served = dict(con.sql("SELECT dataset_id, bundle_id FROM catalog_bundles").fetchall())
runs = collections.defaultdict(set)
for ds, run_id in con.sql("SELECT dataset_id, run_id FROM runs").fetchall():
    runs[ds].add(run_id.split(":", 1)[1])
dataset_counts = {(ds, n): v for ds, n, v in con.sql(
    "SELECT scope_id, name, value FROM metrics WHERE scope = 'dataset' AND source = 'results.txt'").fetchall()}
manifest = yaml.safe_load(open(WORK / "batch" / "manifest.yaml", encoding="utf-8"))
entry_of = {e["accession"]: e for e in manifest["datasets"]}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


tally = collections.Counter()
rows = []
for ds in sorted(served):
    e = entry_of.get(ds)
    if not e:
        tally["no manifest entry"] += 1
        continue
    run_dir = WORK / e["run"]
    search_prov = run_dir / (e.get("stages") or {}).get("search", "04_search") / "provenance.json"
    search_sha = sha(search_prov) if search_prov.exists() else None
    stages = []
    for d in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        prov = d / "provenance.json"
        if not prov.exists():
            continue
        try:
            doc = json.load(open(prov, encoding="utf-8"))
        except Exception:
            continue
        if doc.get("stage") == "qc_payload":
            stages.append((d, doc))
    if not stages:
        tally["no payload stage"] += 1
        rows.append((ds, "no payload stage"))
        continue
    matching = [(d, doc) for d, doc in stages if any(u.get("sha256") == search_sha for u in doc.get("upstream") or [])]
    if len(matching) != 1:
        tally[f"{len(matching)} of {len(stages)} payload stages name this search"] += 1
        rows.append((ds, f"{len(matching)} of {len(stages)} stages match", [str(d.name) for d, _ in stages]))
        continue
    d, doc = matching[0]
    payload = d / "qc_payload.json"
    recorded = [o.get("sha256") for o in doc.get("outputs") or [] if str(o.get("path", "")).replace("\\", "/").endswith("/qc_payload.json")]
    if not payload.exists():
        tally["stage but no payload file"] += 1
        rows.append((ds, "no payload file"))
        continue
    actual = sha(payload)
    if recorded != [actual]:
        tally["payload sha256 not the recorded one"] += 1
        rows.append((ds, "sha mismatch", recorded, actual))
        continue
    p = json.load(open(payload, encoding="utf-8"))
    defs = {k: (v or {}).get("id") + " " + (v or {}).get("version", "") for k, v in (p.get("definitions") or {}).items()
            if k in ("psms", "peptides", "protein_groups")}
    files = {f["file"]: (f.get("metrics") or {}) for f in p.get("files") or []}
    bundle_runs = runs.get(ds, set())
    unmatched = sorted(set(files) - bundle_runs)
    unmatched_with_counts = [f for f in unmatched if any(files[f].get(k) is not None for k in ("psms", "peptides", "protein_groups"))]
    missing_runs = sorted(bundle_runs - set(files))
    have = {k: sum(1 for f, m in files.items() if f in bundle_runs and m.get(k) is not None) for k in ("psms", "peptides", "protein_groups")}
    psm_sum = sum(m.get("psms") or 0 for f, m in files.items() if f in bundle_runs)
    key = (p.get("schema"), defs.get("psms"))
    tally[key] += 1
    rows.append((ds, p.get("schema"), d.name, len(bundle_runs), len(files), have, f"unmatched={unmatched[:3]}{'...' if len(unmatched) > 3 else ''}",
                 f"unmatched_with_counts={len(unmatched_with_counts)}", f"runs_without_file={len(missing_runs)}",
                 f"psm_sum={psm_sum} results_txt={dataset_counts.get((ds, 'psms_1pct'))}"))

print(dict(tally))
for r in rows:
    print("\t".join(str(v) for v in r))
