"""Q5: prove rows (not catalog record_count) come back over HTTP: fingerprint every row vs local parquet."""
import duckdb, os

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
URL = "http://127.0.0.1:8765"
S = HERE + "/store"
B = ["PXD035446/5c5f8f73a717d7c4", "PXD058775/ef86a0f83b59b75d"]
TABLES = ["protein_groups", "quant_values", "psms"]

r = duckdb.connect()
r.execute("LOAD httpfs; LOAD ducklake")
r.execute("SET enable_external_file_cache = false")
r.execute(f"ATTACH 'ducklake:{URL}/lake3/meta.ducklake' AS r3 (READ_ONLY)")
r.execute(f"ATTACH 'ducklake:{URL}/lake4/meta.ducklake' AS r4 (READ_ONLY, DATA_PATH '{URL}/lake2/data/', OVERRIDE_DATA_PATH true)")
FP = "SELECT count(*), sum(hash(t)) FROM {src} t"
for t in TABLES:
    local = r.execute(FP.format(src=f"read_parquet(['{S}/{B[0]}/{t}.parquet','{S}/{B[1]}/{t}.parquet'])")).fetchone()
    for cat in ["r3", "r4"]:
        try:
            got = r.execute(FP.format(src=f"{cat}.{t}")).fetchone()
            print(f"{t:15s} {cat}: rows={got[0]} fingerprint_equal={got == local}")
        except Exception as e:
            print(f"{t:15s} {cat}: FAIL {str(e).splitlines()[0][:160]}")
    v4 = r.execute(FP.format(src=f"(SELECT * FROM r4.{t} AT (VERSION => 4))")).fetchone()
    l1 = r.execute(FP.format(src=f"read_parquet('{S}/{B[0]}/{t}.parquet')")).fetchone()
    print(f"{t:15s} r4 AT VERSION 4 (release r1) equals bundle 1 alone: {v4 == l1} rows={v4[0]}")
