"""Scratch measurement for our answer to PXR-R72 (3): how big is an accession index over target peptidoforms at 1%?

Opens aging's catalog READ-ONLY, writes the candidate index to a scratch Parquet file sorted by accession, and reports
rows, bytes and how long a one-accession lookup takes against the file. Writes nothing outside the scratch folder.
"""
import os
import sys
import time

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
catalog, out_dir = sys.argv[1], sys.argv[2]
out = os.path.join(out_dir, "accession_index.parquet")
con = duckdb.connect(catalog, read_only=True)
print("catalog_meta:", con.execute("SELECT catalog_id, layout FROM catalog_meta").fetchall())
t = time.time()
con.execute(f"""
COPY (
  SELECT unnest(protein_accessions) AS protein_accession, dataset_id, bundle_id, peptidoform_id, base_sequence, best_q_value
  FROM peptidoforms_1pct
  ORDER BY protein_accession, dataset_id
) TO '{out.replace(os.sep, '/')}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)
""")
print(f"build: {time.time() - t:.1f} s")
print("bytes:", os.path.getsize(out))
mem = duckdb.connect()
print("rows, accessions, (accession, dataset) pairs:",
      mem.execute(f"SELECT count(*), count(DISTINCT protein_accession), count(DISTINCT (protein_accession, dataset_id)) FROM '{out}'").fetchall())
for acc in ["P14136", "P03995", "P47819"]:
    t = time.time()
    n = mem.execute(f"SELECT count(*) FROM '{out}' WHERE protein_accession = ?", [acc]).fetchone()[0]
    print(f"lookup {acc}: {n} rows in {time.time() - t:.3f} s")
