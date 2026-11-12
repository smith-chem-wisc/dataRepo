"""Print the run_counts_missing finding (1.5.0 item 7) of every bundle in a scratch store."""
import sys
from pathlib import Path
import duckdb
sys.stdout.reconfigure(encoding="utf-8")
store = Path(sys.argv[1] if len(sys.argv) > 1 else "F:/datarepo_scratch_150/store_item7")
for f in sorted(store.glob("*/*/findings.parquet")):
    rows = duckdb.sql(f"SELECT severity, message FROM '{f.as_posix()}' WHERE code = 'run_counts_missing'").fetchall()
    print(f.parent.parent.name, f.parent.name, "no run_counts_missing" if not rows else rows[0][0])
    for _, message in rows:
        print("   ", message)
