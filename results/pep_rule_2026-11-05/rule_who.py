"""Scratch, read-only: what the deposits the 1% PEP q-value rule hollows out have in common."""
import csv
import os
import re
import statistics
import sys
from collections import defaultdict

import duckdb
import yaml

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = [r for r in csv.DictReader(handle, delimiter=chr(9)) if r["ratio"]]
for r in rows:
    r["ratio"] = float(r["ratio"])
    r["n_q"] = int(r["n_q"])
    r["n_rows"] = int(r["n_rows"])
with open("F:/aging_data/batch/manifest.yaml", encoding="utf-8") as handle:
    entries = {e["accession"]: e for e in yaml.safe_load(handle)["datasets"]}

cat = duckdb.connect("F:/aging_data/repo/catalogs/catalog-d621ea41cd649681.duckdb", read_only=True)
over = {x[0]: x[1:] for x in cat.execute(
    "SELECT dataset_id, enrichment, instrument_vendor, n_runs, n_protein_groups_1pct FROM dataset_overview").fetchall()}
cat.close()


def table(label, key):
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r["ratio"])
    print(f"--- by {label}: value, deposits, below 0.5, median ratio")
    for value, ratios in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {value}: {len(ratios)}, {sum(1 for x in ratios if x < 0.5)}, {statistics.median(ratios):.2f}")


def profile(r):
    entry = entries.get(r["dataset"], {})
    found = re.findall(r"under profile ([\w.@-]+)", str(entry))
    return found[-1] if found else "none named"


def analyzer(r):
    text = str(entries.get(r["dataset"], {}))
    if re.search(r"low-?res|ion trap|ITMS|LTQ", text, re.I):
        return "low-res words in entry"
    return "no low-res words"


table("search profile", profile)
table("entry text", analyzer)
table("enrichment", lambda r: str(over[r["dataset"]][0]))
table("vendor", lambda r: str(over[r["dataset"]][1]))
print("--- below 0.5, not a low-res profile:")
for r in rows:
    if r["ratio"] < 0.5 and "lowres" not in profile(r):
        print(" ", r["dataset"], r["ratio"], profile(r), analyzer(r), over[r["dataset"]][:2], "q rows", r["n_q"])
print("--- low-res profile, ratio at or above 1:")
print(" ", sorted((r["ratio"], r["dataset"], r["n_q"]) for r in rows if "lowres" in profile(r) and r["ratio"] >= 1)[:20])
low = [r for r in rows if "lowres" in profile(r)]
high = [r for r in rows if "lowres" not in profile(r)]
print("--- low-res profile deposits", len(low), "below 1:", sum(1 for r in low if r["ratio"] < 1), "q rows", sum(r["n_q"] for r in low))
print("--- other deposits", len(high), "below 1:", sum(1 for r in high if r["ratio"] < 1), "q rows", sum(r["n_q"] for r in high))
table("peptide acceptance rate (q-rule rows / target-and-decoy rows)", lambda r: (
    "under 2%" if r["n_q"] / r["n_rows"] < 0.02 else "2-5%" if r["n_q"] / r["n_rows"] < 0.05
    else "5-15%" if r["n_q"] / r["n_rows"] < 0.15 else "over 15%"))

print()
print("--- the PEP block, three deposits")
names = {r["dataset"]: r for r in rows}
for name in ("PXD057502", "PXD022227", "PXD027971"):
    path = names[name]["file"]
    results = os.path.join(os.path.dirname(path), "results.txt")
    if not os.path.exists(results):
        results = os.path.join(os.path.dirname(os.path.dirname(path)), "results.txt")
    with open(results, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    at = text.find("Metrics for Determination of PEP")
    print(name, os.path.getsize(path) // 1000000, "MB peptide table")
    print(text[max(0, at - 200):at + 1200])
    print("=====")
    for line in text.splitlines():
        if re.search(r"target (PSMs|peptides).*q-value|Identification filter|within 1% FDR", line):
            print("   ", line[:150])
    print("=====")
