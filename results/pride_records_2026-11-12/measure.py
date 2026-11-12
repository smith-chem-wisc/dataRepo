"""1.5.0 item 12, scratch and read-only. (1) The PRIDE records `datarepo pride` kept for every deposit in aging's serving
catalog (F:/datarepo_scratch_150/pride_store), set beside our 2026-11-04 measurement of 193 (ptmQtl 061), applying the
catalog's rules (an empty string is NULL, PubMed 0 is NULL). (2) The three tables of a scratch catalog of eight bundles
(catalog_item12). (3) `shared_raw_files`, its SQL taken from that catalog, run over the runs of aging's serving catalog."""
import collections
import glob
import json
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8")
STORE = "F:/datarepo_scratch_150/pride_store2/_companion/pride"
ADDRESS = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def text(v):
    return v if isinstance(v, str) and v else None


records = {}
for acc_dir in sorted(glob.glob(f"{STORE}/*")):
    kept = sorted(glob.glob(f"{acc_dir}/*/record.json"))
    records[acc_dir.replace("\\", "/").rsplit("/", 1)[1]] = json.load(open(kept[-1], encoding="utf-8"))
print(f"(1) records kept: {len(records)}; found: {sum(r['found'] for r in records.values())}; "
      f"with an e-mail key: {sum('\"email\"' in json.dumps(r).lower() for r in records.values())}; with an e-mail address: "
      f"{sum(bool(ADDRESS.search(json.dumps(r))) for r in records.values())}; with one replaced by the marker: "
      f"{sum('[e-mail removed]' in json.dumps(r) for r in records.values())}")
found = [r for r in records.values() if r["found"]]
print("  lab heads per deposit:", dict(collections.Counter(len(r["lab_heads"]) for r in found)))
print("  submitters per deposit:", dict(collections.Counter(len(r["submitters"]) for r in found)))
print("  papers per deposit:", dict(sorted(collections.Counter(len(r["references"]) for r in found).items())))
heads = [c for r in found for c in r["lab_heads"]]
subs = [c for r in found for c in r["submitters"]]
refs = [x for r in found for x in r["references"]]
print(f"  lab-head ORCID: {sum(text(c['orcid']) is not None for c in heads)} of {len(heads)}; "
      f"submitter ORCID: {sum(text(c['orcid']) is not None for c in subs)} of {len(subs)}")
print(f"  papers {len(refs)}: PubMed 0 {sum(x['pubmed_id'] == 0 for x in refs)}, no citation line "
      f"{sum(text(x['reference_line']) is None for x in refs)}, no DOI {sum(text(x['doi']) is None for x in refs)}")
same = sum(1 for r in found if r["submitters"] and r["lab_heads"]
           and (text(r["submitters"][0]["last_name"]) or "").lower() == (text(r["lab_heads"][0]["last_name"]) or "").lower())
print(f"  submitter has the lab head's last name: {same} of {len(found)}")
head_ids = collections.Counter(c["pride_contact_id"] for c in heads)
sub_ids = collections.Counter(c["pride_contact_id"] for c in subs)
print(f"  lab-head contact ids recurring: {sum(1 for n in head_ids.values() if n > 1)}; "
      f"submitter accounts on more than one deposit: {sum(1 for n in sub_ids.values() if n > 1)}")
names = collections.Counter(c["last_name"] for c in heads)
print("  lab-head last name 'PhD':", names.get("PhD", 0))

cat = json.load(open("F:/datarepo_scratch_150/catalog_item12/latest.json"))
con = duckdb.connect("F:/datarepo_scratch_150/catalog_item12/" + cat["catalog"], read_only=True)
print(f"\n(2) scratch catalog {cat['catalog_id']} (eight bundles):")
for t in ("deposit_records", "deposit_contacts", "deposit_references"):
    print(f"  {t}: {con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]} rows")
print("  contacts by role:", con.execute("SELECT role, count(*) FROM deposit_contacts GROUP BY 1 ORDER BY 1").fetchall())
print("  references with pubmed / doi:", con.execute(
    "SELECT count(*), count(pubmed_id), count(doi) FROM deposit_references").fetchone())
print("  deposits joined through dataset_overview.accession:", con.execute(
    "SELECT count(DISTINCT o.dataset_id) FROM dataset_overview o JOIN deposit_records r ON r.accession = o.accession").fetchone()[0])
print("  shared_raw_files rows here:", con.execute("SELECT count(*) FROM shared_raw_files").fetchone()[0])
view_sql = con.execute("SELECT sql FROM duckdb_views() WHERE view_name = 'shared_raw_files'").fetchone()[0]
body = view_sql[view_sql.upper().index(" AS ") + 4:].rstrip(";")

serving = json.load(open("F:/aging_data/repo/catalogs/latest.json"))
aging = duckdb.connect("F:/aging_data/repo/catalogs/" + serving["catalog"], read_only=True)
print(f"\n(3) shared_raw_files over the runs of aging's serving catalog {serving['catalog_id']} "
      f"({aging.execute('SELECT count(*) FROM runs').fetchone()[0]:,} runs):")
rows = aging.execute(f"SELECT run_id, n_copies, other_run_ids, in_same_accession, in_other_accession FROM ({body}) ORDER BY run_id").fetchall()
for r in rows:
    print("  ", r)
print(f"  {len(rows)} runs; across deposits: {sum(r[4] for r in rows)}; within a deposit: {sum(r[3] for r in rows)}")
