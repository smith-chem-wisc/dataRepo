"""G94 step 1 measurement (scratch, never shipped): a catalog of VIEWS over aging's store, read-only on the store.

Picks the newest bundle per deposit (bundle.json mtime) on the current schema, builds a DuckDB file in scratch holding
only views over the bundles' Parquet (PSMs excluded) plus one materialised corpus index, and measures build time,
file size, query times, the sandbox (enable_external_access=false + allowed_directories) and relative paths
(file_search_path).
"""
import glob, json, os, sys, time
import duckdb

STORE = r"F:\aging_data\repo\store"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
cat = os.path.join(OUT, "catalog-views.duckdb")
for f in (cat, cat + ".wal"):
    if os.path.exists(f):
        os.remove(f)

# newest bundle per deposit, current schema only
latest = {}
for bj in glob.glob(os.path.join(STORE, "PXD*", "*", "bundle.json")):
    d = os.path.dirname(bj)
    m = json.load(open(bj, encoding="utf-8"))
    if str(m.get("schema_version")) != "0.0.15":
        continue
    acc = os.path.basename(os.path.dirname(d))
    t = os.path.getmtime(bj)
    if acc not in latest or t > latest[acc][0]:
        latest[acc] = (t, d)
bundles = sorted(d for _, d in latest.values())
print(f"bundles (newest per deposit, schema 0.0.15): {len(bundles)}")

tables = {}
for d in bundles:
    for p in glob.glob(os.path.join(d, "*.parquet")):
        tables.setdefault(os.path.splitext(os.path.basename(p))[0], []).append(p)
size = {t: sum(os.path.getsize(p) for p in ps) for t, ps in tables.items()}
print("tables:", len(tables), "| parquet GB total:", round(sum(size.values()) / 1e9, 2),
      "| psms GB:", round(size.get("psms", 0) / 1e9, 2), "| peptidoforms GB:", round(size.get("peptidoforms", 0) / 1e9, 2))
missing = {t: len(bundles) - len(ps) for t, ps in tables.items() if len(ps) != len(bundles)}
print("tables absent from some bundles:", missing or "none")

def rel(p):
    return os.path.relpath(p, STORE).replace("\\", "/")

t0 = time.time()
con = duckdb.connect(cat)
con.execute(f"SET file_search_path = '{STORE}'")  # views bind their files when created
for t, ps in sorted(tables.items()):
    if t == "psms":
        continue  # rule 3: PSMs never in a catalog
    files = ", ".join("'" + rel(p) + "'" for p in sorted(ps))
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{rel(ps[0])}')").fetchall()]
    seg = "regexp_extract(filename, '([^\\\\/]+)[\\\\/]([^\\\\/]+)[\\\\/][^\\\\/]+$', {})"
    ids = ("" if "dataset_id" in cols else seg.format(1) + " AS dataset_id, ") + seg.format(2) + " AS bundle_id"
    con.execute(f'CREATE VIEW "{t}" AS SELECT * EXCLUDE (filename), {ids} FROM read_parquet([{files}], filename = true)')
t_views = time.time() - t0
con.execute(f"SET file_search_path = '{STORE}'")
t1 = time.time()
# one corpus-wide index, materialised: accession -> datasets, from the answers tier
con.execute("""
    CREATE TABLE protein_index AS
    SELECT accession, count(DISTINCT dataset_id) AS n_datasets, list(DISTINCT dataset_id ORDER BY dataset_id) AS datasets
    FROM (SELECT dataset_id, unnest(protein_accessions) AS accession FROM protein_groups)
    GROUP BY accession
""")
t_index = time.time() - t1
n_idx = con.execute("SELECT count(*) FROM protein_index").fetchone()[0]
con.close()
print(f"build: views {t_views:.1f} s, protein_index {t_index:.1f} s ({n_idx:,} accessions); file {os.path.getsize(cat)/1e6:.1f} MB")

# queries through the views, relative paths resolved by file_search_path
con = duckdb.connect(cat, read_only=True)
con.execute(f"SET file_search_path = '{STORE}'")
def timed(label, sql):
    t = time.time(); r = con.execute(sql).fetchall(); print(f"  {label}: {time.time()-t:.2f} s -> {r[:3]}")
timed("protein_groups rows", "SELECT count(*) FROM protein_groups")
timed("peptidoforms rows", "SELECT count(*) FROM peptidoforms")
timed("one protein across datasets (index)", "SELECT n_datasets FROM protein_index WHERE accession = 'P04406'")
timed("quant_values rows", "SELECT count(*) FROM quant_values")
timed("one dataset's quant values (file pruning?)", "SELECT count(*) FROM quant_values WHERE dataset_id = 'PXD058082'")
timed("one dataset's peptidoforms", "SELECT count(*) FROM peptidoforms WHERE dataset_id = 'PXD058082'")
timed("one protein's quant values across datasets",
      "SELECT count(*), count(DISTINCT q.dataset_id) FROM quant_values q JOIN protein_groups g "
      "ON q.dataset_id = g.dataset_id AND q.feature_type = 'protein_group' AND q.feature_id = g.protein_group_id "
      "WHERE list_contains(g.protein_accessions, 'P04406')")
timed("bundle_id sample", "SELECT DISTINCT dataset_id, bundle_id FROM quant_values WHERE dataset_id = 'PXD058082'")
plan = con.execute("EXPLAIN ANALYZE SELECT count(*) FROM quant_values WHERE dataset_id = 'PXD058082'").fetchall()[0][1]
print("  plan lines mentioning files:", [l.strip() for l in plan.splitlines() if "ile" in l][:6])
con.close()

# the sandbox: D14's enable_external_access=false, with and without allowed_directories
for label, cfg in [("external access off", {"enable_external_access": False}),
                   ("off + allowed_directories=[store]", {"enable_external_access": False, "allowed_directories": [STORE + os.sep]})]:
    try:
        c = duckdb.connect(cat, read_only=True, config=cfg)
        c.execute(f"SET file_search_path = '{STORE}'")
        n = c.execute("SELECT count(*) FROM samples").fetchone()[0]
        try:
            c.execute("SELECT count(*) FROM read_csv_auto('C:/Windows/win.ini')").fetchone()
            outside = "READ a file outside the store"
        except Exception as e:
            outside = f"outside the store refused ({type(e).__name__})"
        print(f"  sandbox [{label}]: views OK ({n} samples); {outside}")
        c.close()
    except Exception as e:
        print(f"  sandbox [{label}]: {type(e).__name__}: {str(e)[:160]}")
