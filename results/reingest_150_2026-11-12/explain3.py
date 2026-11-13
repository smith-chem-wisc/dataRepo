"""Scratch (1.5.0): close the remaining differences.
a. the four one-row peptidoform losses: the new key whose row holds two old keys (a merge);
b. per deposit, every finding code whose row count moves (not just codes that appear or go);
c. metrics: the change equals the payload's rows (source qc_payload.json), and no other metrics row moves in count;
d. samples: the samples that go are exactly those whose only assays are design `empty` channels;
e. bytes: the old bundles' size beside the new, and the serial seconds.
Reads aging's store (read-only) and the scratch store."""
import collections, csv, os, re, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:\aging_data\repo\store"
NEW = os.path.join(HERE, "store")
deps = {d["accession"]: d for d in csv.DictReader(open(os.path.join(HERE, "compare_deposits.tsv"), encoding="utf-8"), delimiter="\t")}
done = {a: d for a, d in deps.items() if d["new_bundle"]}


def o(acc):
    return os.path.join(OLD, acc, deps[acc]["old_bundle"]).replace("\\", "/")


def n(acc):
    return os.path.join(NEW, acc, deps[acc]["new_bundle"]).replace("\\", "/")


print("== a. merges")
for acc in ["PXD018999", "PXD025240", "PXD057545", "PXD077298"]:
    r = duckdb.sql(f"""
      with a as (select peptidoform, n_psms, target_decoy, unnest(engine_full_sequences) e from '{o(acc)}/peptidoforms.parquet'),
           b as (select peptidoform, n_psms, target_decoy, unnest(engine_full_sequences) e from '{n(acc)}/peptidoforms.parquet')
      select b.peptidoform, any_value(b.n_psms), any_value(b.target_decoy), list(distinct a.peptidoform || ' n=' || a.n_psms)
      from b join a on a.e = b.e group by b.peptidoform having count(distinct a.peptidoform) > 1""").fetchall()
    for x in r:
        print(f"  {acc}: new {x[0]} n={x[1]} {x[2]} <- {x[3]}")

print()
print("== b. finding codes whose count moves (code: deposits, total change)")
moves = collections.defaultdict(lambda: [0, 0])
for acc in done:
    fo = collections.Counter(c for (c,) in duckdb.sql(f"select code from '{o(acc)}/findings.parquet'").fetchall())
    fn = collections.Counter(c for (c,) in duckdb.sql(f"select code from '{n(acc)}/findings.parquet'").fetchall())
    for c in set(fo) | set(fn):
        if fo[c] != fn[c]:
            moves[c][0] += 1
            moves[c][1] += fn[c] - fo[c]
for c, (k, t) in sorted(moves.items()):
    print(f"  {c}: {k} deposits, {t:+d} rows")

print()
print("== c. metrics")
bad = []
for acc in done:
    mo = collections.Counter((s, nm) for s, nm in duckdb.sql(f"select source, name from '{o(acc)}/metrics.parquet'").fetchall())
    mn = collections.Counter((s, nm) for s, nm in duckdb.sql(f"select source, name from '{n(acc)}/metrics.parquet'").fetchall())
    diff = {k: mn[k] - mo[k] for k in set(mo) | set(mn) if mn[k] != mo[k]}
    if any(k[0] != "qc_payload.json" for k in diff):
        bad.append((acc, diff))
print("  deposits whose metrics move outside qc_payload.json rows:", len(bad))
for acc, d in bad[:10]:
    print("   ", acc, d)
dchg = collections.Counter()
for acc in done:
    a = duckdb.sql(f"select definition_id, count(*) from '{o(acc)}/metrics.parquet' where source <> 'qc_payload.json' group by 1").fetchall()
    b = duckdb.sql(f"select definition_id, count(*) from '{n(acc)}/metrics.parquet' where source <> 'qc_payload.json' group by 1").fetchall()
    if sorted(a) != sorted(b):
        dchg[tuple(sorted(set(x for x, _ in b) - set(x for x, _ in a)))] += 1
print("  deposits whose non-payload metrics cite new definition ids:", dict(dchg))

print()
print("== d. samples")
for acc in sorted(done):
    so = duckdb.sql(f"select count(*) from '{o(acc)}/samples.parquet'").fetchone()[0]
    sn = duckdb.sql(f"select count(*) from '{n(acc)}/samples.parquet'").fetchone()[0]
    if so == sn:
        continue
    gone = duckdb.sql(f"select sample_id from '{o(acc)}/samples.parquet' except select sample_id from '{n(acc)}/samples.parquet'").fetchall()
    gone = {g for (g,) in gone}
    # in the new bundle, the assays the old bundle tied to those samples
    olda = duckdb.sql(f"select assay_id, sample_id from '{o(acc)}/assays.parquet'").fetchall()
    newa = dict(duckdb.sql(f"select assay_id, design_sample_type from '{n(acc)}/assays.parquet'").fetchall())
    types = collections.Counter(newa.get(a) for a, s in olda if s in gone)
    kept_on_empty = duckdb.sql(f"select count(*) from '{n(acc)}/assays.parquet' where design_sample_type = 'empty' and sample_id is not null").fetchone()[0]
    print(f"  {acc}: {so}->{sn}, {len(gone)} gone, their assays now typed {dict(types)}; empty assays still with a sample: {kept_on_empty}")

print()
print("== e. bytes and seconds")


def size(p):
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)


ob = sum(size(o(a)) for a in done)
nb = sum(size(n(a)) for a in done)
ions = sum(os.path.getsize(os.path.join(n(a), "peptidoform_ions.parquet")) for a in done if os.path.exists(os.path.join(n(a), "peptidoform_ions.parquet")))
secs = sum(int(d["secs"]) for d in done.values() if d["secs"])
print(f"  old bundles {ob/1e9:.1f} GB, new {nb/1e9:.1f} GB (+{(nb-ob)/1e9:.1f}); peptidoform_ions files {ions/1e9:.1f} GB")
print(f"  serial seconds {secs} = {secs/3600:.1f} h; per GB of source", end=" ")
gb = sum(float(r[5]) for r in (l.rstrip('\n').split('\t') for l in open(os.path.join(HERE, 'baseline.tsv'), encoding='utf-8').readlines()[1:]) if r[0] in done)
print(f"{secs/gb:.0f} s ({gb:.0f} GB)")
