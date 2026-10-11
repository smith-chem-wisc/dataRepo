"""Q5 follow-up: DATA_PATH override at attach; relative data_path; time travel over URL paths."""
import duckdb, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
URL = "http://127.0.0.1:8765"


def run(con, label, sql):
    try:
        r = con.execute(sql).fetchall()
        print(f"[OK]   {label}: {r}")
        return r
    except Exception as e:
        print(f"[FAIL] {label}: {type(e).__name__}: {' | '.join(str(e).splitlines())[:400]}")


r = duckdb.connect()
r.execute("LOAD httpfs; LOAD ducklake")
run(r, "lake4 http + DATA_PATH + OVERRIDE_DATA_PATH true",
    f"ATTACH 'ducklake:{URL}/lake4/meta.ducklake' AS r4 (READ_ONLY, DATA_PATH '{URL}/lake2/data/', OVERRIDE_DATA_PATH true)")
run(r, "count r4.psms", "SELECT count(*) FROM r4.psms")
run(r, "count r4.quant_values", "SELECT count(*) FROM r4.quant_values")
run(r, "r4 time travel VERSION 4", "SELECT count(*) FROM r4.psms AT (VERSION => 4)")

# local file, local override (no http) to separate the two effects
run(r, "lake4 LOCAL meta + DATA_PATH override local",
    f"ATTACH 'ducklake:{HERE}/www/lake4/meta.ducklake' AS l4 (READ_ONLY, DATA_PATH '{HERE}/www/lake2/data/', OVERRIDE_DATA_PATH true)")
run(r, "count l4.psms", "SELECT count(*) FROM l4.psms")
run(r, "l4 time travel VERSION 4", "SELECT count(*) FROM l4.psms AT (VERSION => 4)")

# relative DATA_PATH at creation: is it stored relative?
os.chdir(HERE + "/www")
shutil.rmtree("lake5", ignore_errors=True); os.makedirs("lake5")
w = duckdb.connect()
w.execute("LOAD ducklake")
run(w, "create lake5 with relative DATA_PATH", "ATTACH 'ducklake:lake5/meta.ducklake' AS w5 (DATA_PATH 'lake5/data/')")
run(w, "lake5 stored data_path", "SELECT value FROM __ducklake_metadata_w5.ducklake_metadata WHERE key='data_path'")
w.execute("DETACH w5")
