"""G94: today's derived tables (Catalog.cs BuildDerived), run over the views catalog. Scratch measurement only."""
import os, sys, time
import duckdb

STORE = r"F:\aging_data\repo\store"
cat = sys.argv[1]
con = duckdb.connect(cat)
con.execute(f"SET file_search_path = '{STORE}'")
con.execute("DROP TABLE IF EXISTS protein_index")
T = "0.01"
steps = [
    ("peptidoforms_1pct view", f"CREATE OR REPLACE VIEW peptidoforms_1pct AS SELECT * FROM peptidoforms WHERE target_decoy = 'target' "
                               f"AND best_q_value <= {T} AND (best_q_value_notch IS NULL OR best_q_value_notch <= {T})"),
    ("protein_groups_1pct view", f"CREATE OR REPLACE VIEW protein_groups_1pct AS SELECT * FROM protein_groups WHERE target_decoy <> 'decoy' AND q_value <= {T}"),
    ("dataset_overview (no PSM counts)", """
        CREATE TABLE dataset_overview AS
        SELECT d.dataset_id, d.bundle_id, d.title,
            (SELECT count(*) FROM runs r WHERE r.dataset_id = d.dataset_id) AS n_runs,
            (SELECT count(*) FROM samples s WHERE s.dataset_id = d.dataset_id) AS n_samples,
            (SELECT count(*) FROM peptidoforms_1pct pf WHERE pf.dataset_id = d.dataset_id) AS n_peptidoforms_1pct,
            (SELECT count(*) FROM protein_groups_1pct pg WHERE pg.dataset_id = d.dataset_id) AS n_protein_groups_1pct,
            (SELECT count(*) FROM ptm_sites ps WHERE ps.dataset_id = d.dataset_id) AS n_ptm_sites,
            (SELECT count(*) FROM quant_values q JOIN assays a ON a.assay_id = q.assay_id JOIN runs r ON r.run_id = a.run_id
              WHERE r.dataset_id = d.dataset_id) AS n_quant_values,
            (SELECT count(*) FROM findings f WHERE f.dataset_id = d.dataset_id AND f.severity IN ('warning', 'error')) AS n_open_findings
        FROM datasets d"""),
    ("protein_datasets", """
        CREATE TABLE protein_datasets AS
        WITH observed AS (SELECT DISTINCT dataset_id, protein_accession, is_contaminant FROM proteins),
        in_groups AS (SELECT dataset_id, unnest(protein_accessions) AS protein_accession, protein_group_id, q_value FROM protein_groups_1pct),
        in_peptides AS (SELECT dataset_id, unnest(protein_accessions) AS protein_accession, peptidoform_id FROM peptidoforms_1pct)
        SELECT o.dataset_id, o.protein_accession, o.is_contaminant,
               count(DISTINCT g.protein_group_id) AS n_protein_groups, count(DISTINCT p.peptidoform_id) AS n_peptidoforms,
               min(g.q_value) AS best_q_value
        FROM observed o
        LEFT JOIN in_groups g ON g.dataset_id = o.dataset_id AND g.protein_accession = o.protein_accession
        LEFT JOIN in_peptides p ON p.dataset_id = o.dataset_id AND p.protein_accession = o.protein_accession
        GROUP BY o.dataset_id, o.protein_accession, o.is_contaminant"""),
    ("protein_index", """
        CREATE TABLE protein_index AS
        SELECT p.protein_accession, max(p.gene) AS gene, max(p.organism) AS organism,
            count(DISTINCT p.dataset_id) FILTER (WHERE p.is_contaminant) AS n_datasets_contaminant,
            count(DISTINCT p.dataset_id) AS n_datasets,
            count(DISTINCT p.dataset_id) FILTER (WHERE d.n_protein_groups > 0 OR d.n_peptidoforms > 0) AS n_datasets_1pct,
            list_sort(list(DISTINCT p.dataset_id)) AS dataset_ids,
            list_sort(list(DISTINCT p.dataset_id) FILTER (WHERE d.n_protein_groups > 0 OR d.n_peptidoforms > 0)) AS dataset_ids_1pct,
            min(d.best_q_value) AS best_q_value
        FROM proteins p LEFT JOIN protein_datasets d ON d.dataset_id = p.dataset_id AND d.protein_accession = p.protein_accession
        GROUP BY p.protein_accession"""),
    ("search_modifications_placed", r"""
        CREATE TABLE search_modifications_placed AS
        SELECT dataset_id, bundle_id, tag, count(*) AS n_placements, count(DISTINCT peptidoform_id) AS n_peptidoforms
        FROM (SELECT dataset_id, bundle_id, peptidoform_id, unnest(regexp_extract_all(peptidoform, '\[([^\]]*)\]', 1)) AS tag
              FROM peptidoforms_1pct)
        GROUP BY dataset_id, bundle_id, tag"""),
    ("peptide_index", """
        CREATE TABLE peptide_index AS
        SELECT base_sequence, count(DISTINCT dataset_id) AS n_datasets, list_sort(list(DISTINCT dataset_id)) AS dataset_ids,
               count(*) AS n_peptidoforms, min(best_q_value) AS best_q_value
        FROM peptidoforms_1pct GROUP BY base_sequence"""),
]
total = 0.0
for label, sql in steps:
    t = time.time(); con.execute(sql); dt = time.time() - t; total += dt
    print(f"  {label:34s} {dt:6.1f} s")
for t in ("dataset_overview", "protein_datasets", "protein_index", "search_modifications_placed", "peptide_index"):
    print(f"  rows {t:30s} {con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]:>12,}")
con.execute("CHECKPOINT")
con.close()
print(f"derived total {total:.1f} s; file {os.path.getsize(cat)/1e6:.1f} MB")
