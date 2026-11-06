"""Read-only: in a search that trained PEP, how many target rows have a PEP q-value that was never computed for that row?
A blank or unparsable cell, NaN, or a value above 1 (a q-value cannot exceed 1; MetaMorpheus's unset value reads 2).
Does a per-row fallback to QValue Notch differ from the per-search one? Every served AllPeptides.psmtsv."""
import concurrent.futures
import csv
import os
import sys
import time

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter=chr(9)))

SQL = """
SELECT count(*) AS n_target,
  count(*) FILTER (WHERE pep_q <= 0.01 AND NOT isnan(pep_q)) AS n_pep,
  count(*) FILTER (WHERE pep_q IS NULL) AS n_unparsed,
  count(*) FILTER (WHERE isnan(pep_q)) AS n_nan,
  count(*) FILTER (WHERE pep_q > 1 AND NOT isnan(pep_q)) AS n_above_1,
  count(*) FILTER (WHERE pep_q = 2) AS n_exactly_2,
  count(*) FILTER (WHERE (pep_q IS NULL OR isnan(pep_q) OR pep_q > 1) AND notch <= 0.01) AS n_uncomputed_pass_notch,
  count(*) FILTER (WHERE (pep_q IS NULL OR isnan(pep_q) OR pep_q > 1) AND q <= 0.01 AND coalesce(notch <= 0.01, true)) AS n_uncomputed_pass_q,
  min(raw) FILTER (WHERE pep_q IS NULL) AS unparsed_example
FROM (
  SELECT try_cast("PEP_QValue" AS DOUBLE) AS pep_q, "PEP_QValue" AS raw,
         try_cast("QValue Notch" AS DOUBLE) AS notch, try_cast("QValue" AS DOUBLE) AS q
  FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                max_line_size=100000000, sample_size=2000)
  WHERE "Decoy/Contaminant/Target" IN ('T', 'ET')
)
"""
HEADER = ["dataset", "release", "pep_block", "ratio", "n_q", "n_new", "n_target", "n_pep", "n_unparsed", "n_nan", "n_above_1", "n_exactly_2",
          "n_uncomputed_pass_notch", "n_uncomputed_pass_q", "unparsed_example"]


def measure(r):
    con = duckdb.connect()
    con.execute("SET threads=12")
    try:
        return r, con.execute(SQL, [r["file"]]).fetchone()
    finally:
        con.close()


started = time.time()
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for index, (r, values) in enumerate(pool.map(measure, rows), 1):
        results.append([r["dataset"], r["release"], r["pep_block"], r["ratio"], r["n_q"], r["n_new"], *values])
        if index % 20 == 0:
            print(f"{index}/{len(rows)} {time.time() - started:.0f}s")

with open(os.path.join(here, "rule_uncomputed.tsv"), "w", encoding="utf-8", newline="\n") as out:
    out.write(chr(9).join(HEADER) + "\n")
    for row in results:
        out.write(chr(9).join("" if v is None else str(v) for v in row) + "\n")

trained = [dict(zip(HEADER, row)) for row in results if row[2] == "True"]
print(f"done {len(results)} deposits {time.time() - started:.0f}s; trained {len(trained)}")
for key in ("n_target", "n_pep", "n_unparsed", "n_nan", "n_above_1", "n_exactly_2", "n_uncomputed_pass_notch", "n_uncomputed_pass_q"):
    print(f"  {key}: {sum(t[key] for t in trained):,}")
print("deposits with any uncomputed target row:", sum(1 for t in trained if t["n_unparsed"] + t["n_nan"] + t["n_above_1"]))
print("deposits where an uncomputed row passes notch:", sum(1 for t in trained if t["n_uncomputed_pass_notch"]))
print("unparsed examples:", sorted({t["unparsed_example"] for t in trained if t["unparsed_example"] is not None})[:20])
print()
print("largest per-row additions (deposit ratio n_new n_above_1 pass_notch pass_q):")
for t in sorted(trained, key=lambda t: -t["n_uncomputed_pass_notch"])[:15]:
    print(f"  {t['dataset']} {t['ratio']} {int(t['n_new']):,} {t['n_above_1']:,} {t['n_uncomputed_pass_notch']:,} {t['n_uncomputed_pass_q']:,}")
print()
print("the deposits the PEP rule loses rows on (deposit ratio n_q n_new n_target n_above_1 pass_notch pass_q):")
for t in sorted((t for t in trained if t["ratio"] and float(t["ratio"]) < 1), key=lambda t: float(t["ratio"])):
    print(f"  {t['dataset']} {t['ratio']} {int(t['n_q']):,} {int(t['n_new']):,} {t['n_target']:,} {t['n_above_1']:,} {t['n_uncomputed_pass_notch']:,} {t['n_uncomputed_pass_q']:,}")
