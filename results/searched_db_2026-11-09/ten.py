"""The ten searches whose proteome GPTMD database has no recorded sha256: find both GPTMD files in the search folder the served
bundle names, check the recorded contaminant file still hashes to its recorded value, and hash the proteome file now. Read only."""
import glob
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
served = {"PXD007999": "094005f4ee4da7e0", "PXD018969": "fed05ac2602e3da1", "PXD027318": "4b75374ba407531d",
          "PXD032040": "b375d5ee00869b7f", "PXD032202": "2c73cb35813984d0", "PXD036557": "0955c951b61e80ba",
          "PXD042301": "f5c6cb1d792766da", "PXD044773": "8fe12f4432968b70", "PXD052189": "aac992ee3b6a6560",
          "PXD058775": "f973337f70227e3d"}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


for dataset, bundle in sorted(served.items()):
    root = f"F:/aging_data/repo/store/{dataset}/{bundle}"
    with open(f"{root}/bundle.json", encoding="utf-8") as handle:
        manifest = json.load(handle)
    results = next(s for s in manifest["sources"] if s["role"] == "results_txt")["path"]
    search = os.path.dirname(os.path.dirname(results))
    recorded = {}
    prov = next((s for s in manifest["sources"] if s["role"] == "provenance:04_search"), None)
    if prov:
        with open(os.path.join(root, prov["bundle_path"]), encoding="utf-8") as handle:
            for o in json.load(handle).get("outputs", []):
                if o.get("path", "").endswith("GPTMD.xml"):
                    recorded[os.path.basename(o["path"])] = o.get("sha256")
    for path in sorted(glob.glob(os.path.join(search, "**", "*GPTMD.xml"), recursive=True)):
        name = os.path.basename(path)
        now = sha(path)
        was = recorded.get(name)
        verdict = "no recorded sha256" if was is None else ("matches the record" if was == now else "DIFFERS from the record")
        print(f"{dataset} {name[:40]:40s} {os.path.getsize(path)/1e6:7.1f} MB  sha256 {now}  {verdict}")
