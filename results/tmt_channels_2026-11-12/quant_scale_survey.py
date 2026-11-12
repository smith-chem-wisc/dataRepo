"""1.5.0 item 14 (DATAREPO-88 b), scratch and read-only: what dataset_overview.quant_scale will say for every isobaric search
aging's serving catalog serves, from the qc_report.json each served bundle copied (its `sps_ms3` per file), by the rule the
build applies: every run ms3 -> reporter_ms3, every run ms2 -> reporter_ms2, both -> mixed, any unknown -> not recorded."""
import collections
import glob
import json
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
p = json.load(open("F:/aging_data/repo/catalogs/latest.json"))
con = duckdb.connect("F:/aging_data/repo/catalogs/" + p["catalog"], read_only=True)
rows = con.execute("""SELECT d.dataset_id, d.search_engine_version, b.path FROM datasets d JOIN catalog_bundles b USING (dataset_id)
                      WHERE d.quant_method = 'isobaric' ORDER BY 1""").fetchall()
print(f"catalog {p['catalog_id']}: {len(rows)} isobaric searches")
scales = collections.Counter()
for ds, version, path in rows:
    qc = glob.glob(f"{path}/sources/qc_report.json")
    levels = []
    if qc:
        doc = json.load(open(qc[0], encoding="utf-8"))
        n_runs = con.execute("SELECT count(*) FROM runs WHERE dataset_id = ?", [ds]).fetchone()[0]
        for name in [r[0] for r in con.execute("SELECT file_name FROM runs WHERE dataset_id = ?", [ds]).fetchall()]:
            entry = doc.get(name) or doc.get(name.rsplit(".", 1)[0]) or {}
            v = entry.get("sps_ms3")
            levels.append("ms3" if v is True else "ms2" if v is False else None)
    if not levels or any(x is None for x in levels):
        scale = "reporter_level_not_recorded"
    elif len(set(levels)) > 1:
        scale = "reporter_level_mixed"
    else:
        scale = "reporter_" + levels[0]
    scales[(scale, version)] += 1
    print(f"  {ds:12} MetaMorpheus {version:7} {len(levels):3} runs  {scale}")
print("by scale and release:", dict(sorted(scales.items())))
