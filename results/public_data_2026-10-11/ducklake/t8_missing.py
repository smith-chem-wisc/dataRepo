import duckdb, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
S = HERE + "/store"; EV = HERE + "/evo2"
shutil.rmtree(EV, ignore_errors=True); os.makedirs(EV)
B1 = S + "/PXD035446/5c5f8f73a717d7c4"; B2 = S + "/PXD058775/ef86a0f83b59b75d"
con = duckdb.connect(); con.execute("LOAD ducklake")
con.execute(f"COPY (SELECT * EXCLUDE (score) FROM read_parquet('{B2}/psms.parquet')) TO '{EV}/psms_noscore.parquet' (FORMAT parquet)")
con.execute(f"ATTACH 'ducklake:{EV}/meta.ducklake' AS lake (DATA_PATH '{EV}/data/')")
con.execute(f"CREATE TABLE lake.psms AS SELECT * FROM read_parquet('{B1}/psms.parquet') LIMIT 0")
con.execute(f"CALL ducklake_add_data_files('lake', 'psms', '{B1}/psms.parquet')")
con.execute(f"CALL ducklake_add_data_files('lake', 'psms', '{EV}/psms_noscore.parquet', allow_missing => true)")
print("rows, non-null score:", con.execute("SELECT count(*), count(score) FROM lake.psms").fetchall())
con.execute("ALTER TABLE lake.psms ADD COLUMN bundle_id VARCHAR DEFAULT 'unknown'")
print("after ADD COLUMN ... DEFAULT:", con.execute("SELECT bundle_id, count(*) FROM lake.psms GROUP BY 1").fetchall())
