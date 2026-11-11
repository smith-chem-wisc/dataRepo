"""Scratch, read-only (1.5.0 build list item 2): for every deposit aging's serving catalog holds, count AllPeptides.psmtsv
target rows whose PEP_QValue, or QValue Notch, is EXACTLY 0.01. Those are the only rows on which `<= 0.01` (the catalog's
views) and `< 0.01` (mzLib's QuantifiedPsmRule.PassesConfidence) disagree. Also counts each rule's rows at `<=` and `<`."""
import glob
import json
import os
import sys
import time

import duckdb
import yaml

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TAB = chr(9)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "at_threshold.tsv")
ROOT = "F:/aging_data"


def load_manifest():
    for _ in range(5):
        try:
            with open(f"{ROOT}/batch/manifest.yaml", encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except yaml.YAMLError:
            time.sleep(10)
    raise SystemExit("manifest would not parse")


with open(f"{ROOT}/repo/catalogs/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
catalog = os.path.join(f"{ROOT}/repo/catalogs", latest["catalog"])
print("catalog", latest["catalog_id"], latest["builder_version"])
cat = duckdb.connect(catalog, read_only=True)
served = sorted(r[0] for r in cat.execute("SELECT dataset_id FROM dataset_overview").fetchall())
cat.close()
entries = {e["accession"]: e for e in load_manifest()["datasets"]}

con = duckdb.connect()
con.execute("SET threads=32")
SQL = """
SELECT
  count(*) FILTER (WHERE pq = 0.01)  AS pep_eq,
  count(*) FILTER (WHERE pq <= 0.01) AS pep_le,
  count(*) FILTER (WHERE pq < 0.01)  AS pep_lt,
  count(*) FILTER (WHERE nq = 0.01)  AS notch_eq,
  count(*) FILTER (WHERE nq <= 0.01) AS notch_le,
  count(*) FILTER (WHERE nq < 0.01)  AS notch_lt,
  count(*) FILTER (WHERE q = 0.01)   AS q_eq
FROM (
  SELECT try_cast("PEP_QValue" AS DOUBLE) AS pq, try_cast("QValue Notch" AS DOUBLE) AS nq, try_cast("QValue" AS DOUBLE) AS q
  FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                max_line_size=100000000, sample_size=2000)
  WHERE "Decoy/Contaminant/Target" IN ('T', 'ET')
)
"""
HEADER = ["dataset", "pep_eq", "pep_le", "pep_lt", "notch_eq", "notch_le", "notch_lt", "q_eq", "file"]
totals = [0] * 7
failed = []
started = time.time()
with open(OUT, "w", encoding="utf-8", newline="\n") as out:
    out.write(TAB.join(HEADER) + "\n")
    for index, accession in enumerate(served, 1):
        entry = entries.get(accession)
        if entry is None:
            failed.append((accession, "not in manifest"))
            continue
        run = os.path.join(ROOT, entry["run"])
        folder = os.path.join(run, entry["search_results"]) if entry.get("search_results") else None
        candidates = [c for c in ([os.path.join(folder, "AllPeptides.psmtsv")] if folder else []) if os.path.exists(c)]
        if not candidates:
            candidates = sorted(glob.glob(os.path.join(run, "04_search*", "**", "AllPeptides.psmtsv"), recursive=True))
        if not candidates:
            failed.append((accession, f"no AllPeptides under {run}"))
            continue
        try:
            counts = con.execute(SQL, [candidates[-1]]).fetchone()
        except duckdb.Error as error:
            failed.append((accession, str(error)[:200]))
            continue
        totals = [a + b for a, b in zip(totals, counts)]
        out.write(TAB.join([accession, *(str(c) for c in counts), candidates[-1]]) + "\n")
        if index % 25 == 0:
            print(f"{index}/{len(served)} {time.time() - started:.0f}s")

print(f"done {len(served) - len(failed)} of {len(served)}, {time.time() - started:.0f}s")
print("totals", dict(zip(HEADER[1:8], totals)))
for accession, why in failed:
    print("FAILED", accession, why)
