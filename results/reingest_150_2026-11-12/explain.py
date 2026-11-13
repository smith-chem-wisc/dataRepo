"""Scratch (1.5.0): summarise compare_deposits.tsv / compare_tables.tsv so each difference can be mapped to a 1.5.0
build item. Prints: deposits per changed table with old->new, source roles that changed, finding codes gained/lost,
and the deposits with no peptidoform_ions table. Reads only the scratch folder and aging's store (read-only)."""
import collections, csv, os, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
deps = list(csv.DictReader(open(os.path.join(HERE, "compare_deposits.tsv"), encoding="utf-8"), delimiter="\t"))
rows = list(csv.DictReader(open(os.path.join(HERE, "compare_tables.tsv"), encoding="utf-8"), delimiter="\t"))

by = collections.defaultdict(dict)
for r in rows:
    by[r["accession"]][r["table"]] = (r["old_rows"], r["new_rows"])

done = [d for d in deps if d["new_bundle"]]
print(len(done), "re-ingested;", sum(1 for d in done if d["old_bundle"] == d["new_bundle"]), "kept their id")
print()
for t in ["peptidoforms", "samples", "metrics", "provenance_records", "findings"]:
    ch = [(a, v) for a, tv in by.items() for tt, v in tv.items() if tt == t and v[0] != v[1]]
    print(f"== {t}: {len(ch)} deposits")
    for a, (o, n) in sorted(ch, key=lambda x: x[0]):
        q = next(d for d in deps if d["accession"] == a)
        if t in ("peptidoforms", "samples"):
            print(f"   {a} {o}->{n} ({int(n)-int(o):+d})  mm={q['metamorpheus']} quant={q['quant_method']}")
    if t in ("metrics", "provenance_records", "findings"):
        deltas = collections.Counter(int(n) - int(o) for a, (o, n) in ch)
        print("   deltas:", dict(sorted(deltas.items())))
    print()

no_ions = [a for a in by if by[a].get("peptidoform_ions", ("", ""))[1] in ("", None) and any(d["accession"] == a and d["new_bundle"] for d in deps)]
print("== no peptidoform_ions table:", no_ions)
zero_ions = [a for a in by if by[a].get("peptidoform_ions", ("", ""))[1] == "0"]
print("== peptidoform_ions with 0 rows:", zero_ions)
print()

src = collections.Counter()
for d in done:
    for r in d["sources_changed"].split():
        src[r.split(":")[0]] += 1
print("== source roles changed (deposits):", dict(src.most_common()))
print()

gone, new = collections.Counter(), collections.Counter()
for d in done:
    gone.update(d["findings_gone"].split())
    new.update(d["findings_new"].split())
print("== finding codes that appear (deposits):", dict(new.most_common()))
print("== finding codes that go (deposits):", dict(gone.most_common()))
print()

ms = collections.Counter()
for d in done:
    ms[(d["metamorpheus"], d["quant_method"])] += 1
print("== re-ingested by MetaMorpheus/quant:", dict(sorted(ms.items())))

# deposits whose only differences are the expected ones (definitions + new ions table)
plain = [d["accession"] for d in done if set(x.split(" ")[0] for x in d["tables_that_differ"].split("; ")) <= {"definitions", "peptidoform_ions"}]
print("== deposits differing only in definitions + peptidoform_ions:", len(plain))
