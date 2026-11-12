"""Read-only: which served deposits lack per-run results.txt counts, by count, with run counts (item 7)."""
import json, sys
import duckdb
sys.stdout.reconfigure(encoding="utf-8")
root = "F:/aging_data/repo/catalogs/"
latest = json.load(open(root + "latest.json"))
con = duckdb.connect(root + latest["catalog"], read_only=True)
print("catalog", latest["catalog_id"], latest["builder_version"], latest["pointed_utc"])
rows = con.sql("""
WITH r AS (SELECT dataset_id, count(*) AS n_runs FROM runs GROUP BY 1),
m AS (
  SELECT split_part(scope_id, ':', 1) AS dataset_id, name, count(DISTINCT scope_id) AS n
  FROM metrics WHERE scope = 'run' AND source = 'results.txt' GROUP BY 1, 2),
q AS (SELECT split_part(scope_id, ':', 1) AS dataset_id, count(DISTINCT scope_id) AS n
  FROM metrics WHERE scope = 'run' AND source = 'qc_report.json' AND name = 'ms2' GROUP BY 1)
SELECT d.dataset_id, d.search_engine_version, r.n_runs,
  coalesce(max(m.n) FILTER (WHERE m.name = 'psms_1pct'), 0) AS psms,
  coalesce(max(m.n) FILTER (WHERE m.name = 'peptides'), 0) AS peptides,
  coalesce(max(m.n) FILTER (WHERE m.name = 'protein_groups'), 0) AS groups,
  coalesce(max(m.n) FILTER (WHERE m.name = 'precursors'), 0) AS precursors,
  coalesce(max(m.n) FILTER (WHERE m.name = 'ms2_scans'), 0) AS ms2_scans,
  coalesce(max(q.n), 0) AS qc_ms2
FROM datasets d JOIN r USING (dataset_id) LEFT JOIN m USING (dataset_id) LEFT JOIN q USING (dataset_id)
GROUP BY 1, 2, 3 ORDER BY 1
""").fetchall()
short = [x for x in rows if min(x[3:8]) < x[2]]
print(f"{len(rows)} deposits; {len(short)} short of a per-run count on some run")
print("dataset\tmm\truns\tpsms\tpeptides\tgroups\tprecursors\tms2_scans\tqc_ms2")
for x in short:
    print("\t".join(str(v) for v in x))
