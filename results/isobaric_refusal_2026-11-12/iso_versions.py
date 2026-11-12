import json, sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
root = "F:/aging_data/repo/catalogs/"
latest = json.load(open(root + "latest.json", encoding="utf-8"))
print({k: latest[k] for k in latest if k in ("catalog_id", "file", "catalog", "pointed_at", "built_by")})
f = latest.get("file") or latest.get("catalog")
con = duckdb.connect(root + f.split("/")[-1], read_only=True)
cols = [r[0] for r in con.execute("select column_name from information_schema.columns where table_name='datasets'").fetchall()]
lab = "labelling" if "labelling" in cols else [c for c in cols if "label" in c][0]
print(con.execute(f"select search_engine_version, count(*) from datasets where labelling in ('TMT','iTRAQ') group by 1 order by 1").fetchall())
