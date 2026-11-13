"""Scratch (1.5.0): compare the scratch folder catalog (built from the 192 re-ingested bundles and the replayed engines)
with aging's serving catalog 75e1c0c82f8dc965, on the deposits both hold. Checks (pass/fail by kind), engine artefacts
per engine, engine coverage per deposit (gene resolutions, protein localizations), and dataset_overview's counts.
Reads both catalogs read-only."""
import json, os, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:/aging_data/repo/catalogs/catalog-75e1c0c82f8dc965.duckdb"
latest = json.load(open(os.path.join(HERE, "catalogs", "latest.json"), encoding="utf-8"))
NEW = os.path.join(HERE, "catalogs", latest["catalog"]).replace("\\", "/")
print("scratch catalog", latest["catalog_id"], "release", latest["release_id"], "format", latest["catalog_version"], "builder", latest["builder_version"])
o = duckdb.connect(OLD, read_only=True)
n = duckdb.connect(NEW, read_only=True)


def q(c, sql):
    return c.execute(sql).fetchall()


print("\n== checks: kind, ok, count (old | new)")
print(" old:", q(o, "select kind, ok, count(*) from catalog_checks group by all order by all"))
print(" new:", q(n, "select kind, ok, count(*) from catalog_checks group by all order by all"))
for r in q(n, "select name, kind, observed, expected, left(detail, 300) from catalog_checks where not ok"):
    print("  FAILED:", r)

print("\n== engine artefacts (old | new)")
print(" old:", q(o, "select engine, count(*) from catalog_engine_artefacts group by 1 order by 1"))
print(" new:", q(n, "select engine, count(*) from catalog_engine_artefacts group by 1 order by 1"))

both = [r[0] for r in q(n, "select dataset_id from datasets")]
both = [d for d in both if q(o, f"select count(*) from datasets where dataset_id = '{d}'")[0][0]]
print("\n== deposits in both:", len(both))


def per(c, sql):
    return dict(q(c, sql))


for name, sql in [
    ("protein_genes rows", "select dataset_id, count(*) from protein_genes group by 1"),
    ("protein_localizations rows", "select dataset_id, count(*) from protein_localizations group by 1"),
    ("peptidoforms_1pct rows", "select dataset_id, count(*) from peptidoforms_1pct group by 1"),
    ("protein_groups_1pct rows", "select dataset_id, count(*) from protein_groups_1pct group by 1"),
]:
    try:
        a, b = per(o, sql), per(n, sql)
    except Exception as e:  # a table one side lacks
        print(f"  {name}: {e}".splitlines()[0])
        continue
    diff = [(d, a.get(d), b.get(d)) for d in both if a.get(d) != b.get(d)]
    print(f"  {name}: deposits differing {len(diff)} of {len(both)}; old total {sum(a.get(d, 0) for d in both)}, new total {sum(b.get(d, 0) for d in both)}")
    for x in diff[:8]:
        print("     ", x)

print("\n== dataset_overview columns only in new:", sorted(set(r[0] for r in q(n, "describe dataset_overview")) - set(r[0] for r in q(o, "describe dataset_overview"))))
print("== tables only in new:", sorted(set(r[0] for r in q(n, "select table_name from information_schema.tables")) - set(r[0] for r in q(o, "select table_name from information_schema.tables"))))
print("== tables only in old:", sorted(set(r[0] for r in q(o, "select table_name from information_schema.tables")) - set(r[0] for r in q(n, "select table_name from information_schema.tables"))))
print("== confidence rules:", q(n, "select confidence_rule, count(*) from dataset_overview group by 1"))
print("== quant_scale:", q(n, "select quant_scale, count(*) from dataset_overview group by 1 order by 1"))
for t in ["deposit_records", "deposit_contacts", "deposit_references", "shared_raw_files", "isobaric_channels", "peptidoform_ions"]:
    try:
        print(f"== {t}:", q(n, f"select count(*) from {t}")[0][0])
    except Exception as e:
        print(f"== {t}: {str(e).splitlines()[0]}")
