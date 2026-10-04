"""Write the Python 0.32.0 MCP server's answers to a corpus of tool calls, for the C# parity test.

Each call goes through `CatalogServer` exactly as `bound_tools` sends it (a DataRepoError becomes the
`{error, message, hint}` payload; anything else propagates and is recorded as an exception), and the
answer is rendered as the Python MCP SDK renders it for the agent:
`pydantic_core.to_json(result, fallback=str, indent=2)`.

usage: python mcp_parity.py <catalog.duckdb> <out.json> [--real]

`pytz` must be importable (DuckDB's Python client needs it to return a TIMESTAMP WITH TIME ZONE); put
it on PYTHONPATH if the environment lacks it.
"""
from __future__ import annotations

import json
import os
import sys

# `pytz` for TIMESTAMP WITH TIME ZONE, from a folder beside this script when the environment lacks it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylib"))

import duckdb
import pydantic_core

from datarepo.errors import DataRepoError
from datarepo.mcp import CatalogServer, _error_payload

catalog, out_path = sys.argv[1], sys.argv[2]
real = "--real" in sys.argv[3:]

SLOW = ("SELECT count(*) FROM (SELECT a.range, b.range FROM range(200000) a, range(200000) b "
        "WHERE (a.range * b.range) % 7 = 3)")

# --------------------------------------------------------------------------------------------------
# the corpus
# --------------------------------------------------------------------------------------------------

con = duckdb.connect(catalog, read_only=True)
tables = sorted(r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall())


def q(sql, *params):
    return con.execute(sql, list(params)).fetchall()


calls: list[dict] = []


def call(tool, server=None, **args):
    calls.append({"id": f"{len(calls):03d}", "server": server or {}, "tool": tool, "args": args})


# describe: the catalog, every table (concise), a sample in detail, enums, definitions, layers, unknowns
for target in [None, "", "  ", "catalog", "CATALOG", "overview", ".", "tables", "schema", "Tables", " SCHEMA "]:
    call("describe", target=target)
for t in tables:
    call("describe", target=t)
for t in ["psms", "peptidoforms", "protein_groups", "ptm_sites", "samples", "runs", "dataset_overview",
          "protein_index", "sample_ages", "catalog_meta", "protein_localizations", "gene_resolutions"]:
    if t in tables:
        call("describe", target=t, detail="detailed")
for target in ["Acquisition", "TargetDecoy", "SiteType", "AgeResponse", "FitRefusal", "QuantMethod"]:
    call("describe", target=target)
defs = [r[0] for r in q("SELECT DISTINCT definition_id FROM definitions ORDER BY 1 LIMIT 6")]
for d in defs:
    call("describe", target=d)
call("describe", target="PEP:def-pep")
call("describe", target="aging")
call("describe", target="AGING")
for target in ["psmz", "protien_index", "Psms", "tabels", "datasetz", "xyzzy", "it's", "é", "acquisition",
               "PSMS_1PCT", "sample_age", "catalog_tabel"]:
    call("describe", target=target)
call("describe", target=" psms ")
call("describe", target="psms", detail="verbose")
call("describe", target="psms", detail="")
call("describe", detail="DETAILED")

# search: every kind, ids from the catalog, truncation, refusals
accessions = [r[0] for r in q("SELECT protein_accession FROM protein_index ORDER BY n_datasets_1pct DESC, protein_accession LIMIT 3")]
genes = [r[0] for r in q("SELECT gene FROM protein_index WHERE gene IS NOT NULL ORDER BY n_datasets DESC, gene LIMIT 3")]
decoy = [r[0] for r in q("SELECT protein_accession FROM protein_index WHERE starts_with(protein_accession, 'DECOY_') ORDER BY 1 LIMIT 1")]
contam = [r[0] for r in q("SELECT protein_accession FROM protein_index WHERE n_datasets_contaminant > 0 ORDER BY 1 LIMIT 1")]
peptides = [r[0] for r in q("SELECT base_sequence FROM peptide_index ORDER BY n_datasets DESC, base_sequence LIMIT 2")]
datasets = [r[0] for r in q("SELECT dataset_id FROM datasets ORDER BY 1 LIMIT 2")]
runs = [r[0] for r in q("SELECT file_name FROM runs ORDER BY 1 LIMIT 1")]
for value in accessions + genes + decoy + contam + peptides + datasets + runs:
    call("search", query=value)
for value in [a.lower() for a in accessions[:1]] + [p.lower() for p in peptides[:1]] + [p[2:9] for p in peptides[:1]]:
    call("search", query=value)
for value in ["LMNA", "P02545", "ALB", "P02768", "KRT", "KRT1", "COX4I1", "cytochrome c oxidase", "mitochondria",
              "mitochondrion", "nucleus", "lysosome", "skeletal muscle", "plasma", "brain", "liver", "Homo sapiens",
              "Mus musculus", "human", "Thermo", "Q Exactive", "Orbitrap", "Oxidation", "phospho", "Phospho",
              "Carbamidomethyl", "acetyl", "Deamidation", "GlyGly", "DEF-PEP", "pep", "occupancy", "1pct",
              "PXD036557", "pxd999999", "zzzzqqq", "SAD", "PEPTIDE", "PEPTIDES", "ß", "straße", "İstanbul",
              "100%", "a_b", "'quoted'", "  padded  ", "\x1ctrim\x1f"]:
    call("search", query=value)
for kind in ["dataset", "protein", "peptide", "modification", "sample", "run", "definition", "localization"]:
    call("search", query=(peptides[0] if kind == "peptide" else genes[0] if kind == "protein" else "a"), kind=kind)
call("search", query="A", kind="protein", limit=1)
call("search", query="P", kind="protein", limit=2)
call("search", query="P", kind="protein", limit=0)
call("search", query="P", kind="protein", limit=-5)
call("search", query="P", kind="protein", limit=500)
call("search", query="e", limit=1)
call("search", query="e", kind="definition", limit=3)
call("search", query="x", kind="nope")
call("search", query="x", kind="Protein")
call("search", query="")
call("search", query="   ")

# sql: answers, refusals, guards, forgeries, caps, the watchdog, types
dsid = datasets[0]
for sql in [
    "SELECT dataset_id, count(*) AS n FROM psms GROUP BY 1 ORDER BY 1",
    "SELECT count(*) FROM psms_1pct",
    "SELECT dataset_id, n_psms_1pct, n_peptidoforms_1pct, n_protein_groups_1pct FROM dataset_overview ORDER BY 1",
    "SELECT dataset_id, title, organisms, acquisition, quant_method, labelling, enrichment FROM datasets ORDER BY 1",
    "SELECT * FROM datasets",
    "SELECT * FROM dataset_overview",
    "SELECT * FROM catalog_meta",
    "SELECT * FROM catalog_bundles",
    "SELECT * FROM catalog_tables ORDER BY table_name",
    "SELECT * FROM catalog_study_bundles",
    "SELECT * FROM catalog_checks ORDER BY name LIMIT 20",
    "SELECT * FROM findings ORDER BY finding_id LIMIT 20",
    "SELECT * FROM definitions ORDER BY definition_id LIMIT 5",
    "SELECT * FROM metrics ORDER BY dataset_id, name LIMIT 30",
    "SELECT * FROM runs ORDER BY run_id LIMIT 5",
    "SELECT run_id, acquisition_datetime FROM runs ORDER BY run_id LIMIT 5",
    "SELECT * FROM provenance_records ORDER BY stage LIMIT 5",
    "SELECT * FROM samples ORDER BY sample_id LIMIT 10",
    "SELECT * FROM sample_characteristics ORDER BY sample_id, name LIMIT 10",
    "SELECT s.sample_id, a.age_years FROM samples s LEFT JOIN sample_ages a USING (sample_id) ORDER BY 1 LIMIT 10",
    "SELECT * FROM sample_ages ORDER BY sample_id LIMIT 10",
    "SELECT count(*) FROM curated_sample_characteristics",
    "SELECT * FROM age_effects LIMIT 5",
    "SELECT * FROM gene_resolutions ORDER BY accession LIMIT 10",
    "SELECT * FROM protein_genes LIMIT 10",
    "SELECT * FROM releases",
    "SELECT * FROM glycopeptides LIMIT 3",
    "SELECT * FROM ptm_sites ORDER BY ptm_site_id LIMIT 10",
    "SELECT * EXCLUDE (modification_names), list_sort(modification_names) AS names FROM ptm_sites_by_chemistry ORDER BY ALL LIMIT 10",
    "SELECT modification_name, count(*) AS n FROM ptm_sites GROUP BY 1 ORDER BY 2 DESC, 1",
    "SELECT * FROM ptm_stoichiometry ORDER BY ptm_site_id, assay_id LIMIT 10",
    "SELECT * FROM quant_values ORDER BY assay_id, feature_id LIMIT 10",
    "SELECT feature_type, definition_id, count(*), count(value), min(value), max(value) FROM quant_values GROUP BY 1, 2 ORDER BY 1, 2",
    "SELECT * FROM protein_groups ORDER BY protein_group_id LIMIT 5",
    "SELECT * FROM protein_groups_1pct ORDER BY protein_group_id LIMIT 5",
    "SELECT * FROM peptidoforms_1pct ORDER BY peptidoform_id LIMIT 5",
    "SELECT * FROM protein_index ORDER BY protein_accession LIMIT 10",
    "SELECT * FROM peptide_index ORDER BY base_sequence LIMIT 10",
    "SELECT * FROM protein_datasets ORDER BY protein_accession, dataset_id LIMIT 10",
    "SELECT * FROM search_modifications_declared ORDER BY 1, 2 LIMIT 10",
    "SELECT * FROM search_modifications_placed ORDER BY 1, 2 LIMIT 10",
    "SELECT * FROM dataset_databases",
    "SELECT * FROM assays ORDER BY assay_id LIMIT 5",
    "SELECT target_decoy, count(*) FROM psms GROUP BY 1 ORDER BY 1",
    "SELECT dataset_id, count(*) FILTER (WHERE target_decoy = 'target') AS targets FROM psms_1pct GROUP BY 1 ORDER BY 1",
    "SELECT protein_accession, is_contaminant FROM protein_datasets WHERE is_contaminant ORDER BY 1",
    f"SELECT dataset_id, count(DISTINCT protein_group_id) FROM protein_groups_1pct WHERE dataset_id = '{dsid}' GROUP BY 1",
    "SELECT p.protein_accession, p.gene, d.dataset_id FROM protein_index p JOIN protein_datasets d USING (protein_accession) WHERE p.gene = 'LMNA' ORDER BY 3",
    "SELECT * FROM protein_localizations",
    "SELECT l.compartment, count(*) FROM protein_localizations l JOIN organelle_term_categories c USING (compartment) GROUP BY 1",
    "SELECT g.dataset_id, count(*) FROM protein_groups_1pct g LEFT JOIN protein_localizations l ON l.dataset_id = g.dataset_id GROUP BY 1 ORDER BY 1",
    "SELECT * FROM age_effects a JOIN organelle_age_summaries o USING (dataset_id)",
    # forgeries: a CTE named after a real view, a computed dataset_id/bundle_id
    "WITH protein_groups_1pct AS (SELECT 'PXD036557' AS dataset_id, 99999 AS n) SELECT * FROM protein_groups_1pct",
    "WITH psms AS (SELECT 1 AS x) SELECT count(*) FROM psms",
    "SELECT max(dataset_id) AS dataset_id, count(*) FROM ptm_sites",
    "SELECT 'bfd1f55807f661f7' AS bundle_id, 'PXD000000' AS dataset_id, 42 AS answer",
    "SELECT count(*) FROM (SELECT * FROM psms) AS protein_groups_1pct",
    # opaque table functions and tables in strings
    "SELECT count(*) FROM query_table('ptm_stoichiometry')",
    "SELECT * FROM query('SELECT count(*) FROM psms')",
    "SELECT 'psms' AS name, 'FROM psms' AS text",
    # run-relative columns
    "SELECT pep FROM psms ORDER BY psm_id LIMIT 3",
    "SELECT pep AS x FROM psms ORDER BY psm_id LIMIT 3",
    "SELECT p.pep FROM psms p ORDER BY p.psm_id LIMIT 3",
    "WITH t AS (SELECT pep FROM psms) SELECT count(*) FROM t",
    "SELECT * FROM psms ORDER BY psm_id LIMIT 2",
    "SELECT count(*) FROM (SELECT * FROM psms)",
    "SELECT dataset_id, median(pep) FROM psms GROUP BY 1 ORDER BY 1",
    "SELECT best_pep FROM peptidoforms ORDER BY peptidoform_id LIMIT 2",
    "SELECT pep_q_value FROM psms ORDER BY psm_id LIMIT 2",
    "SELECT 0.5 AS pep",
    "SELECT q_value FROM psms ORDER BY psm_id LIMIT 2",
    "SELECT COLUMNS('q_.*') FROM psms ORDER BY psm_id LIMIT 2",
    "SELECT PEP FROM psms ORDER BY psm_id LIMIT 1",
    # statement kinds: allowed
    "EXPLAIN SELECT * FROM psms",
    "SHOW TABLES",
    "DESCRIBE psms",
    "SUMMARIZE samples",
    "PRAGMA table_info('psms')",
    "PRAGMA version",
    "FROM datasets SELECT dataset_id",
    "VALUES (1, 'a'), (2, 'b')",
    "(SELECT 1 AS a) UNION ALL (SELECT 2)",
    "SELECT 1;",
    "  SELECT 1 ;  ",
    "SELECT 1 -- trailing comment",
    "/* lead */ SELECT 2",
    "SELECT ';' AS semi",
    # statement kinds: refused
    "DROP TABLE psms",
    "DROP TABLE nope",
    "DELETE FROM psms",
    "TRUNCATE psms",
    "UPDATE psms SET pep = 0",
    "INSERT INTO psms VALUES (1)",
    "INSERT INTO nope VALUES (1)",
    "WITH t AS (SELECT 1) INSERT INTO psms SELECT * FROM t",
    "CREATE TABLE x AS SELECT 1",
    "CREATE VIEW v AS SELECT 1",
    "ALTER TABLE psms ADD COLUMN z INT",
    "ATTACH 'other.duckdb' AS other (READ_ONLY)",
    "DETACH other",
    "COPY psms TO 'out.csv'",
    "COPY (SELECT 1) TO 'out.csv'",
    "EXPORT DATABASE 'exported'",
    "INSTALL httpfs",
    "LOAD httpfs",
    "SET threads=4",
    "SET enable_external_access=true",
    "RESET disabled_filesystems",
    "PRAGMA threads=4",
    "CALL pragma_version()",
    "CHECKPOINT",
    "BEGIN TRANSACTION",
    "VACUUM",
    "PREPARE p AS SELECT 1",
    "EXECUTE p",
    "USE memory",
    "UPDATE EXTENSIONS",
    "PIVOT psms ON target_decoy USING count(*)",
    "SELECT 1; SELECT 2",
    "SELECT 1; DROP TABLE psms",
    "SELECT * FROM nope; INSERT INTO nope VALUES (1)",
    "",
    "   ",
    ";",
    "-- only a comment",
    # not valid SQL, and DuckDB's own errors
    "SELEC 1",
    "SELECT FROM WHERE",
    "SELECT 'unterminated",
    "this is not sql",
    "SELECT nope FROM psms",
    "SELECT * FROM nope",
    "SELECT * FROM psm",
    "SELECT 1 + 'a'",
    "SELECT ?",
    "SELECT * FROM read_csv_auto('C:/Windows/win.ini')",
    "SELECT * FROM glob('*')",
    "SELECT 1/0 AS x, 1//0 AS y",
    # types
    "SELECT 1e-5::DOUBLE a, 1e20::DOUBLE b, 1.0::DOUBLE c, 0.1::FLOAT d, 123.450::DECIMAL(10,3) e, "
    "DATE '2026-01-02' f, TIMESTAMP '2026-01-02 03:04:05.5' g, TIMESTAMPTZ '2026-01-02 03:04:05+00' h, "
    "INTERVAL 3 DAY i, '00000000-0000-0000-0000-000000000001'::UUID j, {'x': 1, 'y': [1, 2]} k, MAP {'a': 1} l",
    "SELECT 'nan'::DOUBLE n, 'inf'::DOUBLE o, '-inf'::DOUBLE o2, 170141183460469231731687303715884105727::HUGEINT p, "
    "TIME '01:02:03' r, 1.5e300 s, 123456789012345678.0 t, -0.0::DOUBLE u, 1e16::DOUBLE v, 1e15::DOUBLE w, 0.0001 x, "
    "5e-324::DOUBLE y, [] z, 255::UTINYINT aa, 2::TINYINT ab, 18446744073709551615::UBIGINT ac, '{\"a\":1}'::JSON ad, NULL ae",
    "SELECT 12345678.9::DOUBLE af, 0.1::DOUBLE ag, 1/3 ah, 2.5e-7::DOUBLE ai, 1e21::DOUBLE aj, 1e-7::DOUBLE ak, "
    "123456789.123::DOUBLE al, 'nan'::FLOAT am, 1.0e100::DOUBLE an, 100.0::DOUBLE ao, TIMESTAMP '2026-01-02 03:04:05' ap",
    "SELECT INTERVAL '1 month 2 days 03:04:05.5' aq, [1.5, NULL] ar, {'z': NULL} as_, INTERVAL '-90 minutes' at, "
    "INTERVAL '400 days 10 microseconds' au, 0.0000001::DECIMAL(18,10) av, 0::DECIMAL(9,3) aw, -12.5::DECIMAL(5,2) ax",
    "SELECT 'é<>\"\\' || chr(10) || chr(9) || chr(1) || chr(127) || chr(8232) || chr(128512) AS m, '\\x41'::BLOB AS q, "
    "[1, NULL, 3]::INTEGER[] li, ['x', NULL] ls, [[1, 2], [3]] ll, [{'a': 1}] lst",
    "SELECT 0.000001::DOUBLE a, 0.00001234::DOUBLE b, 1.5e16::DOUBLE c, 123456789012345680000.0::DOUBLE d, "
    "9007199254740993::DOUBLE e, 2.0::DOUBLE ** 70 f, 1.7976931348623157e308::DOUBLE g, 3.14159::DOUBLE h, -1e-5::DOUBLE i",
    "SELECT range AS n, range * 1.5 AS x, 'row ' || range AS s FROM range(5)",
    "SELECT sum(n_psms) FROM ptm_sites",
    "SELECT list(dataset_id) FROM datasets",
    "SELECT current_setting('enable_external_access') AS eea",
    "SELECT * FROM duckdb_settings() WHERE name IN ('enable_external_access', 'threads') ORDER BY name",
    "SELECT table_name FROM information_schema.tables ORDER BY 1",
    "SELECT * FROM duckdb_tables() ORDER BY table_name LIMIT 3",
    "SELECT 'ünïcödé ' || repeat('x', 3) AS t, '😀😀' AS e",
]:
    call("sql", query=sql)

# caps
call("sql", query="SELECT range FROM range(10)", max_rows=3)
call("sql", query="SELECT range FROM range(10)", max_rows=10)
call("sql", query="SELECT range FROM range(10)", max_rows=0)
call("sql", query="SELECT range FROM range(10)", max_rows=-1)
call("sql", query="SELECT range FROM range(10)", max_rows=-5)
call("sql", query="SELECT range FROM range(2000)")
call("sql", query="SELECT range FROM range(1000)")
call("sql", query="SELECT range FROM range(1001)")
call("sql", query="SELECT range FROM range(5000)", max_rows=5000)
call("sql", query="SELECT * FROM psms ORDER BY psm_id", max_rows=2)
small = {"row_cap": 3, "char_cap": 60, "timeout_seconds": 7}
call("sql", server=small, query="SELECT range FROM range(10)")
call("sql", server=small, query="SELECT range FROM range(10)", max_rows=100)
call("sql", server=small, query="SELECT psm_id, usi, peptidoform FROM psms ORDER BY psm_id")
call("sql", server=small, query="SELECT 'ünïcödé😀' AS a, 'x' AS b FROM range(5)")
call("describe", server=small, target="psms")
call("search", server=small, query="P", kind="protein", limit=2)
chars = {"char_cap": 200}
call("sql", server=chars, query="SELECT [1.5, NULL] AS l, {'k': 'v'} AS s, 1.0e-5 AS d, NULL AS n, TRUE AS b FROM range(20)")
call("sql", server=chars, query="SELECT DATE '2026-01-02' AS d, TIMESTAMP '2026-01-02 03:04:05.25' AS t, 1.50::DECIMAL(4,2) AS m FROM range(20)")
call("sql", server=chars, query="SELECT [DATE '2026-01-02'] AS d, [1.50::DECIMAL(4,2)] AS m, ['it''s'] AS s FROM range(20)")
call("sql", server={"char_cap": 10}, query="SELECT 'abcdefghijklmnop' AS x")
call("sql", server={"row_cap": 0}, query="SELECT 1")
# the watchdog: stopped at the deadline, and the connection still answers
slow = {"timeout_seconds": 1}
call("sql", server=slow, query=SLOW)
call("sql", server=slow, query="SELECT count(*) FROM datasets")
call("sql", server={"timeout_seconds": 0.5}, query=SLOW)

if real:
    # aging's benchmark, in the style of design/QUESTIONS.md: the questions an agent is actually asked
    for value in ["LMNA", "P02545", "GDF15", "progerin", "PXD036557", "skeletal muscle", "mitochondri", "lysosom",
                  "Phospho", "Acetyl", "GG", "Citrullination", "Oxidation on M", "SNHMQELSELLQ", "LMNA_HUMAN",
                  "Mus musculus", "Rattus", "DIA", "TMT", "plasma", "brain", "fibroblast", "progeria", "H3C1"]:
        call("search", query=value)
    for sql in [
        # A1/A5/A8
        "SELECT dataset_id, organisms, acquisition, quant_method, labelling, n_samples, n_psms_1pct, n_peptidoforms_1pct, n_protein_groups_1pct FROM dataset_overview ORDER BY dataset_id",
        "SELECT acquisition, quant_method, count(*) FROM datasets GROUP BY 1, 2 ORDER BY 1, 2",
        "SELECT dataset_id FROM datasets WHERE list_contains(organisms, 'Mus musculus') ORDER BY 1",
        # A9/A10
        "SELECT dataset_id, enrichment, labelling FROM datasets WHERE enrichment <> ['none'] OR labelling <> 'none' ORDER BY 1",
        # B1/B3/B5
        "SELECT s.dataset_id, count(*) AS n, min(a.age_years), max(a.age_years), count(*) FILTER (WHERE a.age_is_lower_bound) AS lower_bounds FROM samples s JOIN sample_ages a USING (sample_id) GROUP BY 1 ORDER BY 1",
        "SELECT organism_part, organism_part_name, count(*) FROM samples GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20",
        "SELECT disease_name, count(*) FROM samples GROUP BY 1 ORDER BY 2 DESC",
        "SELECT * FROM samples WHERE dataset_id = 'PXD036557' ORDER BY sample_id LIMIT 5",
        "SELECT sample_id, name, value FROM sample_characteristics WHERE lower(value) LIKE '%muscle%' ORDER BY 1, 2 LIMIT 20",
        # C1/C4/C6/C8
        "SELECT dataset_id, protein_group_id, q_value, unique_peptides FROM protein_groups_1pct WHERE list_contains(protein_accessions, 'P02545') ORDER BY dataset_id, protein_group_id",
        "SELECT pg.dataset_id, count(qv.value) AS quantified, count(*) AS n FROM protein_groups_1pct pg JOIN quant_values qv ON qv.dataset_id = pg.dataset_id AND qv.feature_id = pg.protein_group_id WHERE list_contains(pg.protein_accessions, 'P02545') GROUP BY 1 ORDER BY 1",
        "SELECT dataset_id, peptidoform, best_q_value, is_unique, is_isoform_specific FROM peptidoforms_1pct WHERE list_contains(protein_accessions, 'P02545') ORDER BY dataset_id, peptidoform LIMIT 50",
        "SELECT * FROM protein_datasets WHERE protein_accession = 'P02768' ORDER BY dataset_id",
        "SELECT * FROM protein_index WHERE gene = 'LMNA'",
        "SELECT detection_type, count(*) FROM quant_values WHERE dataset_id = 'PXD036557' GROUP BY 1 ORDER BY 1",
        # D6/D17: organelles (empty in this catalog: the guard must fire)
        "SELECT compartment, count(DISTINCT protein_accession) FROM protein_localizations GROUP BY 1",
        "SELECT o.* FROM organelle_age_summaries o ORDER BY 1 LIMIT 5",
        "SELECT a.* FROM age_effects a JOIN protein_localizations l ON l.protein_accession = a.feature_id LIMIT 5",
        # K1/E: PTM stoichiometry and sites
        "SELECT dataset_id, count(*) AS n, avg(modified_fraction_count) AS mean_fraction FROM ptm_stoichiometry GROUP BY 1 ORDER BY 1",
        "SELECT modification_name, count(*) AS sites, count(DISTINCT dataset_id) AS datasets FROM ptm_sites GROUP BY 1 ORDER BY 2 DESC LIMIT 15",
        "SELECT * FROM ptm_sites WHERE protein_accession = 'P02545' ORDER BY dataset_id, position LIMIT 20",
        "SELECT * EXCLUDE (modification_names), list_sort(modification_names) AS names FROM ptm_sites_by_chemistry WHERE protein_accession = 'P02545' ORDER BY ALL LIMIT 20",
        # G1: trust
        "SELECT code, severity, count(*) FROM findings GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2",
        "SELECT dataset_id, name, value FROM metrics WHERE name LIKE '%id_rate%' ORDER BY 1 LIMIT 20",
        "SELECT * FROM catalog_checks WHERE NOT ok",
        # pep traps
        "SELECT dataset_id, median(pep) AS median_pep FROM psms_1pct GROUP BY 1 ORDER BY 1",
        "SELECT dataset_id, count(*) FILTER (WHERE pep < 0.01) FROM psms_1pct GROUP BY 1 ORDER BY 1",
        # J traps
        "SELECT count(*) FROM sample_ages WHERE age_years >= 100",
        "SELECT * FROM age_effects WHERE feature_id = 'P02545'",
        "SELECT count(*) FROM psms",
        "SELECT * FROM psms LIMIT 1500",
        "SELECT * FROM proteins LIMIT 3",
        "SELECT gene_symbol, outcome, count(*) FROM gene_resolutions GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2 LIMIT 10",
    ]:
        call("sql", query=sql)
    call("sql", query="SELECT protein_accession, count(*) FROM proteins GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 5")
    call("sql", query=SLOW, server={"timeout_seconds": 2})
catalog_id = q("SELECT catalog_id FROM catalog_meta")[0][0]
con.close()

# --------------------------------------------------------------------------------------------------
# answering it
# --------------------------------------------------------------------------------------------------

servers: dict[str, CatalogServer] = {}
results = []
for c in calls:
    key = json.dumps(c["server"], sort_keys=True)
    if key not in servers:
        servers[key] = CatalogServer(catalog, **c["server"])
    server = servers[key]
    method = getattr(server, c["tool"])
    entry = dict(c)
    try:
        try:
            result = method(**c["args"])
        except DataRepoError as exc:
            result = _error_payload(exc)
        entry["text"] = pydantic_core.to_json(result, fallback=str, indent=2).decode()
    except Exception as exc:  # noqa: BLE001 - recorded, not raised: the SDK reports it as a tool error
        entry["exception"] = type(exc).__name__
        entry["message"] = str(exc)
    results.append(entry)
    # Python's server holds one catalog per process, and DuckDB refuses a second connection with another
    # config to the same file; one server is kept open at a time.
    if len(servers) > 1:
        for k in list(servers):
            if k != key:
                servers.pop(k).close()

for s in servers.values():
    s.close()
about = {"catalog": catalog, "catalog_id": catalog_id, "datarepo": __import__("datarepo").__version__, "duckdb": duckdb.__version__,
         "pydantic_core": pydantic_core.__version__, "calls": len(results)}
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"_about": about, "calls": results}, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(f"{len(results)} calls -> {out_path}")
