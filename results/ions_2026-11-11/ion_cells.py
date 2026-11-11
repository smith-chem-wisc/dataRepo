"""Scratch, read-only (1.5.0 build list item 3, peptidoform_ions): for every bundle aging's serving catalog holds, read the
AllPeptides.psmtsv it was ingested from and count, among target rows (T, ET) that pass the search's confidence rule
(item 2: PEP_QValue strictly below 0.01; QValue Notch for PXD058775, the one search off PEP):
  - rows; rows whose Full Sequence is ambiguous (holds '|'); rows whose six Matched Ion cells are blank (MetaMorpheus
    writes " " for a match with no ion list) or hold '|'; Matched Ion Counts that are not one whole number;
  - Full Sequences written twice (the proposed key is (peptidoform_id, full_sequence));
  - contaminant rows that pass (left out by a target-only rule).
Also lists bundles whose AllPeptides.psmtsv is gone from disk."""
import concurrent.futures
import json
import os
import sys
import time

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "F:/aging_data/repo"
NOTCH = {"PXD058775"}
with open(f"{ROOT}/catalogs/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
cat = duckdb.connect(os.path.join(f"{ROOT}/catalogs", latest["catalog"]), read_only=True)
bundles = cat.execute("SELECT dataset_id, bundle_id FROM catalog_bundles ORDER BY dataset_id").fetchall()
cat.close()
print("catalog", latest["catalog_id"], len(bundles), "bundles")

ION = ["Matched Ion Series", "Matched Ion Mass-To-Charge Ratios", "Matched Ion Mass Diff (Da)", "Matched Ion Mass Diff (Ppm)",
       "Matched Ion Intensities", "Matched Ion Counts"]
BLANK = " OR ".join(f'"{c}" IS NULL OR trim("{c}") = \'\'' for c in ION)
PIPE = " OR ".join(f'"{c}" LIKE \'%|%\'' for c in ION)
SQL = """
WITH r AS (
  SELECT * FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
                         max_line_size=100000000, sample_size=2000)
), pass AS (
  SELECT * FROM r WHERE try_cast("{col}" AS DOUBLE) < 0.01
)
SELECT
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET')),
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET') AND "Full Sequence" LIKE '%|%'),
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET') AND ({blank})),
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET') AND ({pipe})),
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET') AND try_cast("Matched Ion Counts" AS BIGINT) IS NULL),
  (SELECT count(*) - count(DISTINCT "Full Sequence") FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET')),
  (SELECT count(*) FROM pass WHERE "Decoy/Contaminant/Target" NOT IN ('T', 'ET', 'D')),
  (SELECT min("Matched Ion Counts") FROM pass WHERE "Decoy/Contaminant/Target" IN ('T', 'ET') AND try_cast("Matched Ion Counts" AS BIGINT) IS NULL)
"""


def measure(item):
    dataset, bundle = item
    with open(f"{ROOT}/store/{dataset}/{bundle}/bundle.json", encoding="utf-8") as handle:
        sources = json.load(handle)["sources"]
    paths = [s["path"] for s in sources if s.get("role") == "peptides"]
    if not paths or not os.path.exists(paths[0]):
        return dataset, bundle, None
    con = duckdb.connect()
    con.execute("SET threads=12")
    try:
        col = "QValue Notch" if dataset in NOTCH else "PEP_QValue"
        return dataset, bundle, con.execute(SQL.format(col=col, blank=BLANK, pipe=PIPE), [paths[0]]).fetchone()
    finally:
        con.close()


HEADER = ["dataset", "bundle", "n_pass", "n_ambiguous", "n_blank_ion_cell", "n_pipe_ion_cell", "n_counts_not_int",
          "n_full_sequence_repeated", "n_contaminant_pass", "counts_example"]
started = time.time()
results, missing = [], []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for index, (dataset, bundle, values) in enumerate(pool.map(measure, bundles), 1):
        if values is None:
            missing.append((dataset, bundle))
        else:
            results.append([dataset, bundle, *values])
        if index % 30 == 0:
            print(f"{index}/{len(bundles)} {time.time() - started:.0f}s")
with open(os.path.join(HERE, "ion_cells.tsv"), "w", encoding="utf-8", newline="\n") as out:
    out.write("\t".join(HEADER) + "\n")
    for row in results:
        out.write("\t".join("" if v is None else str(v) for v in row) + "\n")
print(f"done {len(results)} read, {len(missing)} without AllPeptides.psmtsv on disk, {time.time() - started:.0f}s")
for i, name in enumerate(HEADER[2:9], 2):
    total = sum(r[i] for r in results)
    deposits = sum(1 for r in results if r[i])
    print(f"  {name}: {total:,} rows in {deposits} deposit(s)")
print("deposits with no passing target row:", [r[0] for r in results if r[2] == 0])
print("counts examples:", sorted({r[9] for r in results if r[9] is not None})[:10])
print("most ambiguous:", sorted(((r[3], r[0]) for r in results), reverse=True)[:5])
print("missing:", missing)
