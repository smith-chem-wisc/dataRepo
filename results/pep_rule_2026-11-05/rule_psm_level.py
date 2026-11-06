"""Read-only: on the deposits the 1% PEP q-value rule hollows out at peptide level, does the PSM level fail the same way?
Reads each served bundle's psms.parquet. Compares with a sample of deposits that gain rows."""
import csv
import glob
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = [r for r in csv.DictReader(handle, delimiter=chr(9)) if r["ratio"]]
for r in rows:
    r["ratio"] = float(r["ratio"])

cat = duckdb.connect("F:/aging_data/repo/catalogs/catalog-d621ea41cd649681.duckdb", read_only=True)
bundles = dict(cat.execute("SELECT DISTINCT dataset_id, bundle_id FROM datasets").fetchall())
cat.close()
con = duckdb.connect()
con.execute("SET threads=32")
SQL = """
SELECT count(*) FILTER (WHERE target_decoy = 'target' AND q_value <= 0.01
                        AND (q_value_notch IS NULL OR q_value_notch <= 0.01)
                        AND coalesce(notch_ambiguous, false) = false),
       count(*) FILTER (WHERE target_decoy = 'target' AND pep_q_value <= 0.01),
       min(pep_q_value) FILTER (WHERE target_decoy = 'target')
FROM read_parquet(?)
"""
losers = sorted((r for r in rows if r["ratio"] < 1), key=lambda r: r["ratio"])
gainers = sorted((r for r in rows if r["ratio"] >= 1), key=lambda r: r["ratio"])
sample = gainers[:: max(1, len(gainers) // 12)]


def report(label, group):
    print(label)
    print("  deposit peptide_ratio psm_q_rule psm_pep_rule psm_ratio min_pep_q")
    total_q = total_pep = 0
    for r in group:
        found = glob.glob(f"F:/aging_data/repo/store/{r['dataset']}/{bundles[r['dataset']]}*/**/psms.parquet", recursive=True)
        if not found:
            print(" ", r["dataset"], "no psms.parquet")
            continue
        q, pep, low = con.execute(SQL, [found[0]]).fetchone()
        total_q += q
        total_pep += pep
        print(f"  {r['dataset']} {r['ratio']} {q:,} {pep:,} {pep / q if q else 0:.3f} {low}")
    print(f"  total {total_q:,} {total_pep:,}")


report("PEPTIDE-LEVEL LOSERS", losers)
report("SAMPLE THAT GAINS AT PEPTIDE LEVEL", sample)
