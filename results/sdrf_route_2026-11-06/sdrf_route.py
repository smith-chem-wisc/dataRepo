"""For every served deposit: which SDRF was read, what its factor columns hold, and what the search's own SDRF holds. Read-only."""
import collections
import csv
import json
import os
import re
import sys

import duckdb
import yaml

sys.stdout.reconfigure(encoding="utf-8")
out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
RESERVED = {"", "not available", "not applicable", "na", "n/a", "none", "not provided", "unknown"}

con = duckdb.connect("F:/aging_data/repo/catalogs/catalog-53f5ff162ba37e84.duckdb", read_only=True)
served = con.execute("SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY 1").fetchall()
stored_chars = collections.defaultdict(set)
for dataset, name in con.execute("SELECT DISTINCT dataset_id, name FROM sample_characteristics").fetchall():
    stored_chars[dataset].add(name.lower())
con.close()

with open("F:/aging_data/batch/manifest.yaml", encoding="utf-8") as handle:
    manifest = {e["accession"]: e for e in yaml.safe_load(handle)["datasets"]}


def read_sdrf(path):
    """{lower column: [cell, ...]}, keeping repeated columns apart. None when unreadable."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle, delimiter="\t"))
    except OSError:
        return None
    if not rows:
        return None
    header = [h.strip().lower() for h in rows[0]]
    columns = collections.defaultdict(list)
    for row in rows[1:]:
        for i, column in enumerate(header):
            columns[column].append(row[i].strip() if i < len(row) else "")
    return columns


def real(cells):
    return {c for c in cells if c.lower() not in RESERVED}


def inner(column):
    match = re.match(r"^[^\[]*\[(.*)\]$", column)
    return match.group(1) if match else column


rows = []
for dataset, bundle in served:
    entry = manifest.get(dataset, {})
    root = "F:/aging_data/" + str(entry.get("run", ""))
    with open(f"F:/aging_data/repo/store/{dataset}/{bundle}/bundle.json", encoding="utf-8") as handle:
        info = json.load(handle)
    note = info.get("sdrf") or (info.get("notes") or {}).get("sdrf") or {}
    read = note.get("read")
    source_row = next((s for s in info.get("sources", []) if s.get("role") == "sdrf"), None)
    path = (source_row or {}).get("path") or (source_row or {}).get("source_path")
    table = read_sdrf(path) if path else None

    factor_columns, lost, informative = [], [], []
    if table:
        characteristic_names = {inner(c) for c in table if c.startswith("characteristics[")}
        for column, cells in table.items():
            if column.startswith("factor value["):
                name = inner(column)
                factor_columns.append(name)
                if len(real(cells)) >= 2:
                    informative.append(name)
                    if name not in characteristic_names:
                        lost.append(name)

    search_dir = os.path.join(root, str(entry.get("search_results") or "04_search/mm/Task3SearchTask"))
    own_path = os.path.join(search_dir, "experiment.sdrf.tsv")
    own = read_sdrf(own_path)
    own_chars, own_factor_values = [], []
    if own:
        own_chars = sorted(inner(c) for c, cells in own.items() if c.startswith("characteristics[") and real(cells) and inner(c) != "organism")
        for c, cells in own.items():
            if c.startswith("factor value["):
                own_factor_values.extend(sorted(real(cells)))

    rows.append({
        "dataset_id": dataset,
        "chosen_by": note.get("chosen_by") or ("none" if not source_row else "unrecorded"),
        "factor_values": note.get("factor_values") or "",
        "operator_sdrf": bool(entry.get("operator_sdrf")),
        "factor_columns": ",".join(factor_columns),
        "informative_factors": ",".join(informative),
        "factors_with_no_characteristic": ",".join(lost),
        "stored_treatment_like": ",".join(sorted(n for n in stored_chars[dataset] if re.search("treatment|compound|drug", n))),
        "own_sdrf": own is not None,
        "own_real_characteristics": ",".join(own_chars),
        "own_factor_distinct": len(set(own_factor_values)),
    })

with open(os.path.join(out_dir, "sdrf_route_by_deposit.tsv"), "w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print("deposits:", len(rows))
print("by chosen_by, factor_values:", collections.Counter((r["chosen_by"], r["factor_values"]) for r in rows).most_common())
left_out = [r for r in rows if r["factor_values"] == "left out"]
print("left out:", len(left_out))
print("  with an informative factor column:", sum(1 for r in left_out if r["informative_factors"]))
print("  with an informative factor and no same-named characteristic:", sum(1 for r in left_out if r["factors_with_no_characteristic"]))
names = collections.Counter(n for r in left_out for n in r["factors_with_no_characteristic"].split(",") if n)
print("  those factor names:", names.most_common(25))
names_all = collections.Counter(n for r in left_out for n in r["informative_factors"].split(",") if n)
print("  informative factor names (all):", names_all.most_common(25))
kept = [r for r in rows if r["factor_values"] == "kept"]
print("kept:", len(kept), "with informative factor:", sum(1 for r in kept if r["informative_factors"]))
print("no SDRF read:", sum(1 for r in rows if r["chosen_by"] == "none"))
print("stored treatment-like characteristic:", sum(1 for r in rows if r["stored_treatment_like"]))
print("own SDRF present:", sum(1 for r in rows if r["own_sdrf"]))
present = [r for r in rows if r["own_sdrf"]]
print("  with a real characteristic beyond organism:", sum(1 for r in present if r["own_real_characteristics"]))
print("  characteristic names:", collections.Counter(n for r in present for n in r["own_real_characteristics"].split(",") if n).most_common(12))
print("  factor distinct values, 0/1/2+:", sum(1 for r in present if r["own_factor_distinct"] == 0), sum(1 for r in present if r["own_factor_distinct"] == 1), sum(1 for r in present if r["own_factor_distinct"] >= 2))
print("sample of left-out with factor-only:", [(r["dataset_id"], r["factors_with_no_characteristic"]) for r in left_out if r["factors_with_no_characteristic"]][:12])
print("bundle keys sample:", sorted(info.keys()))
print("source sample:", (source_row or info.get("sources", [{}])[0]))
