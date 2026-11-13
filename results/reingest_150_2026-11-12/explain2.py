"""Scratch (1.5.0): look inside the differences explain.py found.
1. the four deposits losing one peptidoform: which keys go/come (old store vs scratch), and whether two old keys merge;
2. the 15 deposits losing unresolved_modifications: the old finding's message;
3. the 22 deposits gaining confidence_rule_fewer_peptides: the new message;
4. isobaric deposits: qc_payload metrics names, and whether protein_groups_1pct_whole_search is there;
5. PXD057502's new findings.
Reads aging's store (read-only) and the scratch store."""
import csv, json, os, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:\aging_data\repo\store"
NEW = os.path.join(HERE, "store")
deps = {d["accession"]: d for d in csv.DictReader(open(os.path.join(HERE, "compare_deposits.tsv"), encoding="utf-8"), delimiter="\t")}


def o(acc):
    return os.path.join(OLD, acc, deps[acc]["old_bundle"]).replace("\\", "/")


def n(acc):
    return os.path.join(NEW, acc, deps[acc]["new_bundle"]).replace("\\", "/")


print("== 1. peptidoform keys")
for acc in ["PXD018999", "PXD025240", "PXD057545", "PXD077298"]:
    q = f"""
    with a as (select peptidoform, engine_full_sequences, target_decoy from '{o(acc)}/peptidoforms.parquet'),
         b as (select peptidoform, engine_full_sequences, target_decoy from '{n(acc)}/peptidoforms.parquet')
    select (select count(*) from a where peptidoform not in (select peptidoform from b)) gone,
           (select count(*) from b where peptidoform not in (select peptidoform from a)) came
    """
    gone, came = duckdb.sql(q).fetchone()
    print(f"  {acc}: keys gone {gone}, keys new {came}")
    # keys that are new: show one, and the old keys sharing its engine full sequence
    ex = duckdb.sql(f"""
      with a as (select peptidoform, engine_full_sequences, target_decoy, n_psms from '{o(acc)}/peptidoforms.parquet'),
           b as (select peptidoform, engine_full_sequences, target_decoy, n_psms from '{n(acc)}/peptidoforms.parquet'),
           ga as (select * from a where peptidoform not in (select peptidoform from b)),
           nb as (select * from b where peptidoform not in (select peptidoform from a)),
           ae as (select peptidoform, n_psms, unnest(engine_full_sequences) e from ga),
           be as (select peptidoform, n_psms, target_decoy, unnest(engine_full_sequences) e from nb),
           j as (select be.peptidoform np, be.n_psms nn, be.target_decoy td, list(distinct ae.peptidoform || ' n=' || ae.n_psms) olds
                 from be join ae on be.e = ae.e group by 1, 2, 3)
      select np, nn, td, olds from j order by len(olds) desc limit 2""").fetchall()
    for r in ex:
        print("     new:", r[0][:140], "|", r[2], "n=", r[1])
        print("     old keys sharing an engine sequence:", [x[:140] for x in r[3]])
    unmatched = duckdb.sql(f"""
      with a as (select peptidoform, engine_full_sequences from '{o(acc)}/peptidoforms.parquet'),
           b as (select peptidoform, engine_full_sequences from '{n(acc)}/peptidoforms.parquet'),
           ga as (select peptidoform, unnest(engine_full_sequences) e from a where peptidoform not in (select peptidoform from b)),
           nb as (select peptidoform, unnest(engine_full_sequences) e from b where peptidoform not in (select peptidoform from a))
      select (select count(distinct peptidoform) from ga where e not in (select e from nb)),
             (select count(distinct peptidoform) from nb where e not in (select e from ga))""").fetchone()
    print("     gone keys with no new key on their engine sequence:", unmatched[0], "; new keys with no gone one:", unmatched[1])

print()
print("== 2. unresolved_modifications that go")
for acc, d in sorted(deps.items()):
    if "unresolved_modifications" in d["findings_gone"].split():
        m = duckdb.sql(f"select message from '{o(acc)}/findings.parquet' where code='unresolved_modifications'").fetchall()
        print(f"  {acc} {d['metamorpheus']}:", " || ".join(x[0][:260] for x in m))

print()
print("== 3. confidence_rule_fewer_peptides / fallback")
for acc, d in sorted(deps.items()):
    nf = d["findings_new"].split()
    if "confidence_rule_fewer_peptides" in nf or "confidence_rule_fallback" in nf:
        m = duckdb.sql(f"select code, message from '{n(acc)}/findings.parquet' where code like 'confidence_rule%'").fetchall()
        for c, msg in m:
            print(f"  {acc} {d['metamorpheus']} {c}: {msg[:220]}")

print()
print("== 4. qc_payload metric names, isobaric vs label-free")
for acc, d in sorted(deps.items()):
    if not d["new_bundle"] or "qc_payload" not in d["sources_changed"].split():
        continue
    names = duckdb.sql(f"select name, count(*) from '{n(acc)}/metrics.parquet' where source='qc_payload.json' group by 1 order by 1").fetchall()
    print(f"  {acc} {d['quant_method']}:", dict(names))

print()
print("== 5. PXD057502 findings (new)")
for r in duckdb.sql(f"select code, severity, left(message, 200) from '{n('PXD057502')}/findings.parquet' order by 1").fetchall():
    print("  ", r)
