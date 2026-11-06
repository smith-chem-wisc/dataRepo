"""For the five curated SDRFs whose factor column has no same-named characteristic: is the fact held by another column? Read-only."""
import csv
import glob
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
RESERVED = {"", "not available", "not applicable", "na", "n/a", "none", "not provided", "unknown"}
for dataset in ("PXD002467", "PXD006815", "PXD011740", "PXD022196", "PXD056433"):
    path = None
    for bundle in glob.glob(f"F:/aging_data/repo/store/{dataset}/*/bundle.json"):
        info = json.load(open(bundle, encoding="utf-8"))
        for source in info.get("sources", []):
            if source.get("role") == "sdrf":
                path = source.get("path")
    candidates = glob.glob(f"E:/CodeReview/aging/designs/{dataset}.sdrf.tsv")
    path = candidates[0] if candidates else path
    rows = list(csv.reader(open(path, encoding="utf-8-sig", newline=""), delimiter="\t"))
    header = [h.strip().lower() for h in rows[0]]
    print("==", dataset, path, "rows", len(rows) - 1)
    for i, column in enumerate(header):
        if not column.startswith(("characteristics[", "factor value[")):
            continue
        values = {r[i].strip() for r in rows[1:] if i < len(r)}
        real = sorted(v for v in values if v.lower() not in RESERVED)
        if len(real) >= 2 or column.startswith("factor"):
            print(f"  {column}: {len(real)} real values, e.g. {real[:6]}")
