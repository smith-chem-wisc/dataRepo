"""Q5: static hosting. Metadata + data served by a read-only Range-capable HTTP server on 127.0.0.1:8765 (root = www/)."""
import duckdb, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
URL = "http://127.0.0.1:8765"
TABLES = ["protein_groups", "quant_values", "psms"]
BUNDLES = ["PXD035446/5c5f8f73a717d7c4", "PXD058775/ef86a0f83b59b75d"]


def run(con, label, sql):
    try:
        r = con.execute(sql).fetchall()
        print(f"[OK]   {label}: {r}")
        return r
    except Exception as e:
        print(f"[FAIL] {label}: {type(e).__name__}: {str(e).splitlines()[0][:220]}")


con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; LOAD ducklake")

# A. writer: lake3 whose data files are registered by absolute http URL (the hf:// analogue)
L3 = HERE + "/www/lake3"
shutil.rmtree(L3, ignore_errors=True); os.makedirs(L3)
con.execute(f"ATTACH 'ducklake:{L3}/meta.ducklake' AS w (DATA_PATH '{L3}/data/')")
for t in TABLES:
    con.execute(f"CREATE TABLE w.{t} AS SELECT * FROM read_parquet('{URL}/lake2/data/store/{BUNDLES[0]}/{t}.parquet') LIMIT 0")
for i, b in enumerate(BUNDLES):
    con.execute("BEGIN")
    for t in TABLES:
        con.execute(f"CALL ducklake_add_data_files('w', '{t}', '{URL}/lake2/data/store/{b}/{t}.parquet')")
    con.execute(f"CALL ducklake_set_commit_message('w', 'dataRepo', 'release r{i+1}')")
    con.execute("COMMIT")
print("lake3 stored paths:", con.execute("SELECT path, path_is_relative FROM __ducklake_metadata_w.ducklake_data_file LIMIT 2").fetchall())
con.execute("DETACH w")
print("lake3 dir:", os.listdir(L3))

# B. reader over HTTP
r = duckdb.connect()
r.execute("LOAD httpfs; LOAD ducklake")
run(r, "ATTACH lake3 over http, no READ_ONLY", f"ATTACH 'ducklake:{URL}/lake3/meta.ducklake' AS rw")
run(r, "ATTACH lake3 over http READ_ONLY", f"ATTACH 'ducklake:{URL}/lake3/meta.ducklake' AS r3 (READ_ONLY)")
for t in TABLES:
    run(r, f"count r3.{t}", f"SELECT count(*) FROM r3.{t}")
run(r, "time travel r3.psms AT VERSION 4", "SELECT count(*) FROM r3.psms AT (VERSION => 4)")
run(r, "snapshots over http", "SELECT snapshot_id, commit_message FROM ducklake_snapshots('r3')")
run(r, "write refused", "DELETE FROM r3.psms WHERE true")
run(r, "ATTACH pinned SNAPSHOT_VERSION 4", f"ATTACH 'ducklake:{URL}/lake3/meta.ducklake' AS r3v4 (READ_ONLY, SNAPSHOT_VERSION 4)")
run(r, "count r3v4.psms", "SELECT count(*) FROM r3v4.psms")

# C. lake2 (absolute local C:/ paths) metadata over HTTP
run(r, "ATTACH lake2 over http READ_ONLY", f"ATTACH 'ducklake:{URL}/lake2/meta.ducklake' AS r2 (READ_ONLY)")
run(r, "lake2 stored path", "SELECT path, path_is_relative FROM __ducklake_metadata_r2.ducklake_data_file LIMIT 1")
run(r, "lake2 stored data_path", "SELECT value FROM __ducklake_metadata_r2.ducklake_metadata WHERE key='data_path'")
run(r, "count r2.psms (paths resolve to local disk)", "SELECT count(*) FROM r2.psms")

# D. relative paths: copy lake2's metadata, rewrite paths to be relative (spec-level edit), serve, override DATA_PATH at attach
L4 = HERE + "/www/lake4"
shutil.rmtree(L4, ignore_errors=True); os.makedirs(L4)
shutil.copy(HERE + "/www/lake2/meta.ducklake", L4 + "/meta.ducklake")
e = duckdb.connect(L4 + "/meta.ducklake")
prefix = HERE + "/www/lake2/data/"
# a relative file path is relative to the TABLE path (data_path + main/ + <table>/)
e.execute(f"UPDATE ducklake_data_file SET path = '../../' || replace(path, '{prefix}', ''), path_is_relative = true WHERE path LIKE '{prefix}%'")
e.execute("DELETE FROM ducklake_data_file WHERE path_is_relative = false")  # drop the cwd-relative test row
e.execute("CHECKPOINT"); e.close()
run(r, "ATTACH lake4 http, DATA_PATH override -> http lake2/data/",
    f"ATTACH 'ducklake:{URL}/lake4/meta.ducklake' AS r4 (READ_ONLY, DATA_PATH '{URL}/lake2/data/')")
run(r, "lake4 stored path", "SELECT path, path_is_relative FROM __ducklake_metadata_r4.ducklake_data_file LIMIT 1")
for t in TABLES:
    run(r, f"count r4.{t}", f"SELECT count(*) FROM r4.{t}")
