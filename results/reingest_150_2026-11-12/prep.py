"""Scratch (1.5.0 whole-store re-ingest): the baseline is each deposit's bundle in aging's SERVING catalog (named by id, read
read-only), not the newest in the store. Order the re-ingest largest first. Reads F:\\aging_data only."""
import json, os, sys
import duckdb, yaml

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = r"F:\aging_data\repo\store"
CATALOGS = r"F:\aging_data\repo\catalogs"
CATALOG_ID = "75e1c0c82f8dc965"  # latest.json at the start (pointed 2026-11-12T22:29:30Z, built by 1.4.5)

latest = json.load(open(os.path.join(CATALOGS, "latest.json"), encoding="utf-8"))
if latest["catalog_id"] != CATALOG_ID:
    print("note: latest.json now names", latest["catalog_id"], "; the baseline stays", CATALOG_ID)

con = duckdb.connect(os.path.join(CATALOGS, f"catalog-{CATALOG_ID}.duckdb"), read_only=True)
cols = [r[0] for r in con.execute("DESCRIBE catalog_bundles").fetchall()]
served = {r[0]: r[1] for r in con.execute("SELECT dataset_id, bundle_id FROM catalog_bundles").fetchall()}
con.close()

manifest = yaml.safe_load(open(os.path.join(HERE, "manifest.snapshot.yaml"), encoding="utf-8"))
rows = []
for entry in manifest["datasets"]:
    if entry.get("status") != "include":
        continue
    acc = entry["accession"]
    bid = served.get(acc)
    b = None
    if bid:
        path = os.path.join(STORE, acc, bid, "bundle.json")
        if os.path.isfile(path):
            b = json.load(open(path, encoding="utf-8"))
    size = sum(s.get("size_bytes", 0) for s in b["sources"]) if b else 0
    rows.append((acc, bid or "-", b["schema_version"] if b else "-", entry.get("metamorpheus", "-"),
                 entry.get("quant_method", "-"), size))

not_in_manifest = sorted(set(served) - {r[0] for r in rows})
rows.sort(key=lambda r: -r[5])
with open(os.path.join(HERE, "baseline.tsv"), "w", newline="\n", encoding="utf-8") as f:
    f.write("accession\tserved_bundle\tschema\tmetamorpheus\tquant_method\tsource_bytes\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")
with open(os.path.join(HERE, "order.txt"), "w", newline="\n", encoding="utf-8") as f:
    f.write("".join(r[0] + "\n" for r in rows))
print("catalog_bundles columns:", cols)
print(len(served), "served in", CATALOG_ID, ";", len(rows), "include entries;",
      sum(1 for r in rows if r[1] == "-"), "include entries not served;",
      len(not_in_manifest), "served but not include:", not_in_manifest)
print(f"{sum(r[5] for r in rows)/1e9:.1f} GB of sources; largest:", [(r[0], round(r[5]/1e9, 1)) for r in rows[:6]])
