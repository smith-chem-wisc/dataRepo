"""Scratch: before the ingests reach them, check each include entry's search folder and the database files its served
bundle read still exist (1.4.0 found 24 deposits reading deleted pin folders). Reads F:\\aging_data only."""
import json, os, sys
import yaml

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = r"F:\aging_data\repo\store"
m = yaml.safe_load(open(os.path.join(HERE, "manifest.snapshot.yaml"), encoding="utf-8"))
root = m["work_root"]
base = {l.split("\t")[0]: l.split("\t")[1] for l in open(os.path.join(HERE, "baseline.tsv"), encoding="utf-8").read().splitlines()[1:]}
bad = 0
for e in m["datasets"]:
    if e.get("status") != "include":
        continue
    acc = e["accession"]
    run = os.path.join(root, e["run"])
    probs = []
    search = os.path.join(run, (e.get("stages") or {}).get("search", "04_search"))
    if not os.path.isdir(search):
        probs.append("no search folder " + search)
    if e.get("search_results") and not os.path.isdir(os.path.join(run, e["search_results"])):
        probs.append("no search_results " + e["search_results"])
    bid = base.get(acc, "-")
    if bid != "-":
        b = json.load(open(os.path.join(STORE, acc, bid, "bundle.json"), encoding="utf-8"))
        for s in b["sources"]:
            if s.get("role", "").startswith("protein_database"):
                p = s.get("path") or ""
                if p and not os.path.isabs(p):
                    p = os.path.join(run, p)
                if p and not os.path.exists(p):
                    probs.append("database gone " + (s.get("path") or ""))
    if probs:
        bad += 1
        print(acc, e.get("metamorpheus"), e.get("quant_method"), "|", "; ".join(probs[:3]))
print(bad, "include entries with a missing input")
