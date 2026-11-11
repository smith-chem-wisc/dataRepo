"""Scratch, read-only: pairs each row compare_stores.py found moved between store595 and store597 with its counterpart,
and checks that only the peptidoform key changed (README.md's table)."""
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
A, B = "F:/datarepo_scratch_150/store595", "F:/datarepo_scratch_150/store597"
con = duckdb.connect()
con.execute("SET enable_progress_bar=false")


def moved(a, b, table):
    return (f"o AS (SELECT * FROM '{a}/{table}.parquet' EXCEPT ALL SELECT * FROM '{b}/{table}.parquet'), "
            f"n AS (SELECT * FROM '{b}/{table}.parquet' EXCEPT ALL SELECT * FROM '{a}/{table}.parquet')")


for ds, bid in [("PXD011740", "b7dbca088aa5c165"), ("PXD034564", "ff841cc55ccccb31")]:
    a, b = f"{A}/{ds}/{bid}", f"{B}/{ds}/{bid}"
    print(ds, "peptidoforms (paired, mass tag -> none, other columns equal):", con.sql(f"""
        WITH {moved(a, b, 'peptidoforms')}
        SELECT count(*), count(*) FILTER (WHERE o.peptidoform LIKE '%[+%' AND n.peptidoform NOT LIKE '%[+%'),
               count(*) FILTER (WHERE o.best_q_value IS NOT DISTINCT FROM n.best_q_value AND o.n_psms IS NOT DISTINCT FROM n.n_psms
                                AND o.target_decoy = n.target_decoy AND o.base_sequence = n.base_sequence
                                AND o.best_pep IS NOT DISTINCT FROM n.best_pep)
        FROM o JOIN n ON o.engine_full_sequences = n.engine_full_sequences""").fetchone())
    cols = [r[0] for r in con.sql(f"DESCRIBE SELECT * FROM '{a}/psms.parquet'").fetchall()]
    other = " AND ".join(f'o."{c}" IS NOT DISTINCT FROM n."{c}"' for c in cols if c not in ("psm_id", "peptidoform", "usi"))
    print(ds, "psms (paired by psm_id, only peptidoform/usi differ, old had a mass tag):", con.sql(f"""
        WITH {moved(a, b, 'psms')}
        SELECT count(*), count(*) FILTER (WHERE {other}), count(*) FILTER (WHERE o.peptidoform LIKE '%[+%')
        FROM o JOIN n USING (psm_id)""").fetchone())
    print(ds, "ptm_sites (paired by id, modification NULL -> accession):", con.sql(f"""
        WITH {moved(a, b, 'ptm_sites')}
        SELECT count(*), count(*) FILTER (WHERE o.modification IS NULL AND n.modification IS NOT NULL)
        FROM o JOIN n USING (ptm_site_id)""").fetchone())
    print(ds, "quant_values (moved old/new, old with a mass tag, (assay, definition, value) unmatched):", con.sql(f"""
        WITH {moved(a, b, 'quant_values')}
        SELECT (SELECT count(*) FROM o), (SELECT count(*) FROM n), (SELECT count(*) FROM o WHERE feature_id LIKE '%[+%'),
               (SELECT count(*) FROM (SELECT assay_id, definition_id, value FROM o
                                      EXCEPT ALL SELECT assay_id, definition_id, value FROM n))""").fetchone())
