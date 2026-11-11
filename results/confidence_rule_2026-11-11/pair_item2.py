"""Scratch, read-only (1.5.0 item 2): pairs the rows compare_item2.py found moved between aging's served bundles and the
item-2 scratch bundles, to show they are item 1's mzLib 1.0.597 key change (a mass tag becomes a Unimod accession) and
nothing of item 2's. Same checks as results/mzlib597_2026-11-11/pair_moved.py."""
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
con = duckdb.connect()
PAIRS = {"PXD057502": ("7f2a7f357e3b8713", "7a9b7c7a33af3651"), "PXD058775": ("f973337f70227e3d", "0b92797364a7e76f")}
print("moved rows, paired (item 1's mzLib 1.0.597 key change expected):")
for ds, (old, new) in PAIRS.items():
    a, b = f"F:/aging_data/repo/store/{ds}/{old}", f"F:/datarepo_scratch_150/store_item2/{ds}/{new}"
    cols = ", ".join(f'"{c}"' for c, *_ in con.sql(f"DESCRIBE SELECT * FROM '{a}/peptidoforms.parquet'").fetchall())
    peptidoforms = con.sql(f"""
        WITH o AS (SELECT {cols} FROM '{a}/peptidoforms.parquet' EXCEPT ALL SELECT {cols} FROM '{b}/peptidoforms.parquet'),
             n AS (SELECT {cols} FROM '{b}/peptidoforms.parquet' EXCEPT ALL SELECT {cols} FROM '{a}/peptidoforms.parquet')
        SELECT count(*), count(*) FILTER (WHERE o.peptidoform LIKE '%[+%' AND n.peptidoform NOT LIKE '%[+%'),
               count(*) FILTER (WHERE o.best_q_value IS NOT DISTINCT FROM n.best_q_value AND o.n_psms IS NOT DISTINCT FROM n.n_psms
                                AND o.best_pep IS NOT DISTINCT FROM n.best_pep)
        FROM o JOIN n ON o.engine_full_sequences = n.engine_full_sequences""").fetchone()
    psm_cols = [c for c, *_ in con.sql(f"DESCRIBE SELECT * FROM '{a}/psms.parquet'").fetchall()]
    other = " AND ".join(f'o."{c}" IS NOT DISTINCT FROM n."{c}"' for c in psm_cols if c not in ("psm_id", "peptidoform", "usi"))
    psms = con.sql(f"""
        WITH o AS (SELECT * FROM '{a}/psms.parquet' EXCEPT ALL SELECT * FROM '{b}/psms.parquet'),
             n AS (SELECT * FROM '{b}/psms.parquet' EXCEPT ALL SELECT * FROM '{a}/psms.parquet')
        SELECT count(*), count(*) FILTER (WHERE {other}), count(*) FILTER (WHERE o.peptidoform LIKE '%[+%')
        FROM o JOIN n USING (psm_id)""").fetchone()
    sites = con.sql(f"""
        WITH o AS (SELECT * FROM '{a}/ptm_sites.parquet' EXCEPT ALL SELECT * FROM '{b}/ptm_sites.parquet'),
             n AS (SELECT * FROM '{b}/ptm_sites.parquet' EXCEPT ALL SELECT * FROM '{a}/ptm_sites.parquet')
        SELECT count(*), count(*) FILTER (WHERE o.modification IS NULL AND n.modification IS NOT NULL)
        FROM o JOIN n USING (ptm_site_id)""").fetchone()
    print(f"  {ds}: peptidoforms (paired, mass tag -> no mass tag, other columns equal) {peptidoforms}; "
          f"psms (paired by id, only peptidoform/usi differ, old had a mass tag) {psms}; ptm_sites (paired, NULL -> accession) {sites}")
