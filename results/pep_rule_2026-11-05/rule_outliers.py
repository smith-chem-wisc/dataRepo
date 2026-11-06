"""Scratch, read-only: the deposits where the 1% PEP q-value rule loses most of the q-value rule's rows, and why."""
import csv
import os
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter=chr(9)))
usable = [r for r in rows if r["ratio"]]
for r in usable:
    r["ratio"] = float(r["ratio"])
    for key in ("n_rows", "n_q", "n_new", "n_both", "new_only", "q_only"):
        r[key] = int(r[key])

edges = [(0, 0.5), (0.5, 0.9), (0.9, 1.0), (1.0, 1.1), (1.1, 1.25), (1.25, 1.5), (1.5, 2), (2, 3), (3, 99)]
print("ratio bucket: deposits (q-rule rows, new-rule rows)")
for low, high in edges:
    group = [r for r in usable if low <= r["ratio"] < high]
    print(f"  {low}-{high}: {len(group)} ({sum(r['n_q'] for r in group):,} -> {sum(r['n_new'] for r in group):,})")
print("zero q-rule rows:", [r["dataset"] for r in rows if not r["ratio"]])

print()
print("LOSERS: ratio below 0.9")
con = duckdb.connect()
con.execute("SET threads=32")
PROBE = """
SELECT count(*) FILTER (WHERE t) AS targets,
       count(*) FILTER (WHERE d) AS decoys,
       min(pq) FILTER (WHERE t) AS min_pep_q,
       quantile_cont(pq, 0.5) FILTER (WHERE t AND q) AS med_pep_q_in_q_rule,
       count(*) FILTER (WHERE t AND pq = 2) AS targets_pep_q_2,
       count(*) FILTER (WHERE t AND q AND pq = 2) AS q_rule_pep_q_2,
       count(DISTINCT pep) AS distinct_pep,
       count(*) FILTER (WHERE t AND coalesce(pq <= 0.05, false)) AS pep_q_5pct
FROM (SELECT "Decoy/Contaminant/Target" IN ('T','ET') AS t, "Decoy/Contaminant/Target" = 'D' AS d,
             try_cast("QValue" AS DOUBLE) <= 0.01 AND coalesce(try_cast("QValue Notch" AS DOUBLE) <= 0.01, true) AS q,
             try_cast("PEP_QValue" AS DOUBLE) AS pq, "PEP" AS pep
      FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                    max_line_size=100000000, sample_size=2000))
"""
losers = sorted((r for r in usable if r["ratio"] < 0.9), key=lambda r: r["ratio"])
for r in losers:
    t, d, mn, med, t2, q2, dp, p5 = con.execute(PROBE, [r["file"]]).fetchone()
    results = os.path.join(os.path.dirname(r["file"]), "results.txt")
    if not os.path.exists(results):
        results = os.path.join(os.path.dirname(os.path.dirname(r["file"])), "results.txt")
    with open(results, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    iterative = re.findall(r"[^\n]*[Ii]terative[^\n]*", text)
    auc = re.findall(r"[^\n]*AUC[^\n]*", text)
    print(
        f"{r['dataset']} {r['release']} ratio={r['ratio']} q={r['n_q']:,} new={r['n_new']:,} both={r['n_both']:,} | "
        f"targets={t:,} decoys={d:,} minPEPq={mn} medPEPq(in q rule)={med} targets@2={t2:,} qrule@2={q2:,} "
        f"distinctPEP={dp:,} at5pct={p5:,}"
    )
    for line in (iterative[:1] + auc[:1]):
        print("    ", line.strip()[:170])

print()
print("GAINERS: ratio at or above 2, top 8")
for r in sorted(usable, key=lambda r: -r["ratio"])[:8]:
    print(f"{r['dataset']} {r['release']} ratio={r['ratio']} q={r['n_q']:,} new={r['n_new']:,} q_only={r['q_only']:,}")
print("deposits below 0.9:", len(losers), " at or above 1.5:", sum(1 for r in usable if r["ratio"] >= 1.5))
print("q-rule rows lost in total:", f"{sum(r['q_only'] for r in usable):,}", " rows gained:", f"{sum(r['new_only'] for r in usable):,}")
