"""Q3: can DuckLake maintenance delete/rewrite registered (immutable) bundle files? Runs on scratch copies only."""
import duckdb, glob, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
MODE = sys.argv[1]  # 'explicit' | 'checkpoint' | 'noauto'
M = HERE + f"/m_{MODE[0]}"
shutil.rmtree(M, ignore_errors=True)
os.makedirs(M + "/lake/data")
shutil.copytree(HERE + "/store/PXD035446", M + "/lake/data/store/PXD035446", ignore=shutil.ignore_patterns("provenance_uniprot*"))   # bundle 1 UNDER data_path
shutil.copytree(HERE + "/store/PXD058775", M + "/outside/PXD058775", ignore=shutil.ignore_patterns("provenance_uniprot*"))           # bundle 2 OUTSIDE data_path
B1 = M + "/lake/data/store/PXD035446/5c5f8f73a717d7c4"
B2 = M + "/outside/PXD058775/ef86a0f83b59b75d"
TABLES = ["protein_groups", "psms"]


def files():
    return sorted(p.replace("\\", "/").replace(M + "/", "") for p in glob.glob(M + "/**/*", recursive=True) if os.path.isfile(p) and not p.endswith(".ducklake") and ".ducklake." not in p)


def q(label, sql):
    try:
        r = con.execute(sql).fetchall()
        print(f"[OK] {label}: {r if len(str(r)) < 900 else str(r)[:900] + '...'}")
    except Exception as e:
        print(f"[FAIL] {label}: {' | '.join(str(e).splitlines())[:300]}")


con = duckdb.connect()
con.execute("LOAD ducklake")
con.execute(f"ATTACH 'ducklake:{M}/lake/meta.ducklake' AS lake (DATA_PATH '{M}/lake/data/')")
if MODE == "noauto":
    con.execute("CALL lake.set_option('auto_compact', false)")
for t in TABLES:
    con.execute(f"CREATE TABLE lake.{t} AS SELECT * FROM read_parquet('{B1}/{t}.parquet') LIMIT 0")
for b in (B1, B2):
    con.execute("BEGIN")
    for t in TABLES:
        con.execute(f"CALL ducklake_add_data_files('lake', '{t}', '{b}/{t}.parquet')")
    con.execute("COMMIT")
before = files()
print("files before:", len(before))

q("orphans dry_run", "SELECT path FROM ducklake_delete_orphaned_files('lake', cleanup_all => true, dry_run => true)")
if MODE in ("explicit", "noauto"):
    q("merge_adjacent_files", "CALL ducklake_merge_adjacent_files('lake')")
    q("data files now", "SELECT data_file_id, table_id, begin_snapshot, end_snapshot, regexp_replace(path, '.*/(lake|outside)/', '') FROM __ducklake_metadata_lake.ducklake_data_file ORDER BY 1")
    q("expire_snapshots", "CALL ducklake_expire_snapshots('lake', older_than => now())")
    q("scheduled for deletion", "SELECT regexp_replace(path, '.*/(lake|outside)/', '') FROM __ducklake_metadata_lake.ducklake_files_scheduled_for_deletion")
    q("cleanup_old_files", "CALL ducklake_cleanup_old_files('lake', cleanup_all => true)")
    q("delete_orphaned_files", "CALL ducklake_delete_orphaned_files('lake', cleanup_all => true)")
elif MODE == "default1":
    q("snapshots before", "SELECT list(snapshot_id) FROM ducklake_snapshots('lake')")
    q("CHECKPOINT (defaults, once)", "CHECKPOINT lake")
    q("snapshots after", "SELECT list(snapshot_id) FROM ducklake_snapshots('lake')")
    q("data files now", "SELECT data_file_id, begin_snapshot, end_snapshot, regexp_replace(path, '.*/(lake|outside)/', '') FROM __ducklake_metadata_lake.ducklake_data_file ORDER BY 1")
    q("scheduled for deletion", "SELECT regexp_replace(path, '.*/(lake|outside)/', '') FROM __ducklake_metadata_lake.ducklake_files_scheduled_for_deletion")
else:
    q("CHECKPOINT (defaults)", "CHECKPOINT lake")
    q("data files now", "SELECT data_file_id, table_id, begin_snapshot, end_snapshot, regexp_replace(path, '.*/(lake|outside)/', '') FROM __ducklake_metadata_lake.ducklake_data_file ORDER BY 1")
    q("set expire/delete older_than 0 and CHECKPOINT again", "CALL lake.set_option('expire_older_than', '1 millisecond')")
    con.execute("CALL lake.set_option('delete_older_than', '1 millisecond')")
    import time; time.sleep(0.5)
    q("CHECKPOINT", "CHECKPOINT lake")
after = files()
print("DELETED:", [f for f in before if f not in after])
print("NEW:", [f for f in after if f not in before])
q("psms rows still", "SELECT count(*) FROM lake.psms")
