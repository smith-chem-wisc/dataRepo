"""`datarepo publish`: build then site, for an operator with no script of their own (PXR-D4).

The one behaviour it adds to `build` and `site` is the choice of datasets: every `include` entry
that has a bundle, with each one that has none NAMED rather than silently dropped or fatal.
"""

from __future__ import annotations

import json

from datarepo.cli import main
from test_catalog import write_bundle


def _manifest(tmp_path):
    path = tmp_path / "manifest.yaml"
    path.write_text(
        "manifest_version: 1\ninstance: stranger\nwork_root: work\nstore: store\n"
        "licence: CC-BY-4.0\ncredit: A second consumer\ndatasets:\n"
        "  - {accession: PXD000001, status: include, run: r/PXD000001}\n"
        "  - {accession: PXD000002, status: include, run: r/PXD000002}\n"
        "  - {accession: PXD000003, status: exclude, reason: unfit, run: r/PXD000003}\n",
        encoding="utf-8",
    )
    return path


def test_publish_builds_every_ingested_dataset_and_names_the_rest(tmp_path, capsys):
    manifest = _manifest(tmp_path)
    write_bundle(tmp_path / "store", "PXD000001")
    site = tmp_path / "site"
    assert main(["publish", str(manifest), "--site", str(site)]) == 0
    out = capsys.readouterr().out
    assert "skipped  PXD000002: 'include' in the manifest, but no bundle" in out
    assert "PXD000003" not in out  # excluded is not "missing"
    assert (tmp_path / "catalog.duckdb").exists()
    marker = json.loads((site / ".datarepo-site.json").read_text(encoding="utf-8"))
    assert marker["catalog_id"]
    assert (site / "index.html").exists()


def test_publish_with_nothing_ingested_refuses(tmp_path, capsys):
    assert main(["publish", str(_manifest(tmp_path)), "--site", str(tmp_path / "site")]) == 1
    assert "no 'include' dataset has a bundle" in capsys.readouterr().err
    assert not (tmp_path / "site").exists()


def test_publish_is_repeatable_over_its_own_site(tmp_path, capsys):
    manifest = _manifest(tmp_path)
    write_bundle(tmp_path / "store", "PXD000001")
    site = tmp_path / "site"
    assert main(["publish", str(manifest), "--site", str(site)]) == 0
    first = (site / "index.html").read_bytes()
    assert main(["publish", str(manifest), "--site", str(site)]) == 0
    assert (site / "index.html").read_bytes() == first
