import duckdb, glob, os
S = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/store"
con = duckdb.connect()
b = S + "/PXD035446/5c5f8f73a717d7c4"
for t in ["psms", "protein_groups", "quant_values"]:
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{b}/{t}.parquet')").fetchall()
    print(t, len(cols), [(c[0], c[1]) for c in cols][:40])
# do schemas match across the three bundles?
for t in ["psms", "protein_groups", "quant_values", "samples", "ptm_sites"]:
    sigs = set()
    for f in glob.glob(S + f"/*/*/{t}.parquet"):
        f = f.replace("\\", "/")
        sigs.add(tuple(con.execute(f"DESCRIBE SELECT * FROM read_parquet('{f}')").fetchall()))
    print(t, "distinct schemas across bundles:", len(sigs))
