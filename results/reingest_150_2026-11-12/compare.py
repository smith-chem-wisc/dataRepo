"""Scratch (1.5.0): compare each deposit's bundle in aging's serving catalog 75e1c0c82f8dc965 (cs-1.2.x, schema 0.0.16)
with its scratch re-ingest on feat/1.5.0 aa9ad4b (schema 0.0.17). Per deposit: both ids, rows per table, which sources
changed (by role and sha256), and the finding codes that appear or go (every severity). Writes compare_tables.tsv (long),
compare_deposits.tsv, timing.tsv, and prints a summary."""
import collections, json, os, re, sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = r"F:\aging_data\repo\store"
NEW = os.path.join(HERE, "store")


def load(folder):
    return json.load(open(os.path.join(folder, "bundle.json"), encoding="utf-8"))


def findings(folder):
    path = os.path.join(folder, "findings.parquet")
    if not os.path.exists(path):
        return collections.Counter()
    return collections.Counter(f"{r[0]}" for r in duckdb.sql(f"select code from '{path}'").fetchall())


def sources(b):
    out = {}
    for s in b["sources"]:
        out.setdefault(s["role"], set()).add(s.get("sha256"))
    return {k: tuple(sorted(x for x in v if x)) for k, v in out.items()}


secs = {}
for line in open(os.path.join(HERE, "progress.log"), encoding="utf-8"):
    m = re.match(r"(\S+) done\s+(\S+) rc=(\d+) secs=(\d+)", line)
    if m:
        secs[m.group(2)] = (int(m.group(3)), int(m.group(4)))

base = [l.rstrip("\n").split("\t") for l in open(os.path.join(HERE, "baseline.tsv"), encoding="utf-8")][1:]
long_rows, dep_rows = [], []
totals = collections.Counter()
for acc, old_id, _schema, mm, quant, _size in base:
    new_dir = os.path.join(NEW, acc)
    written = [d for d in os.listdir(new_dir) if os.path.isfile(os.path.join(new_dir, d, "bundle.json"))] if os.path.isdir(new_dir) else []
    rc, s = secs.get(acc, ("", ""))
    if not written:
        err = ""
        ep = os.path.join(HERE, "out", acc + ".err")
        if os.path.exists(ep):
            lines = [l.strip() for l in open(ep, encoding="utf-8", errors="replace") if l.strip()]
            err = lines[-1][:300] if lines else ""
        dep_rows.append([acc, old_id, "", f"not re-ingested (rc={rc}): {err}", "", "", "", mm, quant, str(s)])
        continue
    new_id = max(written, key=lambda d: load(os.path.join(new_dir, d))["written_utc"])
    n = load(os.path.join(new_dir, new_id))
    if old_id == "-":
        dep_rows.append([acc, "-", new_id, "not served before", "", "", "", mm, quant, str(s)])
        for t, v in n["tables"].items():
            long_rows.append([acc, t, "", v])
        continue
    o = load(os.path.join(OLD, acc, old_id))
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
    dep_rows.append([acc, old_id, new_id, "; ".join(differing) or "same rows", " ".join(changed), " ".join(gone), " ".join(new), mm, quant, str(s)])

with open(os.path.join(HERE, "compare_tables.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\ttable\told_rows\tnew_rows\n")
    f.writelines("\t".join(map(str, r)) + "\n" for r in long_rows)
with open(os.path.join(HERE, "compare_deposits.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\told_bundle\tnew_bundle\ttables_that_differ\tsources_changed\tfindings_gone\tfindings_new\tmetamorpheus\tquant_method\tsecs\n")
    f.writelines("\t".join(r) + "\n" for r in dep_rows)
done = [r for r in dep_rows if r[2]]
print(f"{len(done)} of {len(dep_rows)} deposits re-ingested")
print("deposits whose table differs:", dict(totals.most_common()))
for r in dep_rows:
    if not r[2]:
        print("NOT:", r[0], r[7], r[8], "|", r[3])
