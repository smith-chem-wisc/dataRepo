"""Read-only (item 7 side-check): per served deposit, MetaMorpheus release, quant method, protein_groups rows and
which group table the search folder holds."""
import json, sys, collections
from pathlib import Path
import duckdb, yaml
sys.stdout.reconfigure(encoding="utf-8")
root = "F:/aging_data/repo/catalogs/"
latest = json.load(open(root + "latest.json"))
con = duckdb.connect(root + latest["catalog"], read_only=True)
print("catalog", latest["catalog_id"])
rows = con.sql("""
SELECT d.dataset_id, d.search_engine_version, d.quant_method,
  (SELECT count(*) FROM protein_groups g WHERE g.dataset_id = d.dataset_id) AS groups,
  (SELECT max(value) FROM metrics m WHERE m.scope = 'dataset' AND m.scope_id = d.dataset_id AND m.name = 'protein_groups') AS results_txt
FROM datasets d ORDER BY 1""").fetchall()
manifest = yaml.safe_load(open("F:/aging_data/batch/manifest.yaml", encoding="utf-8"))
run_of = {e["accession"]: e.get("run") for e in manifest["datasets"]}
tally = collections.Counter()
for ds, mm, qm, groups, rt in rows:
    run = run_of.get(ds)
    tables = sorted({p.name for p in (Path("F:/aging_data") / run / "04_search").rglob("All*ProteinGroups.tsv")
                     if ".superseded" not in str(p) and "Individual" not in str(p)}) if run else []
    key = (mm, qm, groups == 0, ",".join(tables))
    tally[key] += 1
    if groups == 0:
        print(ds, mm, qm, groups, rt, tables, sep="\t")
print()
for k, v in sorted(tally.items(), key=lambda kv: str(kv[0])):
    print(v, k, sep="\t")
