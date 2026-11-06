"""Scratch, read-only: does results.txt's PEP block say which searches the 1% PEP q-value rule hollows out?"""
import csv
import math
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
here = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
with open(os.path.join(here, "rule_compare.tsv"), encoding="utf-8", newline="") as handle:
    rows = [r for r in csv.DictReader(handle, delimiter=chr(9))]


def block_metrics(path):
    results = os.path.join(os.path.dirname(path), "results.txt")
    if not os.path.exists(results):
        results = os.path.join(os.path.dirname(os.path.dirname(path)), "results.txt")
    with open(results, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    starts = [m.start() for m in re.finditer("Metrics for Determination of PEP", text)]
    if not starts:
        return None
    block = text[starts[-1]: starts[-1] + 1600]

    def value(label):
        m = re.search(re.escape(label) + r":\s*(\S+)", block)
        return m.group(1) if m else None

    accepted = [int(x) for x in re.findall(r"round \d+:\s+accepted (\d+)", block)]
    return {
        "blocks": len(starts),
        "logloss": value("LogLoss"),
        "auc": value("Area Under Curve"),
        "auprc": value("Area under Precision recall Curve"),
        "t": value("Targets Used for Training"),
        "d": value("Decoys Used for Training"),
        "rounds": value("Training Rounds Run"),
        "accepted": accepted,
    }


data = []
for r in rows:
    if not r["ratio"]:
        continue
    m = block_metrics(r["file"])
    if m is None:
        print("no block:", r["dataset"])
        continue
    d = dict(dataset=r["dataset"], release=r["release"], ratio=float(r["ratio"]), n_q=int(r["n_q"]), n_new=int(r["n_new"]), **m)
    d["infinite"] = d["logloss"] is not None and not math.isfinite(float(d["logloss"]))
    d["logloss_missing"] = d["logloss"] is None
    d["trained_on"] = int(d["t"]) / max(int(d["d"]), 1) if d["t"] and d["d"] else None
    data.append(d)


def show(label, group):
    if not group:
        print(f"{label}: none")
        return
    ratios = sorted(g["ratio"] for g in group)
    print(
        f"{label}: {len(group)} deposits, below 0.5: {sum(1 for x in ratios if x < 0.5)}, below 1: {sum(1 for x in ratios if x < 1)}, "
        f"ratio min {ratios[0]} median {statistics.median(ratios):.2f} max {ratios[-1]}, "
        f"q rows {sum(g['n_q'] for g in group):,} -> {sum(g['n_new'] for g in group):,}"
    )


print("blocks per results.txt:", sorted({d["blocks"] for d in data}))
show("LogLoss Infinity", [d for d in data if d["infinite"]])
show("LogLoss finite", [d for d in data if not d["infinite"] and not d["logloss_missing"]])
show("LogLoss missing", [d for d in data if d["logloss_missing"]])
print()
print("by release, LogLoss Infinity:")
for release in sorted({d["release"] for d in data}):
    group = [d for d in data if d["release"] == release]
    print(f"  {release}: {sum(1 for d in group if d['infinite'])} of {len(group)}")
print()
print("Below 1 with a finite LogLoss:")
for d in sorted((d for d in data if d["ratio"] < 1 and not d["infinite"]), key=lambda d: d["ratio"]):
    print(f"  {d['dataset']} {d['release']} ratio {d['ratio']} q {d['n_q']:,} logloss {d['logloss']} rounds {d['rounds']} accepted {d['accepted']} t/d {d['t']}/{d['d']}")
print("Infinity, ratio at or above 1:")
for d in sorted((d for d in data if d["ratio"] >= 1 and d["infinite"]), key=lambda d: d["ratio"]):
    print(f"  {d['dataset']} {d['release']} ratio {d['ratio']} q {d['n_q']:,} rounds {d['rounds']} accepted {d['accepted']} t/d {d['t']}/{d['d']}")
print()
print("targets/decoys in training, against ratio:")
for low, high in [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1), (1, 99)]:
    show(f"  {low}-{high}", [d for d in data if d["trained_on"] is not None and low <= d["trained_on"] < high])
print()
print("Rounds run:")
for rounds in sorted({d["rounds"] for d in data if d["rounds"]}, key=int):
    show(f"  {rounds}", [d for d in data if d["rounds"] == rounds])
show("  not recorded (1.1.11)", [d for d in data if not d["rounds"]])
