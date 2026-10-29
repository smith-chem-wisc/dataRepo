"""Scratch: compare each deposit's newest stored bundle (cs-1.1.0, schema 0.0.15) with its scratch re-ingest
(cs-1.2.0, schema 0.0.16). Per deposit: both ids, rows per table, which sources changed (by role and sha256), and the
findings that appear or go. Writes compare_tables.tsv (long), compare_deposits.tsv, and prints a summary."""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:\aging_data\repo\store"
NEW = os.path.join(HERE, "store")


def load(folder):
    return json.load(open(os.path.join(folder, "bundle.json"), encoding="utf-8"))


def findings(folder):
    import duckdb
    path = os.path.join(folder, "findings.parquet")
    if not os.path.exists(path):
        return collections.Counter()
    return collections.Counter(r[0] for r in duckdb.sql(f"select code from '{path}' where severity in ('warning','error')").fetchall())


def sources(b):
    # Role -> sha256; the manifest entry's own sha is content too.
    out = {}
    for s in b["sources"]:
        out.setdefault(s["role"], set()).add(s.get("sha256"))
    return {k: tuple(sorted(x for x in v if x)) for k, v in out.items()}


base = [l.rstrip("\n").split("\t") for l in open(os.path.join(HERE, "baseline_latest.tsv"), encoding="utf-8")][1:]
long_rows, dep_rows = [], []
totals = collections.Counter()
for acc, old_id, _ing, _schema, served, _size in base:
    new_dir = os.path.join(NEW, acc)
    # A bundle still being written has no bundle.json yet.
    written = [d for d in os.listdir(new_dir) if os.path.isfile(os.path.join(new_dir, d, "bundle.json"))] if os.path.isdir(new_dir) else []
    if not written:
        dep_rows.append([acc, old_id, "", "not re-ingested", "", "", ""])
        continue
    # The newest scratch bundle: a deposit re-ingested after an input was restored has two.
    new_id = max(written, key=lambda d: load(os.path.join(new_dir, d))["written_utc"])
    o, n = load(os.path.join(OLD, acc, old_id)), load(os.path.join(new_dir, new_id))
    so, sn = sources(o), sources(n)
    changed = sorted(r for r in set(so) | set(sn) if so.get(r) != sn.get(r))
    fo, fn = findings(os.path.join(OLD, acc, old_id)), findings(os.path.join(new_dir, new_id))
    gone = sorted(set(fo) - set(fn)); new = sorted(set(fn) - set(fo))
    differing = []
    for t in sorted(set(o["tables"]) | set(n["tables"])):
        a, b = o["tables"].get(t), n["tables"].get(t)
        long_rows.append([acc, t, "" if a is None else a, "" if b is None else b])
        if a != b:
            differing.append(f"{t} {a}->{b}")
            totals[t] += 1
    dep_rows.append([acc, old_id, new_id, "; ".join(differing) or "same rows", " ".join(changed), " ".join(gone), " ".join(new)])

with open(os.path.join(HERE, "compare_tables.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\ttable\told_rows\tnew_rows\n")
    f.writelines("\t".join(map(str, r)) + "\n" for r in long_rows)
with open(os.path.join(HERE, "compare_deposits.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\told_bundle\tnew_bundle\ttables_that_differ\tsources_changed\tfindings_gone\tfindings_new\n")
    f.writelines("\t".join(r) + "\n" for r in dep_rows)
done = [r for r in dep_rows if r[2]]
print(f"{len(done)} of {len(dep_rows)} deposits compared")
print("deposits whose table differs:", dict(totals.most_common()))
for r in done:
    print(r[0], "|", r[3][:220], "| sources:", r[4] or "-", "| gone:", r[5] or "-", "| new:", r[6] or "-")
