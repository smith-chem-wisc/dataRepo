"""A manifest with the proposed non-content fields on the control entry, to show they move no bundle id."""
import sys

import yaml

S = sys.argv[1]
with open(S + "/after.yaml", encoding="utf-8") as handle:
    doc = yaml.safe_load(handle)
control = [e for e in doc["datasets"] if e["accession"] == "PXD017944"][0]
control["split_reason"] = "species"
control["superseded_by"] = ["PXD017944-a", "PXD017944-b"]
doc["datasets"] = [control]
doc["store"] = (S + "/store_fields").replace("\\", "/")
with open(S + "/fields.yaml", "w", encoding="utf-8", newline="\n") as handle:
    yaml.safe_dump(doc, handle, sort_keys=False, allow_unicode=True)
print("wrote fields.yaml")
