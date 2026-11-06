"""Read-only: PXD020462 is the one deposit where most target rows read a PEP q-value above 1. What do they read?"""
import csv
import os
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    row = next(r for r in csv.DictReader(handle, delimiter=chr(9)) if r["dataset"] == "PXD020462")
print(row["dataset"], row["release"], row["file"])
TABLE = """read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                     max_line_size=100000000, sample_size=2000)"""
con = duckdb.connect()
print("Most common PEP_QValue cells, by target or decoy:")
for values in con.execute(
    f"""SELECT "Decoy/Contaminant/Target" AS kind, "PEP_QValue", count(*) AS n FROM {TABLE} GROUP BY 1, 2 ORDER BY n DESC LIMIT 12""",
    [row["file"]],
).fetchall():
    print(" ", values)
print("Target PEP_QValue range, rows above 1:")
print(" ", con.execute(
    f"""SELECT min(p), max(p), count(DISTINCT p), count(*) FROM (SELECT try_cast("PEP_QValue" AS DOUBLE) AS p FROM {TABLE}
        WHERE "Decoy/Contaminant/Target" IN ('T', 'ET')) WHERE p > 1""",
    [row["file"]],
).fetchone())
print("Target PEP among rows with PEP_QValue above 1, and at or below 1:")
print(" ", con.execute(
    f"""SELECT p > 1 AS above_1, count(*), count(DISTINCT pep), min(try_cast(pep AS DOUBLE)), max(try_cast(pep AS DOUBLE))
        FROM (SELECT try_cast("PEP_QValue" AS DOUBLE) AS p, "PEP" AS pep FROM {TABLE} WHERE "Decoy/Contaminant/Target" IN ('T', 'ET'))
        GROUP BY 1 ORDER BY 1""",
    [row["file"]],
).fetchall())
folder = os.path.dirname(row["file"])
results = os.path.join(folder, "results.txt")
if not os.path.exists(results):
    results = os.path.join(os.path.dirname(folder), "results.txt")
with open(results, encoding="utf-8", errors="replace") as handle:
    text = handle.read()
at = text.find("Metrics for Determination of PEP")
print("results.txt PEP block:")
print(text[at: at + 1400])
print("results.txt count lines:")
for line in text.splitlines():
    if re.match(r"All target .* with", line):
        print(" ", line)
