"""Scratch: pick each included deposit's newest stored bundle as the baseline, and order the re-ingest largest first."""
import json, os, sys, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = r"F:\aging_data\repo\store"

manifest = yaml.safe_load(open(os.path.join(HERE, "manifest.snapshot.yaml"), encoding="utf-8"))
served = dict(line.rstrip("\n").split("\t") for line in open(os.path.join(HERE, "baseline.tsv"), encoding="utf-8"))

rows = []
for entry in manifest["datasets"]:
    if entry.get("status") != "include":
        continue
    acc = entry["accession"]
    folder = os.path.join(STORE, acc)
    newest = None
    for bid in os.listdir(folder) if os.path.isdir(folder) else []:
        path = os.path.join(folder, bid, "bundle.json")
        if not os.path.isfile(path):
            continue
        b = json.load(open(path, encoding="utf-8"))
        if newest is None or b["written_utc"] > newest["written_utc"]:
            newest = b
    size = sum(s.get("size_bytes", 0) for s in newest["sources"]) if newest else 0
    rows.append((acc, newest["bundle_id"] if newest else "-", newest["ingester"] if newest else "-",
                 newest["schema_version"] if newest else "-", served.get(acc, "-"), size))

rows.sort(key=lambda r: -r[5])
with open(os.path.join(HERE, "baseline_latest.tsv"), "w", newline="\n", encoding="utf-8") as f:
    f.write("accession\tlatest_bundle\tingester\tschema\tserved_bundle\tsource_bytes\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")
with open(os.path.join(HERE, "order.txt"), "w", newline="\n", encoding="utf-8") as f:
    f.write("".join(r[0] + "\n" for r in rows))
print(len(rows), "deposits;", sum(1 for r in rows if r[1] != r[4]), "differ from served;",
      sum(1 for r in rows if r[1] == "-"), "with no bundle;", f"{sum(r[5] for r in rows)/1e9:.1f} GB of sources")
from collections import Counter
print(Counter((r[2] if isinstance(r[2], str) else json.dumps(r[2]), r[3]) for r in rows))
