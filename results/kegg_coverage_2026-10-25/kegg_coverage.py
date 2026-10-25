# Scratch measurement for kegg KEGG-D3 / KEGG-D1: Reactome coverage of the serving catalog's 1% protein groups.
import duckdb, sys

CAT = r"F:\aging_data\repo\catalogs\catalog-5c0c60396486635d.duckdb"
OUT = r"E:\CodeReview\kegg\results\xml_survey\out"
c = duckdb.connect(CAT, read_only=True)
c.execute("SET threads=16")
for sp in ["human", "mouse", "rat"]:
    c.execute(f"""CREATE TEMP TABLE r_{sp} AS SELECT accession, pathway_id, NULLIF(molecule,'') AS molecule
                  FROM read_csv('{OUT}\\reactome_direct_{sp}.tsv', delim='\t', header=true, all_varchar=true)""")
c.execute("""CREATE TEMP TABLE r AS
  SELECT 'NCBITaxon:9606' AS organism, * FROM r_human UNION ALL
  SELECT 'NCBITaxon:10090', * FROM r_mouse UNION ALL
  SELECT 'NCBITaxon:10116', * FROM r_rat""")

print("== KEGG-D1: organisms per target database (identified non-contaminant, non-decoy proteins)")
for row in c.execute("""
  SELECT dd.database, count(DISTINCT dd.dataset_id) AS datasets, list(DISTINCT p.organism ORDER BY p.organism) AS organisms,
         count(*) FILTER (WHERE p.organism IS NULL) AS null_org
  FROM dataset_databases dd JOIN proteins p ON p.dataset_id = dd.dataset_id
  WHERE dd.role = 'target' AND NOT p.is_contaminant AND p.protein_accession NOT LIKE 'DECOY%'
  GROUP BY 1 ORDER BY 1""").fetchall():
    print("  ", row)
print("  datasets with >1 target database:", c.execute("""
  SELECT count(*) FROM (SELECT dataset_id FROM dataset_databases WHERE role='target' GROUP BY 1 HAVING count(*)>1)""").fetchone())
print("  datasets whose identified non-contaminant proteins span >1 organism:", c.execute("""
  SELECT count(*) FROM (SELECT dataset_id FROM proteins WHERE NOT is_contaminant AND protein_accession NOT LIKE 'DECOY%'
  AND organism IS NOT NULL GROUP BY 1 HAVING count(DISTINCT organism)>1)""").fetchone())

# Members of each 1% target group, with their organism and base accession (isoform suffix and variant suffix removed).
c.execute(r"""CREATE TEMP TABLE m AS
  WITH u AS (SELECT dataset_id, protein_group_id, unnest(protein_accessions) AS acc
             FROM protein_groups_1pct WHERE target_decoy = 'target')
  SELECT u.dataset_id, u.protein_group_id, u.acc AS member, p.organism, p.is_contaminant,
         regexp_extract(u.acc, '^([A-Za-z0-9]+)', 1) AS base
  FROM u LEFT JOIN proteins p ON p.dataset_id = u.dataset_id AND p.protein_accession = u.acc""")
c.execute("""CREATE TEMP TABLE mg AS
  SELECT m.*,
    EXISTS (SELECT 1 FROM r WHERE r.accession = m.base AND r.organism = m.organism) AS hit_any,
    EXISTS (SELECT 1 FROM r WHERE r.accession = m.base AND r.organism = m.organism
            AND (r.molecule IS NULL OR r.molecule = m.member)) AS hit_rule
  FROM m WHERE NOT coalesce(m.is_contaminant, false)""")
# A group's species: the single organism of its non-contaminant members (groups mixing organisms are counted apart).
c.execute("""CREATE TEMP TABLE gg AS
  SELECT dataset_id, protein_group_id, any_value(organism) AS organism, count(DISTINCT organism) AS n_org,
         bool_or(hit_any) AS hit_any, bool_or(hit_rule) AS hit_rule, count(*) AS members
  FROM mg GROUP BY 1, 2""")
c.execute("""CREATE TEMP TABLE genes AS
  SELECT g.dataset_id, g.protein_group_id, count(DISTINCT pg.gene_id) AS n_gene,
         count(*) FILTER (WHERE pg.gene_id IS NULL) AS unresolved
  FROM mg g LEFT JOIN protein_genes pg ON pg.dataset_id = g.dataset_id AND pg.protein_accession = g.member
  GROUP BY 1, 2""")

print("\n== KEGG-D3: 1% target protein groups (contaminant-only groups left out), per species")
for row in c.execute("""
  SELECT gg.organism, count(DISTINCT gg.dataset_id) AS datasets, count(*) AS groups,
         round(100.0*avg(hit_rule::int),1) AS pct_reactome_isoform_rule,
         round(100.0*avg(hit_any::int),1) AS pct_reactome_any_ref_on_entry,
         round(100.0*avg((n_gene>1)::int),1) AS pct_groups_gt1_gene,
         round(100.0*avg((members>1)::int),1) AS pct_groups_gt1_member,
         round(100.0*avg((unresolved>0)::int),1) AS pct_groups_with_unresolved_member
  FROM gg JOIN genes USING (dataset_id, protein_group_id)
  WHERE gg.n_org = 1 GROUP BY 1 ORDER BY 3 DESC""").fetchall():
    print("  ", row)
print("  groups with no organism / mixed organisms:", c.execute(
    "SELECT count(*) FILTER (WHERE organism IS NULL), count(*) FILTER (WHERE n_org>1) FROM gg").fetchone())

print("\n== per-dataset median share with a pathway (isoform rule)")
for row in c.execute("""
  SELECT organism, count(*) AS datasets, round(100*median(s),1), round(100*min(s),1), round(100*max(s),1)
  FROM (SELECT dataset_id, organism, avg(hit_rule::int) AS s FROM gg WHERE n_org=1 GROUP BY 1,2)
  GROUP BY 1 ORDER BY 2 DESC""").fetchall():
    print("  ", row)

print("\n== distinct entries reached (union of groups' members over all datasets)")
for row in c.execute("""
  SELECT organism, count(DISTINCT base) AS entries_seen, count(DISTINCT base) FILTER (WHERE hit_any) AS with_reactome
  FROM mg WHERE organism IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""").fetchall():
    print("  ", row)
