"""Scratch, read-only: is there a per-search test that marks a PEP model that failed, and what do the flagged searches hold
under the notch fallback?"""
import csv
import os
import re
import sys

import duckdb

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = [r for r in csv.DictReader(handle, delimiter=chr(9)) if r["ratio"]]

data = []
for r in rows:
    folder = os.path.dirname(r["file"])
    results = os.path.join(folder, "results.txt")
    if not os.path.exists(results):
        results = os.path.join(os.path.dirname(folder), "results.txt")
    with open(results, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    at = text.find("Metrics for Determination of PEP")
    if at < 0:
        continue
    block = text[at: at + 1600]
    t = re.search(r"Targets Used for Training:\s*(\d+)", block)
    d = re.search(r"Decoys Used for Training:\s*(\d+)", block)
    accepted = [int(x) for x in re.findall(r"round \d+:\s+accepted (\d+)", block)]
    data.append(dict(
        dataset=r["dataset"], release=r["release"], ratio=float(r["ratio"]), n_q=int(r["n_q"]), n_new=int(r["n_new"]), file=r["file"],
        targets=int(t.group(1)) if t else None, decoys=int(d.group(1)) if d else None, accepted=accepted,
    ))

print("kept share = rows the PEP rule accepts / targets the model trained on (a trained model should keep its training targets)")
with_t = [x for x in data if x["targets"]]
for x in with_t:
    x["kept"] = x["n_new"] / x["targets"]
ordered = sorted(with_t, key=lambda x: x["kept"])
for x in ordered[:32]:
    print(f"  {x['kept']:.3f} {x['dataset']} {x['release']} ratio {x['ratio']} q {x['n_q']:,} new {x['n_new']:,} trained {x['targets']:,}/{x['decoys']:,} accepted {x['accepted']}")
print("deposits with no training counts:", [x["dataset"] for x in data if not x["targets"]])

for cut in (0.25, 0.35, 0.5, 0.6, 0.7):
    flagged = [x for x in with_t if x["kept"] < cut]
    print(f"kept below {cut}: {len(flagged)} flagged; ratio below 1 among them {sum(1 for x in flagged if x['ratio'] < 1)}; "
          f"ratio below 1 not flagged {sum(1 for x in with_t if x['ratio'] < 1 and x['kept'] >= cut)}")

con = duckdb.connect()
con.execute("SET threads=32")
print()
print("the deposits the PEP rule loses rows on, under each rule: q rule, PEP rule, notch only")
losers = sorted((x for x in data if x["ratio"] < 1), key=lambda x: x["ratio"])
total_q = total_pep = total_notch = 0
for x in losers:
    notch = con.execute(
        """SELECT count(*) FROM read_csv(?, delim='\t', header=true, quote='', escape='', all_varchar=true, null_padding=true,
              max_line_size=100000000, sample_size=2000)
           WHERE "Decoy/Contaminant/Target" IN ('T','ET') AND try_cast("QValue Notch" AS DOUBLE) <= 0.01""",
        [x["file"]],
    ).fetchone()[0]
    total_q += x["n_q"]
    total_pep += x["n_new"]
    total_notch += notch
    print(f"  {x['dataset']} {x['n_q']:,} {x['n_new']:,} {notch:,}")
print(f"  total {total_q:,} {total_pep:,} {total_notch:,}")

path = next(x["file"] for x in data if x["dataset"] == "PXD034590")
groups = os.path.join(os.path.dirname(path), "AllProteinGroups.tsv")
if os.path.exists(groups):
    with open(groups, encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split(chr(9))
    print()
    print("AllProteinGroups.tsv: PEP-named columns", [c for c in header if "pep" in c.lower() and "peptide" not in c.lower()], "of", len(header))
