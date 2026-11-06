"""What a reader sees of a split deposit in the scratch catalog. Read-only. The second half is a stand-in."""
import glob
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
S = sys.argv[1]
con = duckdb.connect(S + "/after.duckdb", read_only=True)


def show(title, sql):
    print("==", title)
    rows = con.execute(sql)
    print("  ", [c[0] for c in rows.description])
    for row in rows.fetchall():
        print("  ", row)


show("datasets", "SELECT dataset_id, search_engine_version FROM datasets ORDER BY 1")
show("overview columns naming a deposit or group",
     "SELECT column_name FROM information_schema.columns WHERE table_name='dataset_overview' AND (column_name LIKE '%accession%' OR column_name LIKE '%split%' OR column_name LIKE '%deposit%' OR column_name LIKE '%group%')")
show("run ids", "SELECT dataset_id, min(run_id) AS a_run_id, count(*) AS runs, count(DISTINCT sha256) AS distinct_sha256 FROM runs GROUP BY 1 ORDER BY 1")
show("id prefixes in peptidoforms", "SELECT dataset_id, min(peptidoform_id) FROM peptidoforms GROUP BY 1 ORDER BY 1")
show("one bundle per key, reconciliation verdicts",
     "SELECT dataset_id, status, count(*) FROM catalog_reconciliation GROUP BY 1, 2 ORDER BY 1, 2")
show("protein_index: an accession in both halves counts twice",
     """SELECT n_datasets_1pct, count(*) AS proteins FROM protein_index GROUP BY 1 ORDER BY 1""")
show("example", """SELECT protein_accession, n_datasets, n_datasets_1pct, dataset_ids_1pct FROM protein_index
                   WHERE list_contains(dataset_ids_1pct, 'PXD027754-rat') AND list_contains(dataset_ids_1pct, 'PXD027754-mouse')
                     AND NOT list_contains(dataset_ids_1pct, 'PXD017944') LIMIT 1""")
show("peptide_index n_datasets", "SELECT n_datasets, count(*) FROM peptide_index GROUP BY 1 ORDER BY 1")
show("tables with a dataset_id column", """SELECT count(DISTINCT table_name) FROM information_schema.columns WHERE column_name='dataset_id'""")

con.close()
files = glob.glob(S + "/store/PXD027754-rat/*/psms*.parquet") + glob.glob(S + "/store/PXD027754-rat/*/*/psms*.parquet")
print("== psms file:", files[:1])
if files:
    print(duckdb.sql(f"SELECT dataset_id, usi FROM read_parquet('{files[0]}') WHERE usi IS NOT NULL LIMIT 1").fetchall())

print("== site")
page = open(S + "/site/datasets/PXD027754-rat.html", encoding="utf-8").read()
print("  PRIDE links:", sorted(set(re.findall(r"https://www\.ebi\.ac\.uk/pride/archive/projects/[^\"'<\s]*", page))))
index = open(S + "/site/index.html", encoding="utf-8").read()
print("  headline:", re.findall(r"class=\"lede\">(.{0,110})", index)[:1])
print("  rows naming the deposit in index:", len(re.findall(r"PXD027754", index)))
