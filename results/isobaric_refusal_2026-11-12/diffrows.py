import sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
a = "F:/datarepo_scratch_150/store_item7b/PXD027232/3092c336f84cc096/"
b = "F:/datarepo_scratch_150/store_item9/PXD027232/b33d8bcbd9af59b4/"
con = duckdb.connect()
for t in ["psms", "peptidoforms", "quant_values", "ptm_sites", "peptidoform_ions"]:
    old = con.sql(f"SELECT * FROM '{a}{t}.parquet' EXCEPT ALL SELECT * FROM '{b}{t}.parquet'").fetchall()
    new = con.sql(f"SELECT * FROM '{b}{t}.parquet' EXCEPT ALL SELECT * FROM '{a}{t}.parquet'").fetchall()
    cols = [d[0] for d in con.sql(f"SELECT * FROM '{a}{t}.parquet' LIMIT 0").description]
    print("==", t, len(old), len(new))
    for o in old[:2]:
        # find the new row with the most equal columns
        best = max(new, key=lambda n: sum(x == y for x, y in zip(o, n)))
        print("   differs in:", [(c, x, y) for c, x, y in zip(cols, o, best) if x != y][:6])
