"""PXR-R34: is a bundle written to a second store byte-identical to the served one? Compare file by file. Read-only."""
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
scratch = sys.argv[1]


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree(root):
    found = {}
    for folder, _, names in os.walk(root):
        for name in names:
            full = os.path.join(folder, name)
            found[os.path.relpath(full, root).replace("\\", "/")] = full
    return found


def walk_diff(a, b, prefix=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                yield f"{prefix}{key} only on one side"
            else:
                yield from walk_diff(a[key], b[key], f"{prefix}{key}.")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{prefix[:-1]} length {len(a)} vs {len(b)}"
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                yield from walk_diff(x, y, f"{prefix}{i}.")
    elif a != b:
        yield f"{prefix[:-1]}: {str(a)[:70]!r} vs {str(b)[:70]!r}"


for dataset, bundle in (("PXD017944", "3cd52dd1b39472d8"), ("PXD027754", "2799534125b81db3")):
    served = f"F:/aging_data/repo/store/{dataset}/{bundle}"
    ours = f"{scratch}/store/{dataset}/{bundle}"
    a, b = tree(served), tree(ours)
    print("==", dataset, bundle, "files served", len(a), "scratch", len(b))
    print("  only served:", sorted(set(a) - set(b))[:10])
    print("  only scratch:", sorted(set(b) - set(a))[:10])
    same, differ = [], []
    for name in sorted(set(a) & set(b)):
        (same if sha(a[name]) == sha(b[name]) else differ).append(name)
    print("  byte-identical:", len(same), "differ:", differ)
    if "bundle.json" in differ:
        left = json.load(open(a["bundle.json"], encoding="utf-8"))
        right = json.load(open(b["bundle.json"], encoding="utf-8"))
        lines = list(walk_diff(left, right))
        print("  bundle.json differences:", len(lines))
        for line in lines[:25]:
            print("   ", line[:190])
