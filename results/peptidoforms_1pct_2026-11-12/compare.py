"""1.5.0 item 11: on a scratch folder catalog of four real 0.0.17 bundles, peptidoforms_1pct under the recorded rule
against (a) the ingest's own rows (peptidoform_ions' distinct peptidoforms), (b) a recount from each bundle's
peptidoforms.parquet in plain Python under mzLib's rule, (c) item 3's catalog of the same bundles (q-value rule)."""
import glob, json, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
new = json.load(open(r"F:/datarepo_scratch_150/catalog_item11/latest.json"))
old = json.load(open(r"F:/datarepo_scratch_150/catalog_item3/latest.json"))
def path(folder, pointer):
    return f"{folder}/{pointer.get('catalog') or pointer.get('file') or pointer.get('path')}"
newc = duckdb.connect(path("F:/datarepo_scratch_150/catalog_item11", new), read_only=True)
oldc = duckdb.connect(path("F:/datarepo_scratch_150/catalog_item3", old), read_only=True)
print("new catalog", newc.execute("SELECT catalog_id, catalog_version FROM catalog_meta").fetchone())
print("old catalog", oldc.execute("SELECT catalog_id, catalog_version FROM catalog_meta").fetchone())
rows = newc.execute("SELECT dataset_id, bundle_id, confidence_rule, n_peptidoforms_1pct FROM dataset_overview ORDER BY 1").fetchall()
print(f"{'dataset':10} {'rule':14} {'view':>8} {'ions':>8} {'recount':>8} {'q-rule(1.4.5 view)':>20}")
ok = True
for ds, bundle, rule, n in rows:
    view_ids = {r[0] for r in newc.execute("SELECT peptidoform_id FROM peptidoforms_1pct WHERE dataset_id = ?", [ds]).fetchall()}
    ions = {r[0] for r in newc.execute("SELECT DISTINCT peptidoform_id FROM peptidoform_ions WHERE dataset_id = ?", [ds]).fetchall()}
    pq = glob.glob(f"F:/datarepo_scratch_150/store_item3/{ds}/{bundle}/**/peptidoforms.parquet", recursive=True)[0]
    col = {"pep_q_value": "best_pep_q_value", "q_value_notch": "best_q_value_notch", "q_value": "best_q_value"}[rule]
    recount = {r[0] for r in duckdb.execute(f"SELECT peptidoform_id, target_decoy, {col} FROM read_parquet('{pq}')").fetchall()
               if r[1] == "target" and r[2] is not None and r[2] == r[2] and r[2] < 0.01}
    qrule = oldc.execute("SELECT n_peptidoforms_1pct FROM dataset_overview WHERE dataset_id = ?", [ds]).fetchone()[0]
    same = view_ids == recount and len(view_ids) == n and (not ions or ions == view_ids)
    ok &= same
    print(f"{ds:10} {rule:14} {n:>8,} {len(ions):>8,} {len(recount):>8,} {qrule:>20,}  {'same' if same else 'DIFFERENT'}")
print("ALL SAME" if ok else "SOME DIFFER")
