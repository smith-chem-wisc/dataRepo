"""Scratch, read-only (1.5.0 build list item 3): the bundles feat/1.5.0's item-3 code wrote into
F:/datarepo_scratch_150/store_item3 (PXD058775, PXD057502, PXD011740, PXD034564). For each:
  - peptidoform_ions rows against ion_cells.tsv's count of passing target rows read straight from the file;
  - the peptidoforms holding ions against those passing the rule on the peptidoforms table (target, best value of the
    rule's column strictly below 0.01), both ways: item 11's view will be the second set;
  - ambiguous rows, the table's size, the bundle.json note and any peptidoform_ions finding;
  - every other table against the item-2 bundle where one exists (store_item2), else the served bundle with item 2's
    columns left out: nothing but the new table and its note should move."""
import csv
import json
import os
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
NEW, ITEM2, SERVED = "F:/datarepo_scratch_150/store_item3", "F:/datarepo_scratch_150/store_item2", "F:/aging_data/repo/store"
with open(os.path.join(HERE, "ion_cells.tsv"), encoding="utf-8", newline="") as handle:
    measured = {r["dataset"]: r for r in csv.DictReader(handle, delimiter=chr(9))}
with open("F:/aging_data/repo/catalogs/latest.json", encoding="utf-8") as handle:
    latest = json.load(handle)
cat = duckdb.connect(os.path.join("F:/aging_data/repo/catalogs", latest["catalog"]), read_only=True)
served = dict(cat.execute("SELECT dataset_id, bundle_id FROM catalog_bundles").fetchall())
cat.close()
con = duckdb.connect()
COLUMN = {"pep_q_value": "best_pep_q_value", "q_value_notch": "best_q_value_notch", "q_value": "best_q_value"}

for ds in sorted(os.listdir(NEW)):
    bundle = os.listdir(f"{NEW}/{ds}")[0]
    b = f"{NEW}/{ds}/{bundle}"
    rule = con.sql(f"SELECT confidence_rule FROM '{b}/datasets.parquet'").fetchone()[0]
    # The writer leaves out a table with no rows (as for sample_characteristics), so no file is an empty table.
    has_ions = os.path.exists(f"{b}/peptidoform_ions.parquet")
    ions_table = f"'{b}/peptidoform_ions.parquet'" if has_ions else "(SELECT NULL AS peptidoform_id, NULL AS full_sequence WHERE false)"
    ions = con.sql(f"SELECT count(*), count(*) FILTER (WHERE full_sequence LIKE '%|%'), count(DISTINCT peptidoform_id) FROM {ions_table}").fetchone()
    passing = f"SELECT peptidoform_id FROM '{b}/peptidoforms.parquet' WHERE target_decoy = 'target' AND {COLUMN[rule]} < 0.01"
    with_ions = f"SELECT DISTINCT peptidoform_id FROM {ions_table}"
    only_view = con.sql(f"SELECT count(*) FROM ({passing} EXCEPT {with_ions})").fetchone()[0]
    only_ions = con.sql(f"SELECT count(*) FROM ({with_ions} EXCEPT {passing})").fetchone()[0]
    size = os.path.getsize(f"{b}/peptidoform_ions.parquet") if has_ions else 0
    if not has_ions:
        print(f"\n{ds}: no peptidoform_ions.parquet (no row to write)")
    total = sum(os.path.getsize(os.path.join(b, f)) for f in os.listdir(b) if f.endswith(".parquet"))
    with open(f"{b}/bundle.json", encoding="utf-8") as handle:
        note = json.load(handle).get("peptidoform_ions")
    print(f"\n{ds} {bundle} rule {rule}")
    print(f"  peptidoform_ions rows {ions[0]:,} (ambiguous {ions[1]}, peptidoforms {ions[2]:,}); passing target rows in the file "
          f"(ion_cells.tsv) {int(measured[ds]['n_pass']):,}")
    print(f"  peptidoforms passing the rule but no ions: {only_view}; with ions but not passing: {only_ions}")
    print(f"  size {size / 1e6:.1f} MB of a {total / 1e6:.1f} MB bundle ({size / max(ions[0], 1):.0f} bytes/row)")
    print(f"  bundle.json peptidoform_ions: {note}")
    for code, message in con.sql(f"SELECT code, message FROM '{b}/findings.parquet' WHERE code LIKE 'peptidoform_ions%'").fetchall():
        print(f"  finding {code}: {message}")
    # Only the earlier bundle's columns are compared, so a column added since is left out.
    if os.path.isdir(f"{ITEM2}/{ds}"):
        a, against = f"{ITEM2}/{ds}/{os.listdir(f'{ITEM2}/{ds}')[0]}", "item 2"
    else:
        a, against = f"{SERVED}/{ds}/{served[ds]}", "served (1.4.5; item 1's key change and item 2's findings expected)"
    moved = []
    for table in sorted(f for f in os.listdir(b) if f.endswith(".parquet") and f != "peptidoform_ions.parquet"):
        name = table[:-8]
        cols = ", ".join(f'"{c}"' for c, *_ in con.sql(f"DESCRIBE SELECT * FROM '{a}/{table}'").fetchall())
        x = con.sql(f"SELECT count(*) FROM (SELECT {cols} FROM '{a}/{table}' EXCEPT ALL SELECT {cols} FROM '{b}/{table}')").fetchone()[0]
        y = con.sql(f"SELECT count(*) FROM (SELECT {cols} FROM '{b}/{table}' EXCEPT ALL SELECT {cols} FROM '{a}/{table}')").fetchone()[0]
        if x or y:
            moved.append(f"{name} ({x} only before, {y} only now)")
    print(f"  against {against}: {'every other table equal' if not moved else 'moved: ' + '; '.join(moved)}")
