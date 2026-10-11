"""D14 sandbox with views: allow the store, then switch external access off and lock. What can still be read?"""
import os, sys
import duckdb

STORE = r"F:\aging_data\repo\store"
cat = sys.argv[1]
c = duckdb.connect(cat, read_only=True)
c.execute(f"SET file_search_path = '{STORE}'")
for stmt in (f"SET allowed_directories = ['{STORE}{os.sep}']", "SET enable_external_access = false", "SET lock_configuration = true"):
    try:
        c.execute(stmt); print("ok   ", stmt)
    except Exception as e:
        print("FAIL ", stmt, "->", type(e).__name__, str(e)[:140])

def probe(label, sql):
    try:
        r = c.execute(sql).fetchone(); print(f"  READ    {label}: {r}")
    except Exception as e:
        print(f"  refused {label}: {type(e).__name__}: {str(e)[:110]}")

probe("a view over the store", "SELECT count(*) FROM samples")
probe("a file outside", "SELECT count(*) FROM read_csv_auto('C:/Windows/win.ini')")
probe("a store file by name", f"SELECT count(*) FROM read_parquet('{STORE}/PXD058082/3b292839ac60c3d2/runs.parquet')")
probe("traversal out of the store", f"SELECT count(*) FROM read_csv_auto('{STORE}/../catalog_build.log')")
probe("unlock attempt", "SET enable_external_access = true")
probe("attach another db", "ATTACH 'C:/x.duckdb' AS x")
