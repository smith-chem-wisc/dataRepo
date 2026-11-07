"""Read-only: does any file under aging's store look written after its bundle? Stats files; opens only bundle.json."""
import collections
import datetime
import json
import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
STORE = pathlib.Path(r"F:\aging_data\repo\store")
CATALOGS = pathlib.Path(r"F:\aging_data\repo\catalogs")
MARGIN = 3600.0

late = []
stray = []
bundles = 0
newest = None
names = collections.Counter()
for deposit in sorted(STORE.iterdir()):
    if not deposit.is_dir():
        stray.append(("store root", deposit.name))
        continue
    for bundle in sorted(deposit.iterdir()):
        if not bundle.is_dir():
            stray.append((deposit.name, bundle.name))
            continue
        meta = bundle / "bundle.json"
        if not meta.exists():
            stray.append((deposit.name, bundle.name + " (no bundle.json)"))
            continue
        bundles += 1
        written = json.loads(meta.read_text(encoding="utf-8")).get("written_utc", "")
        when = datetime.datetime.fromisoformat(written.replace("Z", "+00:00")).timestamp()
        meta_mtime = meta.stat().st_mtime
        for root, _, files in os.walk(bundle):
            for name in files:
                path = pathlib.Path(root) / name
                names[name] += 1
                mtime = path.stat().st_mtime
                if mtime > when + MARGIN and mtime > meta_mtime + MARGIN:
                    late.append((str(path.relative_to(STORE)), datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc).isoformat(), written))
print("bundles read", bundles)
print("files written over an hour after their bundle:", len(late))
for row in late[:40]:
    print("  ", row)
print("stray entries at store or deposit level:", len(stray))
for row in stray[:40]:
    print("  ", row)
print("file names seen fewer than 3 times (a probe would be rare):")
for name, n in sorted(names.items(), key=lambda kv: kv[1]):
    if n < 3:
        print("  ", n, name)
print("catalogs folder:", sorted(p.name for p in CATALOGS.iterdir() if not p.name.endswith((".duckdb", ".owner")))[:20])
derived = CATALOGS / "derived"
if derived.exists():
    odd = [str(p.relative_to(derived)) for p in derived.rglob("*") if p.is_file() and not p.name.endswith(".parquet")]
    print("derived: non-parquet files", len(odd), odd[:10])
