"""Summarise measure_r81.py's TSV. Usage: python -I summarise_r81.py <r81_by_bundle.tsv>"""
import csv
import statistics
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8"), delimiter="\t"))
for r in rows:
    for k in ("target_psms", "psms_tier", "psms_r81", "psms_both", "psms_r81_resolved"):
        r[k] = int(r[k])
print(f"bundles {len(rows)}")
print("tier:", dict(Counter(r["tier"] for r in rows)))
print("by release and tier:", sorted(Counter((r["metamorpheus"], r["tier"]) for r in rows).items()))
t = sum(r["psms_tier"] for r in rows); f = sum(r["psms_r81"] for r in rows); b = sum(r["psms_both"] for r in rows)
res = sum(r["psms_r81_resolved"] for r in rows)
print(f"target PSMs passing: today's tier (<) {t:,}; the search's filter (<=) {f:,} ({f / t:.3f} of today's); both {b:,}")
print(f"  only today's tier {t - b:,}; only the filter {f - b:,}; filter with the notch-ambiguity clause {res:,}")
ratios = [(r["psms_r81"] / r["psms_tier"] if r["psms_tier"] else float("inf"), r) for r in rows]
fin = sorted(x for x, _ in ratios if x != float("inf"))
print(f"per bundle, filter / tier: median {statistics.median(fin):.3f}, min {fin[0]:.3f}, max {fin[-1]:.3f}")
print(f"  bundles where the filter passes fewer: {sum(1 for x, _ in ratios if x < 1)}, more: {sum(1 for x, _ in ratios if x > 1)}, equal: {sum(1 for x, _ in ratios if x == 1)}")
for tier in sorted({r["tier"] for r in rows}):
    sub = [x for x, r in ratios if r["tier"] == tier and x != float("inf")]
    if sub:
        print(f"  {tier}: {len(sub)} bundles, median {statistics.median(sub):.3f}, range {min(sub):.3f} to {max(sub):.3f}")
print("largest gains under the filter (today's tier passes fewest relative to it):")
for x, r in sorted(ratios, key=lambda p: -p[0])[:6]:
    print(f"  {r['dataset_id']} {r['metamorpheus']} {r['tier']}: tier {r['psms_tier']:,} -> filter {r['psms_r81']:,}")
print("largest losses:")
for x, r in sorted(ratios, key=lambda p: p[0])[:6]:
    print(f"  {r['dataset_id']} {r['metamorpheus']} {r['tier']}: tier {r['psms_tier']:,} -> filter {r['psms_r81']:,}")
