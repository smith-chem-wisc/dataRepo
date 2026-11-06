"""Scratch manifests for a split-deposit trial. Reads aging's live manifest, writes nothing under F:."""
import copy
import os
import sys

import yaml

scratch = sys.argv[1]
os.makedirs(scratch, exist_ok=True)
live = "F:/aging_data/batch/manifest.yaml"
with open(live, encoding="utf-8") as handle:
    doc = yaml.safe_load(handle)
print("top-level keys:", [k for k in doc if k != "datasets"])
entries = {e["accession"]: e for e in doc["datasets"]}
bare = entries["PXD027754"]
control = entries["PXD017944"]
print("bare run:", bare["run"], "| status:", bare["status"], "| control run:", control["run"])


def write(name, datasets):
    out = {k: v for k, v in doc.items() if k != "datasets"}
    out["work_root"] = "F:/aging_data"
    out["store"] = os.path.join(scratch, "store").replace("\\", "/")
    if "candidates" in out and not os.path.isabs(str(out["candidates"])):
        out["candidates"] = os.path.normpath(os.path.join(os.path.dirname(live), out["candidates"])).replace("\\", "/")
    out["datasets"] = datasets
    path = os.path.join(scratch, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(out, handle, sort_keys=False, allow_unicode=True)
    print("wrote", path, "candidates:", out.get("candidates"))


def keyed(key):
    entry = copy.deepcopy(bare)
    entry["accession"] = key
    return entry


retired = copy.deepcopy(bare)
retired["status"] = "superseded"
retired["reason"] = "split into PXD027754-rat and PXD027754-mouse"

# before: the deposit as served today, plus a control whose id is known.
write("before.yaml", [copy.deepcopy(bare), copy.deepcopy(control)])
# after: the bare entry retired, two halves. There is no mouse search, so the second half is the same folder under
# another key: a stand-in that tests whether two keys of one accession collide, not what a real half would hold.
write("after.yaml", [retired, keyed("PXD027754-rat"), keyed("PXD027754-mouse"), copy.deepcopy(control)])
