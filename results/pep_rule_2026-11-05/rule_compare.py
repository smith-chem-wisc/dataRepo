"""Scratch, read-only: for every deposit the serving catalog holds, count AllPeptides.psmtsv target rows under the view's
q-value rule and under the 1% PEP q-value rule (notch fallback for a search with no PEP block)."""
import glob
import json
import os
import statistics
import sys
import time

import duckdb
import yaml

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
TAB = chr(9)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rule_compare.tsv")
ROOT = "F:/aging_data"


def load_manifest():
    for attempt in range(5):
        try:
            with open(f"{ROOT}/batch/manifest.yaml", encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except yaml.YAMLError:
            time.sleep(10)
    raise SystemExit("manifest would not parse")


def serving_catalog():
    with open(f"{ROOT}/repo/catalogs/latest.json", encoding="utf-8") as handle:
        latest = json.load(handle)
    for value in latest.values():
        if isinstance(value, str) and value.endswith(".duckdb"):
            return os.path.join(f"{ROOT}/repo/catalogs", os.path.basename(value)), latest
    raise SystemExit(f"no catalog named in latest.json: {latest}")


path, latest = serving_catalog()
print("catalog", path)
cat = duckdb.connect(path, read_only=True)
served = {
    r[0]: (r[1], r[2])
    for r in cat.execute(
        "SELECT o.dataset_id, d.search_engine_version, o.n_peptidoforms_1pct "
        "FROM dataset_overview o JOIN datasets d USING (dataset_id)"
    ).fetchall()
}
cat.close()
print("served", len(served))
entries = {e["accession"]: e for e in load_manifest()["datasets"]}

con = duckdb.connect()
con.execute("SET threads=32")
SQL = """
SELECT count(*) AS n_rows,
  count(*) FILTER (WHERE target AND q AND notch_ok) AS n_q,
  count(*) FILTER (WHERE target AND pep_q)          AS n_pep,
  count(*) FILTER (WHERE target AND notch_only)     AS n_notch,
  count(*) FILTER (WHERE target AND q AND notch_ok AND pep_q)      AS n_both_pep,
  count(*) FILTER (WHERE target AND q AND notch_ok AND notch_only) AS n_both_notch,
  count(DISTINCT pep_cell) AS n_distinct_pep
FROM (
  SELECT "Decoy/Contaminant/Target" IN ('T', 'ET') AS target,
         try_cast("QValue" AS DOUBLE) <= 0.01 AS q,
         coalesce(try_cast("QValue Notch" AS DOUBLE) <= 0.01, true) AS notch_ok,
         coalesce(try_cast("QValue Notch" AS DOUBLE) <= 0.01, false) AS notch_only,
         coalesce(try_cast("PEP_QValue" AS DOUBLE) <= 0.01, false) AS pep_q,
         "PEP" AS pep_cell
  FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                max_line_size=100000000, sample_size=2000)
)
"""
HEADER = ["dataset", "release", "catalog_n_1pct", "pep_block", "n_rows", "n_q", "n_new", "n_both", "new_only", "q_only",
          "ratio", "n_distinct_pep", "file"]
rows, failed = [], []
started = time.time()
with open(OUT, "w", encoding="utf-8", newline="\n") as out:
    out.write(TAB.join(HEADER) + "\n")
    for index, (accession, (release, n_catalog)) in enumerate(sorted(served.items()), 1):
        entry = entries.get(accession)
        if entry is None:
            failed.append((accession, "not in manifest"))
            continue
        run = os.path.join(ROOT, entry["run"])
        folder = os.path.join(run, entry["search_results"]) if entry.get("search_results") else None
        candidates = [os.path.join(folder, "AllPeptides.psmtsv")] if folder else []
        candidates = [c for c in candidates if os.path.exists(c)]
        if not candidates:
            candidates = sorted(glob.glob(os.path.join(run, "04_search*", "**", "AllPeptides.psmtsv"), recursive=True))
        if not candidates:
            failed.append((accession, f"no AllPeptides under {run}"))
            continue
        peptides = candidates[-1]
        results = os.path.join(os.path.dirname(peptides), "results.txt")
        if not os.path.exists(results):
            results = os.path.join(os.path.dirname(os.path.dirname(peptides)), "results.txt")
        if not os.path.exists(results):
            failed.append((accession, f"no results.txt beside {peptides}"))
            continue
        with open(results, encoding="utf-8", errors="replace") as handle:
            pep_block = "Metrics for Determination of PEP" in handle.read()
        try:
            n_rows, n_q, n_pep, n_notch, both_pep, both_notch, n_distinct = con.execute(SQL, [peptides]).fetchone()
        except duckdb.Error as error:
            failed.append((accession, str(error)[:200]))
            continue
        n_new, both = (n_pep, both_pep) if pep_block else (n_notch, both_notch)
        row = [accession, release, n_catalog, pep_block, n_rows, n_q, n_new, both, n_new - both, n_q - both,
               round(n_new / n_q, 4) if n_q else "", n_distinct, peptides]
        rows.append(row)
        out.write(TAB.join(str(v) for v in row) + "\n")
        out.flush()
        if index % 20 == 0:
            print(f"{index}/{len(served)} {time.time() - started:.0f}s")

print(f"done {len(rows)} deposits, {len(failed)} failed, {time.time() - started:.0f}s")
for accession, why in failed:
    print("FAILED", accession, why)


def summary(label, group):
    usable = [r for r in group if r[5]]
    if not usable:
        return
    ratios = sorted(r[10] for r in usable)
    q_only = sorted(100 * r[9] / r[5] for r in usable)
    print(
        f"{label}: n={len(usable)} q_total={sum(r[5] for r in usable):,} new_total={sum(r[6] for r in usable):,} "
        f"ratio min={ratios[0]} median={statistics.median(ratios)} max={ratios[-1]} "
        f"q_only% median={statistics.median(q_only):.1f} max={q_only[-1]:.1f}"
    )


summary("all", rows)
for release in sorted({r[1] for r in rows}):
    summary(release, [r for r in rows if r[1] == release])
print("catalog count vs file q-rule, largest gaps:")
for r in sorted(rows, key=lambda r: -abs(r[2] - r[5]))[:5]:
    print(" ", r[0], r[2], r[5])
print("no PEP block:", [r[0] for r in rows if not r[3]])
print("one distinct PEP cell:", [r[0] for r in rows if r[11] <= 1])
print("smallest ratios:", [(r[0], r[10]) for r in sorted((r for r in rows if r[5]), key=lambda r: r[10])[:5]])
print("largest ratios:", [(r[0], r[10]) for r in sorted((r for r in rows if r[5]), key=lambda r: -r[10])[:5]])
