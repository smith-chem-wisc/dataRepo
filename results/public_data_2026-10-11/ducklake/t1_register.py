"""Q2 + Q4: register two bundles' files without copying; snapshots, commit messages, time travel."""
import duckdb, glob, hashlib, os, shutil, json

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
S = HERE + "/store"
LAKE = HERE + "/lake1"
shutil.rmtree(LAKE, ignore_errors=True)
os.makedirs(LAKE + "/data")
B1 = S + "/PXD035446/5c5f8f73a717d7c4"
B2 = S + "/PXD058775/ef86a0f83b59b75d"
TABLES = ["protein_groups", "quant_values", "psms"]

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def snapshot_store():
    out = {}
    for f in sorted(glob.glob(S + "/*/*/*.parquet")):
        st = os.stat(f)
        out[f.replace("\\", "/")] = (sha(f), st.st_size, st.st_mtime_ns)
    return out

before = snapshot_store()
con = duckdb.connect()
con.execute("LOAD ducklake")
con.execute(f"ATTACH 'ducklake:{LAKE}/meta.ducklake' AS lake (DATA_PATH '{LAKE}/data/')")
for t in TABLES:
    con.execute(f"CREATE TABLE lake.{t} AS SELECT * FROM read_parquet('{B1}/{t}.parquet') LIMIT 0")
print("data dir after CREATE:", os.listdir(LAKE + "/data"))

for b, tag in [(B1, "release r1: PXD035446/5c5f8f73a717d7c4"), (B2, "release r2: + PXD058775/ef86a0f83b59b75d")]:
    con.execute("BEGIN")
    for t in TABLES:
        con.execute(f"CALL ducklake_add_data_files('lake', '{t}', '{b}/{t}.parquet')")
    con.execute(f"CALL lake.set_commit_message('dataRepo', '{tag}')" if False else
                f"CALL ducklake_set_commit_message('lake', 'dataRepo', '{tag}')")
    con.execute("COMMIT")

print("\n-- row counts: lake vs parquet")
for t in TABLES:
    lake_n = con.execute(f"SELECT count(*) FROM lake.{t}").fetchone()[0]
    pq_n = con.execute(f"SELECT count(*) FROM read_parquet(['{B1}/{t}.parquet','{B2}/{t}.parquet'])").fetchone()[0]
    print(f"{t}: lake={lake_n} parquet={pq_n} equal={lake_n == pq_n}")
# content equality, not just counts
d = con.execute(f"""SELECT count(*) FROM (
  (SELECT * FROM lake.protein_groups EXCEPT ALL SELECT * FROM read_parquet(['{B1}/protein_groups.parquet','{B2}/protein_groups.parquet']))
  UNION ALL
  (SELECT * FROM read_parquet(['{B1}/protein_groups.parquet','{B2}/protein_groups.parquet']) EXCEPT ALL SELECT * FROM lake.protein_groups))""").fetchone()[0]
print("protein_groups symmetric difference rows:", d)

print("\n-- snapshots")
for r in con.execute("SELECT snapshot_id, snapshot_time::VARCHAR, schema_version, changes::VARCHAR, author, commit_message FROM ducklake_snapshots('lake')").fetchall():
    print(r)
print("\n-- time travel")
for v in [1, 2, 3, 4, 5]:
    try:
        n = con.execute(f"SELECT count(*) FROM lake.psms AT (VERSION => {v})").fetchone()[0]
        print(f"psms AT VERSION {v}: {n}")
    except Exception as e:
        print(f"VERSION {v}: {type(e).__name__}: {str(e)[:120]}")

print("\n-- metadata: ducklake_data_file")
meta = "__ducklake_metadata_lake"
print(con.execute(f"SELECT column_name FROM duckdb_columns() WHERE database_name='{meta}' AND table_name='ducklake_data_file'").fetchall())
for r in con.execute(f"SELECT data_file_id, table_id, begin_snapshot, end_snapshot, path, path_is_relative, record_count, file_size_bytes FROM {meta}.ducklake_data_file").fetchall():
    print(r)
print("-- ducklake_metadata (data_path)")
for r in con.execute(f"SELECT * FROM {meta}.ducklake_metadata").fetchall():
    print(r)
print("-- ducklake_snapshot_changes")
for r in con.execute(f"SELECT snapshot_id, changes_made, author, commit_message FROM {meta}.ducklake_snapshot_changes").fetchall():
    print(r)

print("\n-- data dir after registration:", os.listdir(LAKE + "/data"))
after = snapshot_store()
changed = [k for k in before if before[k] != after.get(k)]
added = [k for k in after if k not in before]
print("store files changed:", changed, "added:", added, "count:", len(after))
con.close()
