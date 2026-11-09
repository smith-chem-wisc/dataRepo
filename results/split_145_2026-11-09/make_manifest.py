"""Scratch manifest for the 1.4.5 split trial. Reads aging's live manifest, writes nothing under F:."""
import copy
import os
import sys
import time

import yaml

sys.stdout.reconfigure(encoding="utf-8")
scratch = sys.argv[1]
os.makedirs(scratch, exist_ok=True)
live = "F:/aging_data/batch/manifest.yaml"
for attempt in range(5):  # PXReprise rewrites it non-atomically
    try:
        with open(live, encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        break
    except yaml.YAMLError:
        time.sleep(5)
entries = {e["accession"]: e for e in doc["datasets"]}
bare = entries["PXD027754"]
control = entries["PXD017944"]
print("bare run:", bare["run"], "| status:", bare["status"], "| control run:", control["run"])


def keyed(key):
    entry = copy.deepcopy(bare)
    entry["accession"] = key
    entry["split_reason"] = "species"
    return entry


out = {k: v for k, v in doc.items() if k not in ("datasets", "candidates")}
out["work_root"] = "F:/aging_data"
out["store"] = os.path.join(scratch, "store").replace("\\", "/")
# The whole entry stays include, so a build naming it beside its parts tests the refusal; a build naming the parts
# alone is what PXReprise will serve (with the whole entry superseded).
out["datasets"] = [copy.deepcopy(bare), keyed("PXD027754-rat"), keyed("PXD027754-mouse"), copy.deepcopy(control)]
path = os.path.join(scratch, "manifest.yaml")
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    yaml.safe_dump(out, handle, sort_keys=False, allow_unicode=True)
print("wrote", path)
