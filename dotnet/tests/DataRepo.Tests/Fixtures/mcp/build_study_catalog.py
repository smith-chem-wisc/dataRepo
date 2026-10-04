"""Build the MCP parity's second fixture catalog with the Python 0.32.0 builder.

The site fixture's bundle (python-0.32.0/PXD999999) plus the catalog fixture's study delivery (aging,
sample_ages for both samples + one age_effects row) and its logs.resolve_genes artefact, built as
`datarepo build --study-latest aging` does. Run from dotnet/tests/DataRepo.Tests/Fixtures so the
catalog records the store relative to it.

usage: python build_study_catalog.py <out.duckdb>
"""
import shutil
import sys
import tempfile
from pathlib import Path

from datarepo.catalog import build_catalog, select_artefacts, select_bundles, select_study_bundles
from datarepo.manifest import load_manifest

out = Path(sys.argv[1]).resolve()
fixtures = Path.cwd()
repo = fixtures.parents[3]
with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp) / "store"
    shutil.copytree(fixtures / "python-0.32.0" / "PXD999999", store / "PXD999999")
    shutil.copytree(fixtures / "catalog" / "store" / "_study", store / "_study")
    shutil.copytree(fixtures / "catalog" / "store" / "_engine", store / "_engine")
    manifest = load_manifest(repo / "tests" / "data" / "manifest.yaml")
    bundles = select_bundles(manifest, ["PXD999999"], store=store)
    study = select_study_bundles(store, latest=["aging"])
    artefacts, checks = select_artefacts(store, bundles)
    notes = {"manifest": "tests/data/manifest.yaml", "study": {r.layer: r.bundle_id for r in study}}
    if out.exists():
        out.unlink()
    result = build_catalog(bundles, out, instance=manifest.instance, notes=notes, study_bundles=study,
                           artefacts=artefacts, engine_checks=checks)
    print(result.catalog_id, out)
