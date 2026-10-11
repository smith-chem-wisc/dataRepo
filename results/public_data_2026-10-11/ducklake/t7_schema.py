"""Q6: schema evolution with registered files. Plus: absolute-URL data paths read from a LOCAL metadata file."""
import duckdb, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
S = HERE + "/store"
B1 = S + "/PXD035446/5c5f8f73a717d7c4"
B2 = S + "/PXD058775/ef86a0f83b59b75d"
B3 = S + "/PXD012754/eff05a7486afcee0"
EV = HERE + "/evo"
shutil.rmtree(EV, ignore_errors=True); os.makedirs(EV + "/lake")


def q(label, sql):
    try:
        r = con.execute(sql).fetchall()
        print(f"[OK]   {label}: {r}")
    except Exception as e:
        print(f"[FAIL] {label}: {' | '.join(str(e).splitlines())[:260]}")


con = duckdb.connect()
con.execute("LOAD ducklake")
# a 'next schema version' file: B3 psms + one new column
con.execute(f"COPY (SELECT *, 'v0.0.16' AS new_col FROM read_parquet('{B3}/psms.parquet')) TO '{EV}/psms_v16.parquet' (FORMAT parquet)")
# an 'old schema' file: B2 psms minus one column
con.execute(f"COPY (SELECT * EXCLUDE (matched_ion_count) FROM read_parquet('{B2}/psms.parquet')) TO '{EV}/psms_missing.parquet' (FORMAT parquet)")
con.execute(f"ATTACH 'ducklake:{EV}/lake/meta.ducklake' AS lake (DATA_PATH '{EV}/lake/data/')")
con.execute(f"CREATE TABLE lake.psms AS SELECT * FROM read_parquet('{B1}/psms.parquet') LIMIT 0")
q("register B1 (same schema)", f"CALL ducklake_add_data_files('lake', 'psms', '{B1}/psms.parquet')")
q("register file with EXTRA column, default", f"CALL ducklake_add_data_files('lake', 'psms', '{EV}/psms_v16.parquet')")
q("register file with MISSING column, default", f"CALL ducklake_add_data_files('lake', 'psms', '{EV}/psms_missing.parquet')")
q("register MISSING with allow_missing", f"CALL ducklake_add_data_files('lake', 'psms', '{EV}/psms_missing.parquet', allow_missing => true)")
q("MISSING column reads as", "SELECT count(*), count(matched_ion_count) FROM lake.psms")
q("ALTER TABLE ADD COLUMN new_col", "ALTER TABLE lake.psms ADD COLUMN new_col VARCHAR")
q("register EXTRA-column file after ALTER", f"CALL ducklake_add_data_files('lake', 'psms', '{EV}/psms_v16.parquet')")
q("new_col by file", "SELECT new_col, count(*) FROM lake.psms GROUP BY 1 ORDER BY 1")
q("snapshots", "SELECT snapshot_id, schema_version, changes::VARCHAR FROM ducklake_snapshots('lake')")
q("columns at version before ALTER", "SELECT count(*) FROM (DESCRIBE SELECT * FROM lake.psms AT (VERSION => 3))")
q("columns now", "SELECT count(*) FROM (DESCRIBE SELECT * FROM lake.psms)")
q("type mismatch: register protein_groups file into psms", f"CALL ducklake_add_data_files('lake', 'psms', '{B1}/protein_groups.parquet', allow_missing => true, ignore_extra_columns => true)")
con.close()

# absolute http URL paths, metadata LOCAL (server must be running)
con = duckdb.connect()
con.execute("LOAD httpfs; LOAD ducklake")
con.execute(f"ATTACH 'ducklake:{HERE}/www/lake3/meta.ducklake' AS l3 (READ_ONLY)")
q("lake3 (abs http URLs) local meta: real read", "SELECT count(*), max(psm_id) FROM l3.psms")
q("same file via read_parquet(url)", "SELECT count(*) FROM read_parquet('http://127.0.0.1:8765/lake2/data/store/PXD035446/5c5f8f73a717d7c4/psms.parquet')")
