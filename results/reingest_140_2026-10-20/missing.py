"""Scratch: which stored bundles (the newest per deposit) name a source file that is no longer on disk, and which of
those files survive elsewhere with the same sha256 (a re-ingest could read the copy, if the ingest looked by sha)."""
import json, os, collections, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
base = [l.rstrip("\n").split("\t") for l in open(os.path.join(HERE, "baseline_latest.tsv"), encoding="utf-8")][1:]
missing = collections.defaultdict(list)
by_role = collections.Counter()
by_folder = collections.Counter()
for acc, bid, *_ in base:
    b = json.load(open(os.path.join(r"F:\aging_data\repo\store", acc, bid, "bundle.json"), encoding="utf-8"))
    for s in b["sources"]:
        p = s.get("path", "")
        if not p or p.startswith("<"):
            continue
        if not os.path.exists(p):
            missing[acc].append((s["role"], p, s.get("sha256")))
            by_role[s["role"].split(":")[0]] += 1
            by_folder[os.path.dirname(os.path.dirname(os.path.dirname(p)))] += 1

print(len(missing), "of", len(base), "deposits name a source no longer on disk")
print("by role:", dict(by_role.most_common()))
print("by folder:", by_folder.most_common(10))
only_db = sorted(a for a, v in missing.items() if all(r.startswith("protein_database") for r, _, _ in v))
print("only a database file missing:", len(only_db))
other = sorted(set(missing) - set(only_db))
print("other sources missing:", len(other), other[:20])
for a in other[:8]:
    print("  ", a, [(r, p[-60:]) for r, p, _ in missing[a] if not r.startswith("protein_database")][:3])

# Do the missing database files survive elsewhere under F:\aging_batch with the same sha256?
names = {os.path.basename(p) for v in missing.values() for r, p, _ in v if r.startswith("protein_database")}
copies = collections.defaultdict(set)
for name in names:
    for path in glob.glob(os.path.join(r"F:\aging_batch", "*", "profiles", "lists", name)):
        copies[name].add(hashlib.sha256(open(path, "rb").read()).hexdigest())
unrecoverable = sorted({(os.path.basename(p), sha[:12]) for v in missing.values() for r, p, sha in v
                        if r.startswith("protein_database") and sha not in copies.get(os.path.basename(p), set())})
print("missing database files with no same-sha copy under F:/aging_batch:", unrecoverable)
with open(os.path.join(HERE, "missing_sources.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\trole\tpath\tsha256\n")
    f.writelines(f"{a}\t{r}\t{p}\t{s}\n" for a, v in sorted(missing.items()) for r, p, s in v)
