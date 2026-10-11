"""Which bundle tables carry dataset_id / bundle_id in their own Parquet? (one bundle, read-only)"""
import glob, os, sys
import duckdb
d = sys.argv[1]
con = duckdb.connect()
for p in sorted(glob.glob(os.path.join(d, "*.parquet"))):
    cols = [r[0] for r in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()]
    print(f"{os.path.basename(p):32s} dataset_id={'dataset_id' in cols!s:5s} bundle_id={'bundle_id' in cols!s:5s} {cols[:6]}")
