"""Scratch (1.5.0): explain three catalog differences.
1. the six deposits whose protein_genes collapse: their searched databases, and which serving artefact covered each, with
   that artefact's requested_for;
2. peptidoform_ions vs peptidoforms_1pct per deposit, and ion rows whose peptidoform is not in the view;
3. which deposit has no deposit_records row.
Reads both catalogs and aging's store read-only."""
import json, os, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:/aging_data/repo/catalogs/catalog-75e1c0c82f8dc965.duckdb"
latest = json.load(open(os.path.join(HERE, "catalogs", "latest.json"), encoding="utf-8"))
NEW = os.path.join(HERE, "catalogs", latest["catalog"]).replace("\\", "/")
o = duckdb.connect(OLD, read_only=True)
n = duckdb.connect(NEW, read_only=True)

print("== 1. gene resolutions")
six = ["PXD005035", "PXD005123", "PXD006578", "PXD006589", "PXD025315", "PXD027895"]
print(" dataset_databases columns:", [r[0] for r in n.execute("describe dataset_databases").fetchall()])
print(" gene_resolutions columns:", [r[0] for r in n.execute("describe gene_resolutions").fetchall()][:12])
for d in six:
    print(" ", d, n.execute(f"select * from dataset_databases where dataset_id = '{d}'").fetchall())
arts = {}
for aid, path, inputs in o.execute("select artefact_id, path, inputs from catalog_engine_artefacts where engine = 'logs.resolve_genes'").fetchall():
    r = json.load(open(path + "/run.json", encoding="utf-8"))
    arts[aid] = (json.loads(inputs).get("search_database"), r["input_files"].get("search_database"), [x["dataset_id"] for x in r.get("requested_for", [])])
new_db = set()
for (inputs,) in n.execute("select inputs from catalog_engine_artefacts where engine = 'logs.resolve_genes'").fetchall():
    new_db.add(json.loads(inputs).get("search_database"))
for aid, (sha, path, req) in arts.items():
    if sha not in new_db:
        print("  serving artefact with no scratch counterpart:", aid, os.path.basename(path or ""), "requested_for", req)

print()
print("== 2. ions vs view")
rows = n.execute("""
  with v as (select dataset_id, count(*) c from peptidoforms_1pct group by 1),
       i as (select dataset_id, count(*) c from peptidoform_ions group by 1)
  select coalesce(v.dataset_id, i.dataset_id), v.c, i.c from v full join i using (dataset_id)
  where v.c is distinct from i.c order by 1""").fetchall()
print("  deposits where they differ:", rows)
print("  ion columns:", [r[0] for r in n.execute("describe peptidoform_ions").fetchall()])

print()
print("== 3. deposit records")
print("  deposits:", n.execute("select count(*) from deposits").fetchone()[0])
print("  deposits with no record:", n.execute("select accession from deposits where accession not in (select accession from deposit_records)").fetchall())
