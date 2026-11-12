"""Scratch, read-only (1.5.0, taking mzLib 1.0.598 into item 1): the same eight deposits ingested by feat/1.5.0's code
on mzLib 1.0.597 and on 1.0.598 (only the package version differs), into F:/datarepo_scratch_150/store_598a and
store_598b. Compares bundle ids and every Parquet table, row for row in both directions (EXCEPT ALL), and the copied
sources byte for byte. Item 1's script, pointed at these stores."""
import filecmp
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
ROOT = "F:/datarepo_scratch_150"
A, B = f"{ROOT}/store_598a", f"{ROOT}/store_598b"
con = duckdb.connect()
moved = 0
for dataset in sorted(os.listdir(A)):
    bundles_a = sorted(os.listdir(os.path.join(A, dataset)))
    bundles_b = sorted(os.listdir(os.path.join(B, dataset))) if os.path.isdir(os.path.join(B, dataset)) else []
    print(f"{dataset}: 597 {bundles_a}  598 {bundles_b}")
    if bundles_a != bundles_b or len(bundles_a) != 1:
        moved += 1
        continue
    a, b = os.path.join(A, dataset, bundles_a[0]), os.path.join(B, dataset, bundles_b[0])
    tables = sorted(f for f in os.listdir(a) if f.endswith(".parquet"))
    if tables != sorted(f for f in os.listdir(b) if f.endswith(".parquet")):
        print("  TABLE SETS DIFFER")
        moved += 1
    for table in tables:
        pa, pb = os.path.join(a, table), os.path.join(b, table)
        n = con.execute(f"SELECT count(*) FROM '{pa}'").fetchone()[0]
        only_a = con.execute(f"SELECT count(*) FROM (SELECT * FROM '{pa}' EXCEPT ALL SELECT * FROM '{pb}')").fetchone()[0]
        only_b = con.execute(f"SELECT count(*) FROM (SELECT * FROM '{pb}' EXCEPT ALL SELECT * FROM '{pa}')").fetchone()[0]
        same = "equal" if only_a == only_b == 0 else f"DIFFER: {only_a} rows only in 597, {only_b} only in 598"
        if only_a or only_b:
            moved += 1
        print(f"  {table:<40} {n:>12,}  {same}")
    for name in sorted(os.listdir(os.path.join(a, "sources"))):
        if not filecmp.cmp(os.path.join(a, "sources", name), os.path.join(b, "sources", name), shallow=False):
            print(f"  source {name} DIFFERS")
    ja = json.load(open(os.path.join(a, "bundle.json"), encoding="utf-8"))
    jb = json.load(open(os.path.join(b, "bundle.json"), encoding="utf-8"))
    for key in sorted(set(ja) | set(jb)):
        if key in ("written_utc",):
            continue
        if ja.get(key) != jb.get(key):
            print(f"  bundle.json {key} differs")
print("RESULT:", "no row moves" if moved == 0 else f"{moved} difference(s)")
