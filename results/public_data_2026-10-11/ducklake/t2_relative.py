"""Q2/Q5 prep: bundles placed UNDER DATA_PATH -> are paths stored relative? Build a lake to serve over HTTP."""
import duckdb, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
LAKE = HERE + "/www/lake2"
shutil.rmtree(HERE + "/www", ignore_errors=True)
os.makedirs(LAKE + "/data")
shutil.copytree(HERE + "/store", LAKE + "/data/store")  # store lives inside DATA_PATH
TABLES = ["protein_groups", "quant_values", "psms"]
BUNDLES = ["PXD035446/5c5f8f73a717d7c4", "PXD058775/ef86a0f83b59b75d"]

con = duckdb.connect()
con.execute("LOAD ducklake")
con.execute(f"ATTACH 'ducklake:{LAKE}/meta.ducklake' AS lake (DATA_PATH '{LAKE}/data/')")
for t in TABLES:
    con.execute(f"CREATE TABLE lake.{t} AS SELECT * FROM read_parquet('{LAKE}/data/store/{BUNDLES[0]}/{t}.parquet') LIMIT 0")
for i, b in enumerate(BUNDLES):
    con.execute("BEGIN")
    for t in TABLES:
        con.execute(f"CALL ducklake_add_data_files('lake', '{t}', '{LAKE}/data/store/{b}/{t}.parquet')")
    con.execute(f"CALL ducklake_set_commit_message('lake', 'dataRepo', 'release r{i+1}')")
    con.execute("COMMIT")
# try a relative path argument too
try:
    con.execute(f"CALL ducklake_add_data_files('lake', 'protein_groups', 'store/PXD012754/eff05a7486afcee0/protein_groups.parquet')")
    print("relative-path argument: accepted")
except Exception as e:
    print("relative-path argument:", type(e).__name__, str(e)[:200])

meta = "__ducklake_metadata_lake"
print(con.execute(f"SELECT schema_id, schema_name, path, path_is_relative FROM {meta}.ducklake_schema").fetchall())
print(con.execute(f"SELECT table_id, table_name, path, path_is_relative FROM {meta}.ducklake_table").fetchall())
for r in con.execute(f"SELECT data_file_id, table_id, begin_snapshot, path, path_is_relative FROM {meta}.ducklake_data_file ORDER BY 1").fetchall():
    print(r)
con.execute("DETACH lake")
con.close()
print("files in lake dir:", sorted(os.listdir(LAKE)))
