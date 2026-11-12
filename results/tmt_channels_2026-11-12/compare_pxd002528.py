"""1.5.0 item 14 (DATAREPO-88 a, PXR-R54), scratch and read-only: PXD002528 ingested by feat/1.5.0 (store_item14) against
its bundle served by 1.4.5 (aging's store). Its design marks 116 of its 200 channels `empty` (PXReprise's default design)."""
import glob
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
new = glob.glob("F:/datarepo_scratch_150/store_item14/PXD002528/*/")[0]
old = "F:/aging_data/repo/store/PXD002528/5ca828db8870d011/"
con = duckdb.connect()


def q(sql):
    return con.execute(sql).fetchall()


print("served 1.4.5 bundle:", old)
print("1.5.0 bundle:       ", new)
def rows(b, table):
    return q(f"SELECT count(*) FROM '{b}{table}.parquet'")[0][0]


for name, b in (("1.4.5", old), ("1.5.0", new)):
    print(f"{name}: assays {rows(b, 'assays')}, samples {rows(b, 'samples')}, quant_values {rows(b, 'quant_values'):,}")
print("1.5.0 assays by design_sample_type, with a sample / without:",
      q(f"SELECT design_sample_type, count(sample_id), count(*) - count(sample_id) FROM '{new}assays.parquet' GROUP BY 1 ORDER BY 1"))
print("1.5.0 plexes:", q(f"SELECT count(DISTINCT plex), count(*) FILTER (WHERE plex IS NULL) FROM '{new}assays.parquet'")[0])
print("1.5.0 runs.reporter_level:", q(f"SELECT reporter_level, count(*) FROM '{new}runs.parquet' GROUP BY 1"))
empty_values = q(f"""SELECT count(*), median(v.value) FROM '{new}quant_values.parquet' v JOIN '{new}assays.parquet' a USING (assay_id)
                     WHERE a.design_sample_type = 'empty'""")[0]
real_values = q(f"""SELECT count(*), median(v.value) FROM '{new}quant_values.parquet' v JOIN '{new}assays.parquet' a USING (assay_id)
                    WHERE a.design_sample_type <> 'empty'""")[0]
print(f"values on empty channels: {empty_values[0]:,}, median {empty_values[1]:.4g}; on study samples: {real_values[0]:,}, median {real_values[1]:.4g}")
same_values = q(f"""SELECT count(*) FROM (SELECT assay_id, feature_id, definition_id, value FROM '{old}quant_values.parquet'
                    EXCEPT ALL SELECT assay_id, feature_id, definition_id, value FROM '{new}quant_values.parquet')""")[0][0]
print("quant_values rows of 1.4.5 not in 1.5.0 (assay, feature, definition, value):", same_values)
gone = q(f"""SELECT count(*) FROM '{old}samples.parquet' WHERE sample_id NOT IN (SELECT sample_id FROM '{new}samples.parquet')""")[0][0]
print("1.4.5 samples not in 1.5.0 (the empty channels' fake samples):", gone)
# The rows that differ: is it only the peptidoform key (item 1: mzLib 1.0.597 links more UniProt modifications to Unimod)?
diff = q(f"""SELECT o.feature_id FROM (SELECT assay_id, feature_id, definition_id, value FROM '{old}quant_values.parquet'
             EXCEPT ALL SELECT assay_id, feature_id, definition_id, value FROM '{new}quant_values.parquet') o""")
print("of those, keyed by a mass tag in 1.4.5 ('[+' or '[-' in feature_id):", sum(("[+" in f or "[-" in f) for (f,) in diff))
by_value = q(f"""SELECT count(*) FROM (SELECT assay_id, definition_id, value FROM '{old}quant_values.parquet'
                 EXCEPT ALL SELECT assay_id, definition_id, value FROM '{new}quant_values.parquet')""")[0][0]
print("rows that differ once the feature key is set aside (assay, definition, value):", by_value)
