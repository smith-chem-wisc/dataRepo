"""Scratch: give every old-vs-new difference (compare_deposits.tsv) a cause among 1.4.0's items, or flag it.
Writes explained.tsv and prints the tally and anything unexplained."""
import csv, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "compare_deposits.tsv"), encoding="utf-8"), delimiter="\t"))
long = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(HERE, "compare_tables.tsv"), encoding="utf-8"), delimiter="\t"):
    long[r["accession"]][r["table"]] = (r["old_rows"], r["new_rows"])

tally = collections.Counter()
unexplained = []
out = []
for r in rows:
    acc = r["accession"]
    if not r["new_bundle"]:
        out.append([acc, "not re-ingested: search outputs gone (re-search)", ""])
        tally["not re-ingested"] += 1
        continue
    n = json.load(open(os.path.join(HERE, "store", acc, r["new_bundle"], "bundle.json"), encoding="utf-8"))
    keratins = bool(n["protein_databases"].get("searched_sequence", {}).get("resolved"))
    srcs = set(s.split(":")[0] for s in r["sources_changed"].split())
    gone, new = set(r["findings_gone"].split()), set(r["findings_new"].split())
    causes, left = set(), []
    for f in gone | new:
        if f == "unresolved_modifications" and f in gone: causes.add("G26")
        elif f == "contaminant_label_unresolved" and "protein_database" in srcs: causes.add("database restored")
        elif f == "sample_quant_not_stored" and f in gone: causes.add("PXR-R23")
        elif f == "sdrf_conflicting_rows" and f in new: causes.add("G106")
        elif f.startswith("sdrf") or f == "no_sdrf":
            causes.add("PXR-R22" if "sdrf" in srcs else "?sdrf finding without an SDRF change");
        elif f == "occupancy_not_stored" and f in gone: causes.add("PXR-R23")
        else: left.append(("finding", f, "gone" if f in gone else "new"))
    for t, (a, b) in long[acc].items():
        if a == b: continue
        a_, b_ = (int(a) if a else None), (int(b) if b else None)
        if t == "findings": continue  # explained through the codes above
        if t in ("assay_runs", "assays") and (long[acc].get("assay_runs", ("", ""))[1] or "0") != "0": causes.add("PXR-R23")
        elif t in ("quant_values", "ptm_stoichiometry", "definitions") and (long[acc].get("assay_runs", ("", ""))[1] or "0") != "0" and (a_ or 0) <= (b_ or 0):
            causes.add("PXR-R23")
        elif t in ("ptm_sites", "ptm_stoichiometry") and "protein_database" in srcs and (a_ or 0) < (b_ or 0): causes.add("database restored")
        elif t in ("ptm_sites", "ptm_stoichiometry") and keratins and (b_ or 0) < (a_ or 0): causes.add("G101")
        elif t in ("samples", "sample_characteristics") and "sdrf" in srcs: causes.add("PXR-R22")
        elif t == "sample_characteristics" and "sdrf_conflicting_rows" in new and (b_ or 0) < (a_ or 0): causes.add("G106")
        else: left.append(("table", t, f"{a}->{b}"))
    for s in srcs - {"sdrf", "protein_database"}:
        left.append(("source", s, "changed"))
    for c in causes: tally[c] += 1
    if not causes and not left: tally["identical rows"] += 1
    if left: unexplained.append((acc, left, sorted(causes)))
    out.append([acc, " ".join(sorted(causes)) or "identical rows", "; ".join(f"{k} {a} {b}" for k, a, b in left)])

with open(os.path.join(HERE, "explained.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("accession\tcauses\tunexplained\n")
    f.writelines("\t".join(x) + "\n" for x in out)
print("deposits per cause:", dict(tally.most_common()))
print(len(unexplained), "deposits with something unexplained")
for u in unexplained: print(" ", u)
