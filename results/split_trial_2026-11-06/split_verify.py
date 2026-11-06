"""Check two claims in the draft: equal row counts across keys, and the bare bundle's reconciliation verdict."""
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
S = sys.argv[1]
log = open(S + "/../split_run.log", encoding="utf-8-sig").read()
tables = {}
current = None
for line in log.splitlines():
    stripped = line.strip()
    if re.fullmatch(r"PXD\d+(-[a-z]+)?", stripped):
        current = stripped
    elif stripped.startswith("tables ") and current:
        tables[current] = stripped
for key in ("PXD027754-rat", "PXD027754-mouse"):
    print(key, "tables line equal to bare:", tables.get(key) == tables.get("PXD027754"))
print(tables.get("PXD027754"))

con = duckdb.connect(S + "/both.duckdb", read_only=True)
for row in con.execute(
    "SELECT dataset_id, check_name, observed, expected, status FROM catalog_reconciliation "
    "WHERE dataset_id LIKE 'PXD027754%' AND status <> 'agrees' ORDER BY 1"
).fetchall():
    print(row)
print(con.execute("SELECT dataset_id, status, count(*) FROM catalog_reconciliation GROUP BY 1, 2 ORDER BY 1, 2").fetchall())
con.close()

for key in ("PXD027754", "PXD027754-rat"):
    con = duckdb.connect(S + "/both.duckdb", read_only=True)
    print(key, con.execute(
        f"SELECT count(*), count(DISTINCT full_sequence) FROM peptidoforms WHERE dataset_id = '{key}'").fetchall())
    con.close()
