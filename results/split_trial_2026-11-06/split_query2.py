"""USI and site checks on the scratch split. Read-only."""
import glob
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
S = sys.argv[1]
path = glob.glob(S + "/store/PXD027754-rat/*/psms.parquet")[0].replace("\\", "/")
columns = [r[0] for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall()]
print("usi-like columns:", [c for c in columns if "usi" in c or "spectrum" in c])
print("usi prefixes:", duckdb.sql(
    f"SELECT split_part(usi, ':', 2) AS deposit, count(*) FROM read_parquet('{path}') WHERE usi IS NOT NULL GROUP BY 1").fetchall())
print("psm_id:", duckdb.sql(f"SELECT min(psm_id) FROM read_parquet('{path}')").fetchall())

page = open(S + "/site/datasets/PXD027754-rat.html", encoding="utf-8").read()
print("PRIDE links on the rat page:", sorted(set(re.findall(r"https://www\.ebi\.ac\.uk/pride/archive/projects/[^\"'<\s]*", page))))
print("siblings named on the page:", "PXD027754-mouse" in page)
index = open(S + "/site/index.html", encoding="utf-8").read()
print("headline:", re.findall(r"results for ([^,<]{0,60})", index)[:1])
print("index mentions of the deposit:", sorted(set(re.findall(r"PXD027754[-a-z]*", index))))
print("bare page exists:", bool(glob.glob(S + "/site/datasets/PXD027754.html")))
